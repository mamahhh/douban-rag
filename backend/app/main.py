from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from app.api.endpoints import router as api_router

app = FastAPI(title="Douban RAG System", version="0.1.0")

# CORS setup for Streamlit
origins = [
    "http://localhost:8501",  # Streamlit
    "http://localhost:3000",  # Next.js
    "https://douban-rag-*.a.run.app",
    "http://127.0.0.1:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Douban RAG API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
