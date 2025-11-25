from fastapi import FastAPI, UploadFile, File, HTTPException

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from openai import OpenAI
import os
from datetime import datetime
import traceback
import time
import json
from tavily import TavilyClient
from prompts import ASSISTANT_INSTRUCTIONS, ASSISTANT_NAME, ASSISTANT_MODEL, PROMPT_VERSION

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

# Initialize Tavily client
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable is required")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Your Vector Store ID
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID", "vs_692180726b908191af2f182b14342882")

# Allowed web search domains (ONLY these 3 official EU URLs)
ALLOWED_SEARCH_DOMAINS = [
    "eur-lex.europa.eu",
    "ai-act-service-desk.ec.europa.eu",
    "digital-strategy.ec.europa.eu"
]

# In-memory storage for conversations and assistants
conversations = {}
user_assistants = {}

class ChatRequest(BaseModel):
    conversation_id: str
    message: str
    uploaded_file_ids: Optional[List[str]] = None  # OpenAI file IDs from upload

class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    timestamp: str
    sources: Optional[List[str]] = None  # File IDs or vector store references
    used_vector_store: bool = False
    used_uploaded_files: bool = False
    used_web_search: bool = False
    web_search_results: Optional[List[Dict[str, Any]]] = None

def search_web_restricted(query: str) -> Dict[str, Any]:
    """Search web using Tavily, restricted to allowed domains only"""
    try:
        print(f"🌐 Web search query: {query}")
        print(f"   Restricted to domains: {ALLOWED_SEARCH_DOMAINS}")
        
        # Search with domain restriction
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            include_domains=ALLOWED_SEARCH_DOMAINS,
            max_results=5
        )
        
        results = []
        for result in response.get('results', []):
            results.append({
                "title": result.get('title', ''),
                "url": result.get('url', ''),
                "content": result.get('content', ''),
                "score": result.get('score', 0)
            })
        
        print(f"   Found {len(results)} results from allowed domains")
        return {
            "results": results,
            "query": query
        }
    except Exception as e:
        print(f"Web search error: {str(e)}")
        return {"results": [], "query": query, "error": str(e)}

def get_or_create_assistant(conversation_id: str, additional_file_ids: List[str] = None):
    """Get existing assistant or create new one with vector store and web search"""
    try:
        # Check if assistant exists and has current prompt version
        if conversation_id not in user_assistants or \
           user_assistants[conversation_id].get("prompt_version") != PROMPT_VERSION:
            # Create assistant with vector store and web search tool
            assistant = client.beta.assistants.create(
                name=ASSISTANT_NAME,
                instructions=ASSISTANT_INSTRUCTIONS,
                model=ASSISTANT_MODEL,
                tools=[
                    {
                        "type": "file_search",
                        "file_search": {
                            "max_num_results": 5
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "search_web",
                            "description": "MANDATORY TOOL: You MUST use this for ALL compliance questions. Search official EU AI Act sources (eur-lex.europa.eu, ai-act-service-desk.ec.europa.eu, digital-strategy.ec.europa.eu) for up-to-date information. Use this AFTER file_search for EVERY compliance question - NO EXCEPTIONS. Provides latest updates, recent changes, current dates, official announcements. Examples: 'what is article 11' → call with 'article 11 EU AI Act latest updates'; 'best practices risk management' → call with 'AI risk management best practices EU AI Act'; 'oversight educational tools' → call with 'AI oversight educational tools EU compliance'. You MUST call this tool even if file_search returned good results.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The search query to find relevant information"
                                    }
                                },
                                "required": ["query"]
                            }
                        }
                    }
                ],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [VECTOR_STORE_ID]
                    }
                }
            )
            
            # Create thread
            thread = client.beta.threads.create()
            
            # If old assistant exists, delete it first
            if conversation_id in user_assistants:
                old_assistant_id = user_assistants[conversation_id].get("assistant_id")
                old_thread_id = user_assistants[conversation_id].get("thread_id")
                try:
                    if old_assistant_id:
                        client.beta.assistants.delete(old_assistant_id)
                    if old_thread_id:
                        client.beta.threads.delete(old_thread_id)
                    print(f"Deleted old assistant/thread for conversation: {conversation_id}")
                except Exception as e:
                    print(f"Error deleting old assistant/thread: {str(e)}")
            
            user_assistants[conversation_id] = {
                "assistant_id": assistant.id,
                "thread_id": thread.id,
                "prompt_version": PROMPT_VERSION
            }
            print(f"Created assistant: {assistant.id}, thread: {thread.id}, prompt_version: {PROMPT_VERSION}")
        
        assistant_data = user_assistants[conversation_id]
        
        # If there are additional files, attach them to the thread
        if additional_file_ids:
            # Update assistant to include new files in vector store
            # Note: For dynamically uploaded files, we attach them to messages
            pass
        
        return assistant_data
    except Exception as e:
        print(f"Error creating assistant: {str(e)}")
        raise

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload file to OpenAI and return file ID"""
    try:
        print(f"Uploading file to OpenAI: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Upload to OpenAI
        openai_file = client.files.create(
            file=(file.filename, content),
            purpose='assistants'
        )
        
        print(f"File uploaded to OpenAI with ID: {openai_file.id}")
        
        return {
            "file_id": openai_file.id,
            "filename": file.filename,
            "status": "uploaded"
        }
    except Exception as e:
        print(f"Upload error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

def is_simple_greeting(message: str) -> bool:
    """Detect if message is a simple greeting that doesn't need full processing"""
    message_lower = message.strip().lower()
    # Remove punctuation and extra spaces
    message_clean = ''.join(c for c in message_lower if c.isalnum() or c.isspace()).strip()
    
    simple_greetings = [
        'hi', 'hello', 'hey', 'hi there', 'hello there', 'hey there',
        'good morning', 'good afternoon', 'good evening',
        'greetings', 'howdy'
    ]
    
    # Check if message is just a greeting (possibly with punctuation)
    words = message_clean.split()
    if len(words) <= 3:  # "hi", "hello there", etc.
        return any(greeting in message_clean for greeting in simple_greetings)
    
    return False

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat using RAG with vector store and uploaded files"""
    try:
        print(f"\n=== Chat Request ===")
        print(f"Conversation ID: {request.conversation_id}")
        print(f"Message: {request.message[:100]}...")
        print(f"Uploaded file IDs: {request.uploaded_file_ids}")
        
        # Check API key
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
        
        # Fast path: Simple greetings without files - return immediately
        has_files = bool(request.uploaded_file_ids and len(request.uploaded_file_ids) > 0)
        if is_simple_greeting(request.message) and not has_files:
            print("🚀 Fast path: Simple greeting detected, returning immediate response")
            greeting_response = (
                "Hello! I'm here to help with EU AI Act compliance. "
                "I can assist you with understanding requirements, technical documentation, "
                "risk classification, and more. What would you like to know?"
            )
            return ChatResponse(
                conversation_id=request.conversation_id,
                message=greeting_response,
                timestamp=datetime.now().isoformat(),
                sources=None,
                used_vector_store=False,
                used_uploaded_files=False,
                used_web_search=False,
                web_search_results=None
            )
        
        # Get or create assistant
        assistant_data = get_or_create_assistant(
            request.conversation_id, 
            request.uploaded_file_ids
        )
        
        thread_id = assistant_data["thread_id"]
        assistant_id = assistant_data["assistant_id"]
        
        # Create message with attachments if files uploaded
        # Add explicit files_attached flag to help assistant
        has_files = bool(request.uploaded_file_ids and len(request.uploaded_file_ids) > 0)
        content = (
            f"[context]\nfiles_attached={str(has_files).lower()}\n[/context]\n\n"
            f"{request.message}"
        )
        
        message_params = {
            "thread_id": thread_id,
            "role": "user",
            "content": content
        }
        
        # Attach uploaded files to this specific message
        if request.uploaded_file_ids:
            message_params["attachments"] = [
                {"file_id": file_id, "tools": [{"type": "file_search"}]}
                for file_id in request.uploaded_file_ids
            ]
        
        # Add message to thread
        client.beta.threads.messages.create(**message_params)
        
        # Determine if we should disable tools for simple queries
        # Disable tools for simple greetings to speed up response
        is_greeting = is_simple_greeting(request.message)
        is_compliance_question = any(keyword in request.message.lower() for keyword in [
            'article', 'compliance', 'requirement', 'eu ai act', 'regulation', 
            'what is', 'how to', 'what do', 'what should', 'need to',
            'best practice', 'best practices', 'oversight', 'risk management',
            'implement', 'guidance', 'recommendation'
        ])
        
        # For compliance questions, ensure tools are available (don't disable)
        tool_choice = "none" if (is_greeting and not has_files and not is_compliance_question) else None
        
        # Run assistant
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            tool_choice=tool_choice
        )
        
        if tool_choice == "none":
            print("⚡ Tools disabled for fast greeting response")
        
        print(f"Run created: {run.id}, waiting for completion...")
        print(f"Vector Store ID configured: {VECTOR_STORE_ID}")
        print(f"Uploaded files attached: {len(request.uploaded_file_ids) if request.uploaded_file_ids else 0}")
        
        # Wait for completion and handle tool calls
        max_attempts = 120  # 2 minutes max (120 seconds)
        attempts = 0
        web_search_results = []
        used_web_search = False
        last_status = None
        
        while run.status in ["queued", "in_progress", "requires_action"] and attempts < max_attempts:
            # Print status updates every 5 seconds
            if attempts % 5 == 0 and run.status != last_status:
                print(f"   Status: {run.status} (attempt {attempts}/{max_attempts})")
                last_status = run.status
            
            if run.status == "requires_action":
                print("⚠️ Run requires action - handling tool calls...")
                tool_outputs = []
                
                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    tool_call_id = tool_call.id
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"   Tool call: {function_name} with args: {function_args}")
                    
                    if function_name == "search_web":
                        query = function_args.get("query", "")
                        print(f"   Executing web search: {query}")
                        web_result = search_web_restricted(query)
                        used_web_search = True
                        web_search_results.extend(web_result.get("results", []))
                        
                        # Format result for assistant
                        if web_result.get("results"):
                            formatted_result = "Web search results:\n\n"
                            for idx, result in enumerate(web_result["results"], 1):
                                formatted_result += f"{idx}. {result['title']}\n"
                                formatted_result += f"   URL: {result['url']}\n"
                                formatted_result += f"   Content: {result['content'][:500]}...\n\n"
                        else:
                            formatted_result = "No results found from official EU sources for this query."
                        
                        tool_outputs.append({
                            "tool_call_id": tool_call_id,
                            "output": formatted_result
                        })
                
                # Submit tool outputs
                if tool_outputs:
                    run = client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    print(f"   Submitted {len(tool_outputs)} tool outputs")
            
            # Optimized polling: faster at start, slower later
            if attempts < 3:
                sleep_time = 0.5  # 0.5s for first 3 attempts
            elif attempts < 10:
                sleep_time = 1    # 1s for next 7 attempts
            else:
                sleep_time = 2    # 2s after that
            
            time.sleep(sleep_time)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            attempts += 1
        
        if attempts >= max_attempts:
            raise Exception("Request timeout - assistant took too long to respond")
        
        if run.status == "completed":
            # Get messages
            messages = client.beta.threads.messages.list(thread_id=thread_id, limit=1)
            
            # Extract response and citations
            response_text = ""
            sources = []
            used_vector_store = False
            used_uploaded_files = False
            
            if messages.data:
                latest_message = messages.data[0]
                
                for content_block in latest_message.content:
                    if hasattr(content_block, 'text'):
                        response_text += content_block.text.value
                        
                        # Extract citations from annotations
                        if hasattr(content_block.text, 'annotations'):
                            for annotation in content_block.text.annotations:
                                if hasattr(annotation, 'file_citation'):
                                    file_id = annotation.file_citation.file_id
                                    sources.append(file_id)
                                    # Check if it's from vector store or uploaded file
                                    if request.uploaded_file_ids and file_id in request.uploaded_file_ids:
                                        used_uploaded_files = True
                                    else:
                                        used_vector_store = True
                
                # Check run steps to see if file_search was used
                run_steps = client.beta.threads.runs.steps.list(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                print(f"\n=== Run Steps Analysis ===")
                print(f"Total steps: {len(run_steps.data)}")
                
                for step in run_steps.data:
                    if hasattr(step, 'step_details'):
                        step_details = step.step_details
                        if hasattr(step_details, 'tool_calls'):
                            for tool_call in step_details.tool_calls:
                                if hasattr(tool_call, 'type'):
                                    print(f"Tool call type: {tool_call.type}")
                                    if tool_call.type == 'file_search':
                                        used_vector_store = True
                                        print("✅ File search tool was used (Vector Store accessed)")
                                        if hasattr(tool_call, 'file_search'):
                                            print(f"   File search query: {getattr(tool_call.file_search, 'query', 'N/A')}")
                        elif hasattr(step_details, 'type'):
                            print(f"Step type: {step_details.type}")
                
                print("=== End Analysis ===\n")
            
            # Check if tools were used for compliance questions
            is_compliance_question = any(keyword in request.message.lower() for keyword in [
                'article', 'compliance', 'requirement', 'eu ai act', 'regulation', 
                'what is', 'how to', 'what do', 'what should', 'need to'
            ])
            
            if is_compliance_question and not used_vector_store and not used_web_search:
                print("⚠️ WARNING: Compliance question detected but no tools were used!")
                print("   This may indicate the assistant is not following instructions to search.")
            
            # Handle empty response
            if not response_text or response_text.strip() == "":
                print("⚠️ Warning: Empty response from assistant")
                response_text = "I apologize, but I wasn't able to generate a response. Please try rephrasing your question or ask about EU AI Act compliance requirements."
            
            print(f"Response: {response_text[:100]}...")
            print(f"Sources found: {len(sources)}")
            print(f"Used Vector Store: {used_vector_store}")
            print(f"Used Uploaded Files: {used_uploaded_files}")
            print(f"Used Web Search: {used_web_search}")
            if used_web_search:
                print(f"Web Search Results: {len(web_search_results)} results")
        
            return ChatResponse(
                conversation_id=request.conversation_id,
                message=response_text,
                timestamp=datetime.now().isoformat(),
                sources=sources if sources else None,
                used_vector_store=used_vector_store,
                used_uploaded_files=used_uploaded_files,
                used_web_search=used_web_search,
                web_search_results=web_search_results if web_search_results else None
            )
        elif run.status == "failed":
            error_details = "Unknown error"
            if hasattr(run, 'last_error') and run.last_error:
                error_details = run.last_error.message if hasattr(run.last_error, 'message') else str(run.last_error)
            error_msg = f"Run failed: {error_details}"
            print(f"❌ {error_msg}")
            print(f"   Run ID: {run.id}")
            print(f"   Thread ID: {thread_id}")
            
            # Try to provide a helpful fallback response instead of just raising an error
            fallback_message = f"I encountered an issue while processing your request. Error: {error_details}. Please try rephrasing your question or ask about specific EU AI Act compliance requirements."
            return ChatResponse(
                conversation_id=request.conversation_id,
                message=fallback_message,
                timestamp=datetime.now().isoformat(),
                sources=None,
                used_vector_store=False,
                used_uploaded_files=False,
                used_web_search=False,
                web_search_results=None
            )
        elif run.status in ["cancelled", "expired"]:
            raise Exception(f"Run {run.status}")
        else:
            raise Exception(f"Run failed with status: {run.status}")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.delete("/api/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation and cleanup assistant"""
    try:
        if conversation_id in user_assistants:
            assistant_data = user_assistants[conversation_id]
            
            # Delete thread
            if assistant_data.get("thread_id"):
                client.beta.threads.delete(assistant_data["thread_id"])
            
            # Delete assistant
            client.beta.assistants.delete(assistant_data["assistant_id"])
            
            del user_assistants[conversation_id]
            print(f"Cleaned up conversation: {conversation_id}")
        
        return {"status": "success"}
    except Exception as e:
        print(f"Error cleaning up: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "RAG Chatbot with Vector Store",
        "vector_store_id": VECTOR_STORE_ID,
        "active_conversations": len(user_assistants)
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "vector_store_id": VECTOR_STORE_ID
    }
