#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo "Stopping LawMinded Bot..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup SIGINT

echo "🚀 Starting LawMinded Compliance Bot..."

# Start Backend
echo "-----------------------------------"
echo "🐍 Starting Backend (Port 8001)..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check for .env
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: No .env file found in backend/. Please create one with OPENAI_API_KEY."
fi

uvicorn main:app --reload --port 8001 &
BACKEND_PID=$!
cd ..

# Sleep briefly to let backend init
sleep 2

# Start Frontend
echo "-----------------------------------"
echo "⚛️  Starting Frontend (Port 3000)..."
cd frontend
npm install
npm start &
FRONTEND_PID=$!
cd ..

echo "-----------------------------------"
echo "✅ Bot services started!"
echo "📡 Backend: http://localhost:8001"
echo "💻 Frontend: http://localhost:3000"
echo "press CTRL+C to stop"

wait $BACKEND_PID $FRONTEND_PID
