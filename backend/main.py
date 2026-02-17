from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, AsyncGenerator
from openai import OpenAI
import os
import json
import asyncio
import traceback
from datetime import datetime

# Import tools and prompts
from prompts import ASSISTANT_INSTRUCTIONS, ASSISTANT_NAME, ASSISTANT_MODEL, PROMPT_VERSION
from tools import TOOLS, search_web_restricted, classify_risk

app = FastAPI()

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
cors_origins = [origin.strip() for origin in cors_origins]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=OPENAI_API_KEY)

# Vector Store ID
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID", "vs_692180726b908191af2f182b14342882")

# Singleton Assistant Storage
# We will store the Assistant ID in memory or env if possible, 
# but for a simple restartable service, we can check OpenAI on startup.
GLOBAL_ASSISTANT_ID = None

def get_singleton_assistant() -> str:
    """
    Get or create the singleton assistant.
    Returns the Assistant ID.
    """
    global GLOBAL_ASSISTANT_ID
    
    if GLOBAL_ASSISTANT_ID:
        return GLOBAL_ASSISTANT_ID

    print("🔎 Checking for existing assistant...")
    
    # List assistants to find if one exists with the correct name
    # Note: Pagination might be needed if you have many assistants, 
    # but usually `limit=20` is enough to find the recent one.
    my_assistants = client.beta.assistants.list(order="desc", limit=20)
    
    existing_assistant = None
    for assistant in my_assistants.data:
        if assistant.name == ASSISTANT_NAME:
            existing_assistant = assistant
            break
    
    if existing_assistant:
        print(f"✅ Found existing assistant: {existing_assistant.id}")
        
        # We should update it to ensure it has the latest instructions and tools
        print("🔄 Updating assistant instructions and tools...")
        updated_assistant = client.beta.assistants.update(
            assistant_id=existing_assistant.id,
            instructions=ASSISTANT_INSTRUCTIONS,
            model=ASSISTANT_MODEL,
            tools=TOOLS,
            tool_resources={
                "file_search": {
                    "vector_store_ids": [VECTOR_STORE_ID]
                }
            }
        )
        GLOBAL_ASSISTANT_ID = updated_assistant.id
        return GLOBAL_ASSISTANT_ID
    else:
        print("🆕 Creating NEW assistant...")
        new_assistant = client.beta.assistants.create(
            name=ASSISTANT_NAME,
            instructions=ASSISTANT_INSTRUCTIONS,
            model=ASSISTANT_MODEL,
            tools=TOOLS,
            tool_resources={
                "file_search": {
                    "vector_store_ids": [VECTOR_STORE_ID]
                }
            }
        )
        print(f"✅ Created assistant: {new_assistant.id}")
        GLOBAL_ASSISTANT_ID = new_assistant.id
        return GLOBAL_ASSISTANT_ID

class ChatRequest(BaseModel):
    conversation_id: str = None  # Optional, if None, one will be created/returned? Actually usually we want a thread_id
    # To keep compatibility with frontend, we accept conversation_id and map it to thread_id
    # But ideally, conversation_id SHOULD be the thread_id.
    
    thread_id: Optional[str] = None # Prefer thread_id over conversation_id
    message: str
    uploaded_file_ids: Optional[List[str]] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the singleton assistant on startup"""
    try:
        get_singleton_assistant()
    except Exception as e:
        print(f"❌ Failed to initialize assistant: {e}")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload file to OpenAI and return file ID"""
    try:
        print(f"Uploading file: {file.filename}")
        content = await file.read()
        openai_file = client.files.create(
            file=(file.filename, content),
            purpose='assistants'
        )
        return {
            "file_id": openai_file.id,
            "filename": file.filename,
            "status": "uploaded"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def stream_generator(thread_id: str, assistant_id: str, message_content: str, file_ids: List[str] = None):
    """
    Generator that creates a run and streams events.
    """
    try:
        # Create user message
        msg_params = {
            "thread_id": thread_id,
            "role": "user",
            "content": message_content
        }
        if file_ids:
            msg_params["attachments"] = [
                {"file_id": fid, "tools": [{"type": "file_search"}]} for fid in file_ids
            ]
        
        client.beta.threads.messages.create(**msg_params)

        # Start streaming run
        stream = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            stream=True
        )
        
        for event in stream:
            # handle tool calls and text deltas
            if event.event == 'thread.message.delta':
                # This is a text delta
                data = event.data
                if data.delta.content:
                    for content_part in data.delta.content:
                        if content_part.type == 'text' and content_part.text.value:
                            # Yield text chunk
                            yield f"data: {json.dumps({'type': 'text', 'content': content_part.text.value})}\n\n"
            
            elif event.event == 'thread.run.requires_action':
                run_obj = event.data
                tool_outputs = []
                
                print("⚡ Processing Tool Calls...")
                yield f"data: {json.dumps({'type': 'status', 'content': 'Processing tool calls...'})}\n\n"

                for tool_call in run_obj.required_action.submit_tool_outputs.tool_calls:
                    function_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    
                    print(f"   Calling: {function_name} with {args}")
                    
                    output = None
                    if function_name == "search_web":
                        output = str(search_web_restricted(args.get("query")))
                    elif function_name == "classify_risk":
                        output = json.dumps(classify_risk(args.get("system_description"), args.get("features")))
                    else:
                        output = "Unknown tool"
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": output
                    })
                
                # Submit outputs and continue streaming
                if tool_outputs:
                    # We need to submit and get a NEW stream
                    with client.beta.threads.runs.submit_tool_outputs_stream(
                        thread_id=thread_id,
                        run_id=run_obj.id,
                        tool_outputs=tool_outputs
                    ) as tool_stream:
                        for tool_event in tool_stream:
                            if tool_event.event == 'thread.message.delta':
                                data = tool_event.data
                                if data.delta.content:
                                    for content_part in data.delta.content:
                                        if content_part.type == 'text' and content_part.text.value:
                                            yield f"data: {json.dumps({'type': 'text', 'content': content_part.text.value})}\n\n"
                            elif tool_event.event == 'thread.run.completed':
                                # Done
                                pass

            elif event.event == 'thread.run.completed':
                # Run finished
                pass
            
            elif event.event == 'thread.run.failed':
                print(f"Run failed: {event.data}")
                yield f"data: {json.dumps({'type': 'error', 'content': 'Run failed'})}\n\n"

        yield "data: [DONE]\n\n"

    except Exception as e:
        print(f"Stream error: {e}")
        traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response.
    """
    # Use thread_id if provided, else strictly require conversation_id to reuse as thread logic?
    # Ideally, we should receive a thread_id.
    # If the frontend sends 'conversation_id', we'll assume it MIGHT be a thread_id 
    # OR we create a new thread and map it. 
    # For simplicity, let's treat conversation_id as a potential thread_id.
    
    # However, 'conversation_id' in the old code was just a client-side UUID.
    # We need to map client-UUID to OpenAI Thread ID.
    # But since we are moving to stateless/singleton, we can just say:
    # "Client, please hold onto the thread_id I give you".
    
    # Strategy:
    # If request.thread_id is present, use it.
    # If not, create a new thread.
    
    # We will use 'conversation_id' from the request as the CLIENT's session ID.
    # If we don't have a mapping for it, create a new thread.
    
    # NOTE: Since we restarted the server, in-memory mappings are lost.
    # Best practice: The CLIENT should store the `thread_id` returned by us.
    # But existing client sends `conversation_id`.
    
    # Temporary Hybrid:
    # 1. If we receive a `thread_id` in request, use it.
    # 2. If we receive `conversation_id`, we try to find it in our (now empty) memory?
    #    Realistically, let's just create a NEW thread if we don't have one 
    #    and return it to the client.
    
    target_thread_id = request.thread_id
    if not target_thread_id:
        # Create new thread
        t = client.beta.threads.create()
        target_thread_id = t.id
        print(f"🆕 Created new thread: {target_thread_id}")

    assistant_id = get_singleton_assistant()
    
    return StreamingResponse(
        stream_generator(
            thread_id=target_thread_id,
            assistant_id=assistant_id,
            message_content=request.message,
            file_ids=request.uploaded_file_ids
        ),
        media_type="text/event-stream"
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "assistant_id": GLOBAL_ASSISTANT_ID}

@app.get("/")
def root():
    return {"message": "LawMinded Bot Backend v2 (Streaming)"}

