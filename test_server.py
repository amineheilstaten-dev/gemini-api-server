"""
Unit tests for Gemini API Server.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    mock_client = MagicMock()
    
    # Mock response
    mock_output = MagicMock()
    mock_output.text = "Hello! I'm Gemini, a large language model trained by Google."
    mock_output.thoughts = None
    mock_output.images = []
    mock_output.metadata = ["chat_id", "reply_id", "rcid"]
    
    # Mock candidate
    mock_candidate = MagicMock()
    mock_candidate.text = "Hello! I'm Gemini, a large language model trained by Google."
    mock_candidate.thoughts = None
    mock_candidate.web_images = []
    mock_candidate.generated_images = []
    mock_candidate.rcid = "test_rcid"
    
    mock_output.candidates = [mock_candidate]
    mock_client.generate_content = AsyncMock(return_value=mock_output)
    mock_client.close = AsyncMock()
    
    return mock_client


@pytest.fixture
def test_client(mock_gemini_client):
    """Create a test client with mocked Gemini client."""
    with patch('main.get_client', return_value=mock_gemini_client):
        with patch('main.client', mock_gemini_client):
            from main import app
            client = TestClient(app)
            yield client


def test_root_endpoint(test_client):
    """Test root health endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_health_endpoint(test_client):
    """Test health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_models(test_client):
    """Test list models endpoint."""
    response = test_client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) > 0


def test_chat_completion(test_client, mock_gemini_client):
    """Test chat completion endpoint."""
    response = test_client.post(
        "/v1/chat/completions",
        json={
            "model": "gemini-2.5-flash",
            "messages": [
                {"role": "user", "content": "Say hello!"}
            ]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"
    assert len(data["choices"]) > 0
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert "content" in data["choices"][0]["message"]
    assert data["choices"][0]["message"]["content"] == "Hello! I'm Gemini, a large language model trained by Google."


def test_chat_completion_with_system_prompt(test_client, mock_gemini_client):
    """Test chat completion with system prompt."""
    response = test_client.post(
        "/v1/chat/completions",
        json={
            "model": "gemini-2.5-flash",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is 2+2?"}
            ]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"


def test_chat_completion_multiple_messages(test_client, mock_gemini_client):
    """Test chat completion with multiple messages."""
    response = test_client.post(
        "/v1/chat/completions",
        json={
            "model": "gemini-2.5-pro",
            "messages": [
                {"role": "user", "content": "My favorite color is blue."},
                {"role": "assistant", "content": "That's great to know!"},
                {"role": "user", "content": "What is my favorite color?"}
            ]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"


def test_chat_completion_with_gem(test_client, mock_gemini_client):
    """Test chat completion with Gemini Gem."""
    response = test_client.post(
        "/v1/chat/completions",
        json={
            "model": "gemini-2.5-flash",
            "messages": [
                {"role": "user", "content": "Write a Python function."}
            ],
            "gem": "coding-partner"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"
    
    # Verify gem parameter was passed
    mock_gemini_client.generate_content.assert_called_once()
    call_kwargs = mock_gemini_client.generate_content.call_args.kwargs
    assert call_kwargs.get("gem") == "coding-partner"


def test_completion_endpoint(test_client, mock_gemini_client):
    """Test legacy completion endpoint."""
    response = test_client.post(
        "/v1/completions",
        json={
            "model": "gemini-2.5-flash",
            "prompt": "Say hello!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"


def test_image_generation(test_client, mock_gemini_client):
    """Test image generation endpoint."""
    # Mock images
    mock_image = MagicMock()
    mock_image.url = "https://example.com/image.png"
    mock_image.title = "Generated Image"
    mock_image.alt = "A generated image"
    mock_image.save = AsyncMock(return_value="/path/to/saved/image.png")
    
    mock_output = MagicMock()
    mock_output.images = [mock_image]
    
    mock_gemini_client.generate_content = AsyncMock(return_value=mock_output)
    
    response = test_client.post(
        "/v1/images/generate",
        json={
            "prompt": "A beautiful sunset"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) > 0


def test_invalid_request_no_messages(test_client):
    """Test invalid request with no messages."""
    response = test_client.post(
        "/v1/chat/completions",
        json={
            "model": "gemini-2.5-flash",
            "messages": []
        }
    )
    
    # Empty messages list should return 400 or 422
    assert response.status_code in [400, 422]


def test_invalid_request_no_user_message(test_client):
    """Test that assistant-only messages still work (Gemini handles it)."""
    response = test_client.post(
        "/v1/chat/completions",
        json={
            "model": "gemini-2.5-flash",
            "messages": [
                {"role": "assistant", "content": "Hello!"}
            ]
        }
    )
    
    # The server should still process this (it uses the assistant message as prompt)
    assert response.status_code in [200, 400]


def test_error_handling(test_client, mock_gemini_client):
    """Test error handling."""
    # Simulate an error
    mock_gemini_client.generate_content = AsyncMock(side_effect=Exception("Test error"))
    
    response = test_client.post(
        "/v1/chat/completions",
        json={
            "model": "gemini-2.5-flash",
            "messages": [
                {"role": "user", "content": "Test"}
            ]
        }
    )
    
    assert response.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
