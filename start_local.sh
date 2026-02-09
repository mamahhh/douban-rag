#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID
    exit
}

# Trap SIGINT (Ctrl+C) and call cleanup
trap cleanup SIGINT

# Activate virtual environment if not already active
if [[ -z "$VIRTUAL_ENV" ]]; then
    if [[ -d ".venv" ]]; then
        echo "Activating virtual environment (.venv)..."
        source .venv/bin/activate
    elif [[ -d "venv" ]]; then
        echo "Activating virtual environment (venv)..."
        source venv/bin/activate
    else
        echo "Warning: No virtual environment found in .venv or venv"
    fi
fi

# Start Backend
echo "Starting Backend (port 8000)..."
cd backend
python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to initialize
sleep 2

# Start Frontend
echo "Starting Frontend (port 8501)..."
cd frontend
python -m streamlit run app.py --server.port 8501 &
FRONTEND_PID=$!
cd ..

echo "Services started. Press Ctrl+C to stop."
wait
