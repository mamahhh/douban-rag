import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.auth import get_current_user, User
from app.rag.settings import init_settings

@pytest.fixture
def mock_settings():
    """Mock init_settings to prevent real model loading."""
    with patch("app.rag.settings.init_settings") as mock_init:
        mock_init.return_value = MagicMock()
        yield mock_init

@pytest.fixture
def mock_firebase():
    """Mock Firebase Admin SDK."""
    with patch("app.auth.auth.firebase_admin") as mock_firebase:
        mock_firebase.initialize_app.return_value = MagicMock()
        yield mock_firebase

@pytest.fixture
def mock_rag_engine():
    """Mock RAG engine components."""
    # Patch where the functions are imported/used in endpoints.py
    with patch("app.api.endpoints.create_index") as mock_create_index, \
         patch("app.api.endpoints.get_chat_engine") as mock_get_chat_engine, \
         patch("app.rag.ingestion.process_douban_file") as mock_process:
        
        # Mock chat engine response
        mock_chat_engine = MagicMock()
        mock_chat_engine.chat.return_value = "This is a mock response."
        mock_get_chat_engine.return_value = mock_chat_engine
        
        # Mock processing result
        mock_doc = MagicMock()
        mock_doc.metadata = {"media_type": "movie"}
        # process_douban_file returns a list of documents
        mock_process.return_value = [mock_doc]
        
        yield {
            "create_index": mock_create_index,
            "get_chat_engine": mock_get_chat_engine,
            "process_douban_file": mock_process
        }

@pytest.fixture
def client(mock_settings, mock_firebase, mock_rag_engine):
    """TestClient with mocked dependencies."""
    
    # Override dependency to simulate logged-in user
    async def override_get_current_user():
        return User(
            uid="test-user",
            email="test@example.com",
            display_name="Test User",
            email_verified=True
        )
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()
