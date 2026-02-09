# Multi-stage build for smaller image
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Copy frontend files and install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# Python backend stage
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install Node.js for Next.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=backend-builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy backend code
COPY backend/ ./backend/

# Copy Next.js build and dependencies
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/node_modules ./frontend/node_modules
COPY --from=frontend-builder /app/frontend/package.json ./frontend/package.json
COPY --from=frontend-builder /app/frontend/public ./frontend/public

# Copy demo data
COPY data/demo.xlsx ./data/demo.xlsx

# Create data directories
RUN mkdir -p /app/data/raw /app/data/chromadb

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV NODE_ENV=production

# Expose port
EXPOSE 8080

# Start script will run both backend and frontend
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
