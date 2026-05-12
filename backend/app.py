import logging
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="AI Software Architect", version="0.1.0")
logger = logging.getLogger(__name__)


class AnalyzeProjectRequest(BaseModel):
    idea: str = Field(..., min_length=1, description="Project idea to analyze")


class AnalyzeProjectResponse(BaseModel):
    status: Literal["analysis_started"]


class HealthResponse(BaseModel):
    status: Literal["ok"]


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


@app.post("/analyze-project", response_model=AnalyzeProjectResponse, status_code=202)
def analyze_project(payload: AnalyzeProjectRequest):
    idea = payload.idea.strip()
    if not idea:
        raise HTTPException(status_code=400, detail="idea cannot be empty")
    logger.info("Analysis requested: %s", idea)
    # Temporary fake response while analysis pipeline is implemented
    return {"status": "analysis_started"}
