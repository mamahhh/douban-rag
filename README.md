# Douban RAG System 📚

[中文文档](README_CN.md)

A modern, intelligent RAG (Retrieval-Augmented Generation) system for your Douban (豆瓣) history. Chat with your personal library of movies, books, music, and games using natural language.

![Douban RAG Interface](interface.png)

##  Features

- **Personal Knowledge Base**: Upload your Douban export files (CSV/XLSX) to create a searchable personal database.
- **Intelligent Chat**: Ask natural language questions about your history (e.g., *"What movies did I think had a bad ending?"*).
- **Rich context**: The system retrieves your specific reviews, ratings, and comments to generate personalized answers.
- **Statistics Dashboard**: precise tracking of your processed items:
  -  Movies
  -  Books
  -  Music
  -  Games
- **Modern UI**: specialized dark mode interface with responsive design.
- **Secure Authentication**: User accounts powered by Firebase Auth.

##  Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11
- **RAG Engine**: LlamaIndex, ChromaDB
- **Embeddings**: BGE-M3 (multilingual support)
- **LLM**: Google Gemini
- **Auth**: Firebase Authentication
- **Deployment**: Google Cloud Run (Docker)

##  Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Firebase Project
- Google Gemini API Key

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file with your keys
# GOOGLE_API_KEY=...
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install

# Create .env.local with Firebase config
# NEXT_PUBLIC_FIREBASE_API_KEY=...
# NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

npm run dev
```

### 3. Usage

1.  Open the app at `http://localhost:3000`
2.  Sign in / Sign up
3.  Upload your Douban export file (supports exports from [豆伴](https://chromewebstore.google.com/detail/%E8%B1%86%E4%BC%B4%EF%BC%9A%E8%B1%86%E7%93%A3%E8%B4%A6%E5%8F%B7%E5%A4%87%E4%BB%BD%E5%B7%A5%E5%85%B7/ghppfgfeoafdcaebjoglabppkfmbcjdd))
4.  Wait for processing to complete (stats will update in sidebar)
5.  Start chatting!

## Docker / Deployment

The project is containerized for easy deployment.

```bash
# Build and run with Docker Compose (optional addition)
docker-compose up --build
```

Or deploy to Google Cloud Run using the included `cloudbuild.yaml`.

## License

MIT
