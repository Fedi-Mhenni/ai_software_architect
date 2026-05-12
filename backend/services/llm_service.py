"""LLM service abstraction for calling OpenAI, Google Gemini, or Groq (placeholder).

Responsibilities:
- select provider via env var `LLM_PROVIDER` ("openai", "google", or "groq")
- call provider API with retries and backoff
- extract/parse JSON from LLM text responses
- return raw and parsed wrappers

This implementation keeps network calls isolated and provides simple retry/error handling.
"""
from __future__ import annotations

import json
import logging
import importlib
import os
import time
from typing import Any, Dict, Optional, Tuple

import httpx

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - openai may not be installed in some environments
    OpenAI = None

try:
    genai = importlib.import_module("google.genai")
    genai_types = importlib.import_module("google.genai.types")
except Exception:  # pragma: no cover - google may not be installed
    genai = None
    genai_types = None

from schemas import ClarificationResponse, LLMParsedResponse, LLMRawResponse
from utils.json_utils import extract_json_from_text

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "google")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")


class LLMServiceError(RuntimeError):
    pass


class LLMService:
    def __init__(self, provider: str = DEFAULT_PROVIDER, timeout: int = 30):
        self.provider = provider.lower()
        self.timeout = timeout
        self.openai_client = None
        self.google_client = None
        self.google_config = None
        
        if self.provider == "openai":
            if OpenAI is None:
                raise LLMServiceError("openai package is not installed")
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        elif self.provider == "google":
            if genai is None or genai_types is None:
                raise LLMServiceError("google-genai package is not installed")
            if not GOOGLE_API_KEY:
                raise LLMServiceError("GOOGLE_API_KEY environment variable not set")
            self.google_client = genai.Client(api_key=GOOGLE_API_KEY)
            self.google_config = genai_types.GenerateContentConfig(max_output_tokens=1024, temperature=0.0)

    def _retry_loop(self, func, retries: int = 3, backoff: float = 1.0, *args, **kwargs):
        last_exc = None
        for attempt in range(1, retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - broad on purpose for retries
                last_exc = exc
                sleep = backoff * (2 ** (attempt - 1))
                logger.warning("LLM call failed (attempt %s/%s): %s — retrying in %ss", attempt, retries, exc, sleep)
                time.sleep(sleep)
        raise LLMServiceError(f"LLM call failed after {retries} attempts: {last_exc}")

    def call(self, prompt: str, *, max_tokens: int = 1024, model: Optional[str] = None) -> Tuple[LLMRawResponse, Optional[LLMParsedResponse]]:
        """Call the configured LLM provider and return raw + parsed response (parsed may be None).

        This is a synchronous function. For async usage wrap via loop.run_in_executor.
        """
        if self.provider == "openai":
            raw = self._retry_loop(self._call_openai, 3, 1.0, prompt, max_tokens, model)
        elif self.provider == "google":
            raw = self._retry_loop(self._call_google, 3, 1.0, prompt, max_tokens, model)
        elif self.provider == "groq":
            raw = self._retry_loop(self._call_groq, 3, 1.0, prompt, max_tokens, model)
        else:
            raise LLMServiceError(f"Unknown LLM provider: {self.provider}")

        parsed = None
        try:
            parsed_json = extract_json_from_text(raw.raw_text)
            parsed = LLMParsedResponse(parsed=parsed_json)
        except Exception as e:
            logger.debug("Failed to parse JSON from LLM raw response: %s", e)
            parsed = None

        return raw, parsed

    def _call_openai(self, prompt: str, max_tokens: int, model: Optional[str]) -> LLMRawResponse:
        if self.openai_client is None:
            raise LLMServiceError("openai package is not available")
        model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.debug("Calling OpenAI model=%s max_tokens=%s", model, max_tokens)
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.0,
                timeout=self.timeout,
            )
            # Extract text
            text = None
            choices = getattr(response, "choices", None)
            if choices and len(choices) > 0:
                first_choice = choices[0]
                message = getattr(first_choice, "message", None)
                text = getattr(message, "content", None) if message else None
                if not text:
                    text = getattr(first_choice, "text", None)

            if not text:
                raise LLMServiceError("Empty response from OpenAI")

            return LLMRawResponse(raw_text=text, metadata={"provider": "openai", "model": model})
        except Exception as e:
            logger.exception("OpenAI call failed: %s", e)
            raise

    def _call_google(self, prompt: str, max_tokens: int, model: Optional[str]) -> LLMRawResponse:
        if self.google_client is None:
            raise LLMServiceError("google-genai is not configured")
        model = model or GOOGLE_MODEL
        logger.debug("Calling Google Gemini model=%s max_tokens=%s", model, max_tokens)
        try:
            if genai_types is None:
                raise LLMServiceError("google-genai types are not available")
            response = self.google_client.models.generate_content(
                model=model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.0,
                    response_mime_type="application/json",
                    response_schema=ClarificationResponse,
                ),
            )
            text = getattr(response, "text", None)
            if not text:
                raise LLMServiceError("Empty response from Google Gemini")
            return LLMRawResponse(raw_text=text, metadata={"provider": "google", "model": model})
        except Exception as e:
            logger.exception("Google Gemini call failed: %s", e)
            raise

    def _call_groq(self, prompt: str, max_tokens: int, model: Optional[str]) -> LLMRawResponse:
        # Placeholder implementation for Groq — adapt to Groq API when available.
        logger.debug("Calling Groq (placeholder) model=%s", model)
        if not GROQ_API_KEY:
            raise LLMServiceError("GROQ_API_KEY not configured")

        # Example using httpx — endpoint details depend on Groq provider
        groq_endpoint = os.getenv("GROQ_ENDPOINT", "https://api.groq.com/v1/generate")
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {"prompt": prompt, "max_tokens": max_tokens}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.post(groq_endpoint, json=payload, headers=headers)
                r.raise_for_status()
                data = r.json()
                # normalize according to actual response shape
                text = data.get("text") or data.get("output") or json.dumps(data)
                return LLMRawResponse(raw_text=text, metadata={"provider": "groq"})
        except Exception as e:
            logger.exception("Groq call failed: %s", e)
            raise


# Simple module-level helper
_default_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _default_llm_service
    if _default_llm_service is None:
        _default_llm_service = LLMService()
    return _default_llm_service


if __name__ == "__main__":
    # quick local sanity check (no network mocking)
    svc = LLMService()
    try:
        raw, parsed = svc.call("{\"test\": true}")
        print("RAW:", raw)
        print("PARSED:", parsed)
    except Exception as e:
        print("LLM service test failed:", e)
