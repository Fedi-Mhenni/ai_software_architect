"""LLM service abstraction for calling OpenAI or Groq (placeholder).

Responsibilities:
- select provider via env var `LLM_PROVIDER` ("openai" or "groq")
- call provider API with retries and backoff
- extract/parse JSON from LLM text responses
- return raw and parsed wrappers

This implementation keeps network calls isolated and provides simple retry/error handling.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, Optional, Tuple

import httpx

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - openai may not be installed in some environments
    OpenAI = None

from ..schemas import LLMParsedResponse, LLMRawResponse

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class LLMServiceError(RuntimeError):
    pass


class LLMService:
    def __init__(self, provider: str = DEFAULT_PROVIDER, timeout: int = 30):
        self.provider = provider.lower()
        self.timeout = timeout
        self.openai_client = None
        if self.provider == "openai":
            if OpenAI is None:
                raise LLMServiceError("openai package is not installed")
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Try to extract JSON object from a text blob.

        Strategy:
        - Attempt direct json.loads(text)
        - If fails, search for the first balanced { ... } or [ ... ] and parse
        - If still fails, raise ValueError
        """
        # Try direct parse
        try:
            return json.loads(text)
        except Exception:
            pass

        # Search for JSON object or array using simple bracket matching
        # Find the first '{' or '[' and attempt to find the matching closing bracket.
        start_match = re.search(r"[\[{]", text)
        if not start_match:
            raise ValueError("No JSON object or array found in text")

        start = start_match.start()
        stack = []
        pairs = {"{": "}", "[": "]"}
        for i in range(start, len(text)):
            ch = text[i]
            if ch in pairs:
                stack.append(pairs[ch])
            elif stack and ch == stack[-1]:
                stack.pop()
                if not stack:
                    candidate = text[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        # continue searching if parsing fails
                        pass
        raise ValueError("Could not extract valid JSON from text")

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
        elif self.provider == "groq":
            raw = self._retry_loop(self._call_groq, 3, 1.0, prompt, max_tokens, model)
        else:
            raise LLMServiceError(f"Unknown LLM provider: {self.provider}")

        parsed = None
        try:
            parsed_json = self._extract_json(raw.raw_text)
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
