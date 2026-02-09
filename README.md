# Douban RAG System 📚

A RAG (Retrieval-Augmented Generation) system for querying your Douban (豆瓣) history - movies, books, music, and games.

## Features

- **Upload Douban exports** - Support for CSV and XLSX files from [豆伴](https://chromewebstore.google.com/detail/%E8%B1%86%E4%BC%B4%EF%BC%9A%E8%B1%86%E7%93%A3%E8%B4%A6%E5%8F%B7%E5%A4%87%E4%BB%BD%E5%B7%A5%E5%85%B7/ghppfgfeoafdcaebjoglabppkfmbcjdd) or other export tools
- **Semantic search** - Find content based on meaning, not just keywords
- **Natural language Q&A** - Ask questions about your viewing/reading history
- **MCP Integration** - Connect to AI assistants like Claude, Gemini, ChatGPT
- **Statistics** - View breakdowns by media type, ratings, and more

## Tech Stack

- **Backend**: FastAPI + LlamaIndex + ChromaDB
- **Frontend**: Streamlit
- **Embeddings**: BGE-M3 (BAAI/bge-m3)
- **Reranker**: BGE-Reranker-v2-m3
- **LLM**: Google Gemini

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
pip install streamlit requests
```

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Run the Application

```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
streamlit run app.py --server.port 8501
```

### 4. Upload Your Data

1. Open http://localhost:8501
2. Upload your Douban export file (from [豆伴](https://chromewebstore.google.com/detail/%E8%B1%86%E4%BC%B4%EF%BC%9A%E8%B1%86%E7%93%A3%E8%B4%A6%E5%8F%B7%E5%A4%87%E4%BB%BD%E5%B7%A5%E5%85%B7/ghppfgfeoafdcaebjoglabppkfmbcjdd) or similar)
3. Start chatting with your data!

## MCP Integration

To use with AI assistants via Model Context Protocol:

```json
{
  "mcpServers": {
    "douban-rag": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/douban-rag"
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `search_douban` | Semantic search across your Douban history |
| `ask_douban` | Natural language Q&A about your records |
| `get_stats` | Get statistics overview |

## Project Structure

```
douban-rag/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI endpoints
│   │   ├── core/         # Configuration
│   │   └── rag/          # RAG logic (ingestion, preprocessing, engine)
│   └── requirements.txt
├── frontend/
│   └── app.py            # Streamlit UI
├── mcp_server.py         # MCP server for AI integration
└── data/                 # Data directory (gitignored)
```

## License

MIT
