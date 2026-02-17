from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import io

def test_verify_auth(client: TestClient):
    """Test that mock auth dependency works."""
    response = client.get("/api/auth/verify")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True
    assert data["uid"] == "test-user"

def test_upload_file(client: TestClient, mock_rag_engine):
    """Test file upload endpoint."""
    # Create mock file in memory
    file_content = b"header1,header2\nvalue1,value2"
    files = {"file": ("test.csv", io.BytesIO(file_content), "text/csv")}
    
    response = client.post("/api/upload", files=files)
    
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["message"] == "File uploaded and indexed successfully"
    assert json_response["filename"] == "test.csv"
    
    # Verify mock calls
    mock_rag_engine["process_douban_file"].assert_called_once()
    mock_rag_engine["create_index"].assert_called_once()


def test_chat(client: TestClient):
    """Test chat endpoint."""
    response = client.post(
        "/api/chat",
        json={"message": "What movies did I watch?"}
    )
    
    assert response.status_code == 200
    assert response.json() == {"response": "This is a mock response."}


def test_chat_saves_history(client: TestClient):
    """Test that chat messages are saved to history."""
    # Send a chat message
    client.post("/api/chat", json={"message": "Hello!"})

    # Fetch history
    response = client.get("/api/chat/history")
    assert response.status_code == 200
    data = response.json()
    messages = data["messages"]
    assert len(messages) >= 2  # user + assistant
    assert messages[-2]["role"] == "user"
    assert messages[-2]["content"] == "Hello!"
    assert messages[-1]["role"] == "assistant"
    assert messages[-1]["content"] == "This is a mock response."


def test_chat_history_empty(client: TestClient):
    """Test that history starts empty (per-user isolation)."""
    # Clear any prior messages first
    client.delete("/api/chat/history")
    response = client.get("/api/chat/history")
    assert response.status_code == 200
    assert response.json()["messages"] == []


def test_clear_chat_history(client: TestClient):
    """Test clearing chat history."""
    # Send a message to create history
    client.post("/api/chat", json={"message": "Test"})

    # Clear it
    response = client.delete("/api/chat/history")
    assert response.status_code == 200

    # Verify empty
    response = client.get("/api/chat/history")
    assert response.json()["messages"] == []
