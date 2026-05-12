from __future__ import annotations

import json
import re
from typing import Any, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def extract_json_from_text(text: str) -> Any:
    """Extract and parse a JSON value from a raw text blob.

    Strategy:
    1. Try direct json.loads(text)
    2. Locate the first balanced JSON object/array in the text
    3. Parse the candidate and return it

    Raises:
        ValueError: if no valid JSON can be extracted.
    """
    try:
        return json.loads(text)
    except Exception:
        pass

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
                    # Keep scanning in case there is another valid JSON fragment later.
                    pass

    raise ValueError("Could not extract valid JSON from text")


def validate_json_with_model(data: Any, model: Type[T]) -> T:
    """Validate a parsed JSON value against a Pydantic model.

    Works with Pydantic v2 `model_validate` and falls back to v1 `parse_obj`.
    """
    if hasattr(model, "model_validate"):
        return model.model_validate(data)  # type: ignore[call-arg]
    return model.parse_obj(data)  # type: ignore[attr-defined]


def parse_and_validate_json(text: str, model: Type[T]) -> T:
    """Extract JSON from raw text and validate it against a Pydantic model."""
    payload = extract_json_from_text(text)
    return validate_json_with_model(payload, model)
