from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from schemas import ClarificationResponse, ProjectIdeaRequest
from services.llm_service import LLMService, LLMServiceError, get_llm_service
from utils.json_utils import parse_and_validate_json, validate_json_with_model

logger = logging.getLogger(__name__)


class ClarificationEngineError(RuntimeError):
    pass


class ClarificationEngine:
    """Single-orchestrator clarification engine.

    Responsibilities:
    - load and render the architect prompt template
    - call the LLM service
    - validate and normalize the JSON output into ClarificationResponse
    """

    def __init__(self, llm_service: Optional[LLMService] = None, prompt_path: Optional[Path] = None):
        self.llm_service = llm_service or get_llm_service()
        self.prompt_path = prompt_path or self._default_prompt_path()
        logger.debug("ClarificationEngine initialized with provider=%s", self.llm_service.provider)

    def _default_prompt_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "prompts" / "architect_prompt.txt"

    def load_prompt_template(self) -> str:
        try:
            logger.debug("Loading prompt template from %s", self.prompt_path)
            return self.prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            logger.error("Prompt file not found at %s", self.prompt_path)
            raise ClarificationEngineError(f"Prompt file not found: {self.prompt_path}") from exc

    def build_prompt(self, idea: str) -> str:
        template = self.load_prompt_template()
        return template.replace("{idea}", idea.strip())

    def clarify(self, idea: str | ProjectIdeaRequest) -> ClarificationResponse:
        start_time = time.time()
        idea_text = idea.idea if isinstance(idea, ProjectIdeaRequest) else idea
        if not idea_text or not idea_text.strip():
            logger.warning("Empty idea provided to clarify()")
            raise ClarificationEngineError("idea cannot be empty")

        logger.info("Starting clarification: idea_length=%d", len(idea_text))
        prompt = self.build_prompt(idea_text)
        
        try:
            logger.debug("Calling LLM service with prompt")
            llm_start = time.time()
            raw_response, parsed_response = self.llm_service.call(prompt)
            llm_duration = time.time() - llm_start
            logger.info("LLM call completed in %.2fs", llm_duration)
        except LLMServiceError as exc:
            logger.error("LLM service error: %s", exc)
            raise ClarificationEngineError(str(exc)) from exc

        try:
            if parsed_response is not None:
                logger.debug("Validating pre-parsed LLM response")
                validated = validate_json_with_model(parsed_response.parsed, ClarificationResponse)
            else:
                logger.debug("Parsing and validating raw LLM text response")
                validated = parse_and_validate_json(raw_response.raw_text, ClarificationResponse)
            
            elapsed = time.time() - start_time
            logger.info("Clarification completed successfully in %.2fs", elapsed)
            return validated
        except ValidationError as exc:
            logger.error("LLM response failed ClarificationResponse validation: %s", exc)
            raise ClarificationEngineError("LLM response validation failed") from exc
        except Exception as exc:
            logger.error("Failed to parse/validate LLM response: %s", exc)
            raise ClarificationEngineError("Failed to parse or validate LLM response") from exc


def get_clarification_engine() -> ClarificationEngine:
    return ClarificationEngine()
