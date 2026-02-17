# LawMinded Compliance Assistant

An intelligent, streaming chatbot designed to help users navigate the EU AI Act compliance landscape.

## 🚀 Quick Start

The easiest way to run the bot is using the provided start script:

```bash
chmod +x start.sh
./start.sh
```

## 🛠️ Manual Setup

If you prefer to run services individually:

### 1. Backend (Python/FastAPI)

The backend handles the AI logic, OpenAI integration, and streaming responses.

**Prerequisites**:
-   Python 3.8+
-   OpenAI API Key

**Setup**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Run**:
```bash
# Make sure .env is set with OPENAI_API_KEY
uvicorn main:app --reload --port 8005
```
*Backend will run at http://localhost:8001*

### 2. Frontend (React)

The frontend provides the chat interface.

**Prerequisites**:
-   Node.js 16+
-   npm

**Setup**:
```bash
cd frontend
npm install
```

**Run**:
```bash
npm start
```
*Frontend will run at http://localhost:3000*

## 🔑 Environment Variables

Make sure you have a `.env` file in the `backend/` directory with:

```env
OPENAI_API_KEY=sk-your-key-here
TAVILY_API_KEY=tvLY-your-key-here  # Optional, for web search
VECTOR_STORE_ID=vs_...             # Optional, if using existing store
```

## ✨ Features

-   **Streaming Responses**: Real-time token streaming for faster interactions.
-   **Singleton Assistant**: Efficiently manages one OpenAI Assistant instance.
-   **Risk Classification**: Structured tool to classify AI systems under the EU AI Act.
-   **File Analysis**: Upload and analyze PDF/Docx files for compliance.