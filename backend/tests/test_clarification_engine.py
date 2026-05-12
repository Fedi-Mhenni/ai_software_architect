"""Unit tests for ClarificationEngine with mocked LLM service."""
import json
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.clarification_engine import ClarificationEngine
from schemas import ClarificationResponse, LLMRawResponse


@pytest.fixture
def mock_llm_service():
    """Create a mock LLMService that returns valid JSON."""
    service = MagicMock()
    
    # Example valid clarification response JSON
    valid_response_json = {
        "project_summary": "Test SaaS project",
        "detected_project_type": "SaaS",
        "complexity": "medium",
        "questions": [
            {
                "category": "users",
                "question": "Who are the primary users?",
                "importance": "high"
            }
        ]
    }
    
    raw_response = LLMRawResponse(
        raw_text=json.dumps(valid_response_json),
        metadata={"provider": "mock", "model": "mock"}
    )
    service.call.return_value = (raw_response, None)
    service.provider = "mock"
    return service


@pytest.fixture
def clarification_engine(mock_llm_service):
    """Create a ClarificationEngine with mocked LLM."""
    with patch('orchestrator.clarification_engine.get_llm_service', return_value=mock_llm_service):
        engine = ClarificationEngine()
        engine.llm_service = mock_llm_service
        return engine


def test_clarification_engine_clarifies_project_idea(clarification_engine, mock_llm_service):
    """Test that engine processes a project idea and returns ClarificationResponse."""
    idea = "Create a SaaS for restaurant delivery management"
    
    response = clarification_engine.clarify(idea)
    
    assert isinstance(response, ClarificationResponse)
    assert response.project_summary == "Test SaaS project"
    assert response.detected_project_type == "SaaS"
    assert response.complexity == "medium"
    assert len(response.questions) > 0
    assert mock_llm_service.call.called


def test_clarification_engine_validates_response(clarification_engine, mock_llm_service):
    """Test that engine validates the LLM response structure."""
    response = clarification_engine.clarify("Test project")
    
    # Verify all required fields are present
    assert response.project_summary is not None
    assert response.detected_project_type is not None
    assert response.complexity in ["low", "medium", "high"]
    assert isinstance(response.questions, list)
    for q in response.questions:
        assert q.category is not None
        assert q.question is not None
        assert q.importance in ["low", "medium", "high"]


def test_clarification_engine_handles_invalid_json(clarification_engine, mock_llm_service):
    """Test that engine handles invalid LLM JSON response gracefully."""
    mock_llm_service.call.return_value = (
        LLMRawResponse(raw_text="not valid json", metadata={}),
        None
    )
    
    with pytest.raises(Exception):  # Should raise due to invalid JSON
        clarification_engine.clarify("Test project")


def test_clarification_engine_calls_llm_with_prompt(clarification_engine, mock_llm_service):
    """Test that engine passes the project idea to LLM."""
    idea = "Create a marketplace for freelancers"
    
    clarification_engine.clarify(idea)
    
    # Verify LLM was called with a prompt containing the idea
    mock_llm_service.call.assert_called_once()
    call_args = mock_llm_service.call.call_args
    assert call_args is not None
    prompt = call_args[0][0]  # First positional argument
    assert idea in prompt or "marketplace" in prompt.lower()

