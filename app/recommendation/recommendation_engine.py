from __future__ import annotations

import time
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.logging_config import logger
from app.recommendation.recommendation_parser import parse_recommendation_response
from app.recommendation.recommendation_prompt import build_recommendation_prompt


class RecommendationEngine:
    MODEL_NAME = "gemini-2.5-pro"

    def _get_client(self):
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="google-generativeai dependency is not installed",
            ) from exc

        if not settings.GEMINI_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GEMINI_API_KEY is not configured",
            )

        genai.configure(api_key=settings.GEMINI_API_KEY)
        return genai.GenerativeModel(self.MODEL_NAME)

    def build_prompt(self, case_text: str, similar_cases: list[dict[str, Any]]) -> str:
        return build_recommendation_prompt(case_text, similar_cases)

    def parse_response(self, raw_response: str) -> dict[str, Any]:
        return parse_recommendation_response(raw_response)

    def generate_recommendation(
        self, case_text: str, similar_cases: list[dict[str, Any]]
    ) -> dict[str, Any]:
        logger.info("Building recommendation prompt | Similar cases: %d", len(similar_cases))
        prompt = self.build_prompt(case_text, similar_cases)

        model = self._get_client()
        start_time = time.perf_counter()

        try:
            logger.info("Sending request to Gemini model: %s", self.MODEL_NAME)
            response = model.generate_content(prompt)
            raw_text = response.text
        except Exception as exc:
            logger.exception("Gemini API call failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gemini API request failed",
            ) from exc

        elapsed = time.perf_counter() - start_time
        logger.info("Gemini response received in %.2f seconds", elapsed)

        try:
            parsed = self.parse_response(raw_text)
        except ValueError as exc:
            logger.error("Failed to parse Gemini response: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse AI response: {exc}",
            ) from exc

        logger.info(
            "Recommendation generated | Confidence: %s | Severity: %s",
            parsed.get("confidence_score"),
            parsed.get("severity_level"),
        )
        return parsed
