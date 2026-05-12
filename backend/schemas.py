from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


class ProjectIdeaRequest(BaseModel):
    """Incoming user payload containing a project idea."""

    idea: str = Field(..., description="Free-text description of the user's project idea")


class ClarificationQuestion(BaseModel):
    """A single clarification question produced by the analyzer."""

    category: str = Field(..., description="High-level category for the question, e.g. 'security', 'scalability'")
    question: str = Field(..., description="The natural-language question to ask the user")
    importance: Literal["low", "medium", "high"] = Field(
        "medium", description="Estimated importance of the question"
    )


class ClarificationResponse(BaseModel):
    """Structured clarification response returned by the clarification engine.

    - `project_summary`: short summary extracted from the idea
    - `detected_project_type`: classification (e.g. 'SaaS', 'mobile', 'internal tool')
    - `complexity`: quick complexity estimate
    - `questions`: list of clarification questions to ask the user
    """

    project_summary: str = Field(..., description="Short normalized summary of the project idea")
    detected_project_type: str = Field(..., description="Detected project type or category")
    complexity: Literal["low", "medium", "high"] = Field(
        ..., description="Estimated project complexity"
    )
    questions: List[ClarificationQuestion] = Field(
        default_factory=list, description="Clarification questions to present to the user"
    )


class LLMRawResponse(BaseModel):
    """Raw LLM response wrapper for storage and debugging."""

    raw_text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMParsedResponse(BaseModel):
    """Parsed LLM response when coercible to a Python object/dict."""

    parsed: Dict[str, Any]


__all__ = [
    "ProjectIdeaRequest",
    "ClarificationQuestion",
    "ClarificationResponse",
    "LLMRawResponse",
    "LLMParsedResponse",
]
