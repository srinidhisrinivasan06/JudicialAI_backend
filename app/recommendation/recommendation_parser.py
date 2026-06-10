from __future__ import annotations

import json
import re
from typing import Any


REQUIRED_KEYS = {
    "case_type",
    "recommended_sections",
    "severity_level",
    "historical_outcomes",
    "recommended_punishment",
    "aggravating_factors",
    "mitigating_factors",
    "reasoning",
    "confidence_score",
    "key_influencing_factors",
    "disclaimer",
}


def parse_recommendation_response(raw_response: str) -> dict[str, Any]:
    cleaned = raw_response.strip()

    # Strip markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned invalid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("Gemini response must be a JSON object")

    missing = REQUIRED_KEYS - parsed.keys()
    if missing:
        raise ValueError(f"Gemini response missing required fields: {missing}")

    score = parsed.get("confidence_score")
    if not isinstance(score, (int, float)) or not (0 <= score <= 100):
        raise ValueError("confidence_score must be a number between 0 and 100")

    # Ensure disclaimer is always present
    parsed["disclaimer"] = "This recommendation is advisory only. Final judicial authority remains with the judge."

    return parsed
