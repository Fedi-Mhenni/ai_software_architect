"""Integration tests for FastAPI endpoints."""
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
from schemas import ClarificationResponse, LLMRawResponse


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_llm_service():
    """Create a mock LLMService."""
    service = MagicMock()
    
    valid_response = {
        "project_summary": "Test SaaS",
        "detected_project_type": "SaaS",
        "complexity": "medium",
        "questions": [
            {
                "category": "users",
                "question": "Who are the users?",
                "importance": "high"
            }
        ]
    }
    
    raw = LLMRawResponse(raw_text=json.dumps(valid_response), metadata={})
    service.call.return_value = (raw, None)
    service.provider = "mock"
    return service


def test_health_endpoint(client):
    """Test GET /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"


def test_analyze_project_success(client, mock_llm_service):
    """Test POST /analyze-project with valid input."""
    with patch('orchestrator.clarification_engine.get_llm_service', return_value=mock_llm_service):
        payload = {"idea": "Create a project management tool"}
        response = client.post("/analyze-project", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "project_summary" in data
        assert "questions" in data


def test_analyze_project_missing_idea(client):
    """Test POST /analyze-project without required 'idea' field."""
    response = client.post("/analyze-project", json={})
    assert response.status_code == 422  # Validation error


def test_analyze_project_empty_idea(client):
    """Test POST /analyze-project with empty idea."""
    response = client.post("/analyze-project", json={"idea": ""})
    # Pydantic validates min_length=1, so should be 422
    assert response.status_code == 422


def test_analyze_project_with_french_text(client, mock_llm_service):
    """Test POST /analyze-project with French text."""
    with patch('orchestrator.clarification_engine.get_llm_service', return_value=mock_llm_service):
        payload = {"idea": "Je veux créer un SaaS pour restaurants"}
        response = client.post("/analyze-project", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("project_summary") is not None


def test_analyze_project_response_structure(client, mock_llm_service):
    """Test that response conforms to ClarificationResponse schema."""
    with patch('orchestrator.clarification_engine.get_llm_service', return_value=mock_llm_service):
        payload = {"idea": "Test project"}
        response = client.post("/analyze-project", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify schema
        assert isinstance(data.get("questions"), list)
        for q in data.get("questions", []):
            assert "category" in q
            assert "question" in q
            assert "importance" in q
            assert q["importance"] in ["low", "medium", "high"]


def test_analyze_project_llm_error_handling(client, mock_llm_service):
    """Test POST /analyze-project handles LLM errors gracefully."""
    mock_llm_service.call.side_effect = Exception("LLM service error")
    
    with patch('orchestrator.clarification_engine.get_llm_service', return_value=mock_llm_service):
        payload = {"idea": "Test"}
        response = client.post("/analyze-project", json=payload)
        
        # Should return 500 on LLM error
        assert response.status_code == 500

