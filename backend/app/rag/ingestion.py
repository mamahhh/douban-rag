"""
Ingestion module for Douban RAG system.

Handles loading, processing, and indexing Douban export files.
"""

import os
from typing import List
import chromadb
from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from app.core.config import settings
from app.rag.settings import init_settings
from app.rag.preprocessing import load_and_process_file

# Initialize LLM and embedding settings
init_settings()


def get_vector_store():
    """Get or create the ChromaDB vector store."""
    # Ensure persist directory exists
    os.makedirs(settings.PERSIST_DIR, exist_ok=True)
    
    # Persistent Client
    db = chromadb.PersistentClient(path=settings.PERSIST_DIR)
    chroma_collection = db.get_or_create_collection("douban_history")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    return vector_store


def process_douban_file(file_path: str) -> List[Document]:
    """
    Process a Douban export file (CSV or XLSX) and return documents.
    
    This replaces the old parse_excel function with proper preprocessing:
    - Media type detection from sheet/file names
    - Rating normalization (1-5 → 1-10 scale)
    - Structured metadata parsing from 简介
    - Rich text generation for embeddings
    """
    return load_and_process_file(file_path)


def create_index(documents: List[Document]):
    """Create a vector store index from documents."""
    vector_store = get_vector_store()
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context
    )
    return index


def load_index():
    """Load an existing vector store index."""
    vector_store = get_vector_store()
    index = VectorStoreIndex.from_vector_store(vector_store)
    return index


# Keep old function name for backward compatibility
def parse_excel(file_path: str) -> List[Document]:
    """Deprecated: Use process_douban_file instead."""
    return process_douban_file(file_path)
