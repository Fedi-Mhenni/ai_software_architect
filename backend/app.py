import logging
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from orchestrator.clarification_engine import ClarificationEngineError, get_clarification_engine
from schemas import ClarificationResponse

app = FastAPI(title="AI Software Architect", version="0.1.0")
logger = logging.getLogger(__name__)


class AnalyzeProjectRequest(BaseModel):
    idea: str = Field(..., min_length=1, description="Project idea to analyze")


class HealthResponse(BaseModel):
    status: Literal["ok"]


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


@app.post("/analyze-project", response_model=ClarificationResponse, status_code=200)
def analyze_project(payload: AnalyzeProjectRequest):
    engine = get_clarification_engine()

    idea = payload.idea.strip()
    if not idea:
        raise HTTPException(status_code=400, detail="idea cannot be empty")

    logger.info("Analyzing project idea: %s", idea)
    try:
        result = engine.clarify(idea)
        return result
    except ClarificationEngineError as exc:
        logger.exception("Clarification engine error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during project analysis: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
