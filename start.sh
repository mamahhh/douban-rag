#!/bin/bash
set -e

# Start backend in background
cd /app/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to start
sleep 5

# Start frontend on the main port (Cloud Run expects PORT env var)
cd /app/frontend
streamlit run app.py \
    --server.port=${PORT:-8080} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
