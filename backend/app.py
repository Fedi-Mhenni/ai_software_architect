import logging
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from orchestrator.clarification_engine import ClarificationEngineError, get_clarification_engine
from schemas import ClarificationResponse

app = FastAPI(title="AI Software Architect", version="0.1.0")
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class AnalyzeProjectRequest(BaseModel):
    idea: str = Field(..., min_length=1, description="Project idea to analyze")


class HealthResponse(BaseModel):
    status: Literal["ok"]


@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {"status": "ok"}


@app.post("/analyze-project", response_model=ClarificationResponse, status_code=200)
def analyze_project(payload: AnalyzeProjectRequest):
    """Analyze a project idea and generate clarification questions."""
    engine = get_clarification_engine()

    idea = payload.idea.strip()
    if not idea:
        logger.warning("Empty idea received in analyze_project request")
        raise HTTPException(status_code=400, detail="idea cannot be empty")

    logger.info("POST /analyze-project - processing idea (length=%d)", len(idea))
    try:
        result = engine.clarify(idea)
        logger.info("Successfully analyzed project; generated %d questions", len(result.questions))
        return result
    except ClarificationEngineError as exc:
        logger.error("ClarificationEngine error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze project") from exc
    except Exception as exc:
        logger.error("Unexpected error during project analysis", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
