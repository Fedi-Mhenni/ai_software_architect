from __future__ import annotations

import logging
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

    def _default_prompt_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "prompts" / "architect_prompt.txt"

    def load_prompt_template(self) -> str:
        try:
            return self.prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ClarificationEngineError(f"Prompt file not found: {self.prompt_path}") from exc

    def build_prompt(self, idea: str) -> str:
        template = self.load_prompt_template()
        return template.replace("{idea}", idea.strip())

    def clarify(self, idea: str | ProjectIdeaRequest) -> ClarificationResponse:
        idea_text = idea.idea if isinstance(idea, ProjectIdeaRequest) else idea
        if not idea_text or not idea_text.strip():
            raise ClarificationEngineError("idea cannot be empty")

        prompt = self.build_prompt(idea_text)
        try:
            raw_response, parsed_response = self.llm_service.call(prompt)
        except LLMServiceError as exc:
            raise ClarificationEngineError(str(exc)) from exc

        try:
            if parsed_response is not None:
                validated = validate_json_with_model(parsed_response.parsed, ClarificationResponse)
            else:
                validated = parse_and_validate_json(raw_response.raw_text, ClarificationResponse)
            return validated
        except ValidationError as exc:
            logger.exception("LLM response failed ClarificationResponse validation: %s", exc)
            raise ClarificationEngineError("LLM response validation failed") from exc
        except Exception as exc:
            logger.exception("Failed to parse/validate LLM response: %s", exc)
            raise ClarificationEngineError("Failed to parse or validate LLM response") from exc


def get_clarification_engine() -> ClarificationEngine:
    return ClarificationEngine()
