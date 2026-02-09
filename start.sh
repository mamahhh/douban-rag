#!/bin/bash
set -e

# Start backend in background
cd /app/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to start
sleep 5

# Start Next.js frontend on the main port (Cloud Run expects PORT env var)
cd /app/frontend
npm run start -- -p ${PORT:-8080}
