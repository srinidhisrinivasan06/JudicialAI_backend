from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.recommendation.recommendation_engine import RecommendationEngine
from app.repositories.case_repository import CaseRepository
from app.schemas.case import CaseRead
from app.services.embedding_service import EmbeddingService

TOP_K = 5
VECTOR_STORE_DIR = Path(__file__).resolve().parents[1] / "vector_store" / "embeddings"


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CaseRepository(db)
        self.embedding_service = EmbeddingService(db)
        self.engine = RecommendationEngine()

    def analyze_case(self, case_text: str) -> dict[str, Any]:
        if not case_text or not case_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Case description cannot be empty",
            )

        start_time = time.perf_counter()
        logger.info("Recommendation request received | Case text length: %d", len(case_text))

        query_embedding = self._get_query_embedding(case_text)
        similar_cases = self._retrieve_similar_cases(query_embedding)

        logger.info("Retrieved %d similar cases for recommendation", len(similar_cases))

        recommendation = self.generate_recommendation(case_text, similar_cases)

        elapsed = time.perf_counter() - start_time
        logger.info("Recommendation completed in %.2f seconds", elapsed)

        return {
            "case_analysis": {"case_text": case_text, "processing_time_seconds": round(elapsed, 2)},
            "similar_cases": similar_cases,
            "recommendation": recommendation,
        }

    def generate_recommendation(
        self, case_text: str, similar_cases: list[dict[str, Any]]
    ) -> dict[str, Any]:
        return self.engine.generate_recommendation(case_text, similar_cases)

    def _get_query_embedding(self, case_text: str) -> list[float]:
        try:
            return self.embedding_service.generate_embedding(case_text)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Failed to generate query embedding")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate query embedding",
            ) from exc

    def _retrieve_similar_cases(self, query_embedding: list[float]) -> list[dict[str, Any]]:
        try:
            import faiss
            import numpy as np
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="FAISS or NumPy dependency is not installed",
            ) from exc

        embedding_files = sorted(VECTOR_STORE_DIR.glob("case_*.npy"))
        if not embedding_files:
            logger.warning("No embeddings found in vector store — returning empty similar cases")
            return []

        case_ids: list[int] = []
        vectors: list[Any] = []

        for f in embedding_files:
            try:
                case_id = int(f.stem.replace("case_", ""))
                vec = np.load(f).astype("float32")
                case_ids.append(case_id)
                vectors.append(vec)
            except Exception:  # noqa: BLE001
                continue

        if not vectors:
            return []

        matrix = np.vstack(vectors).astype("float32")
        dimension = matrix.shape[1]

        index = faiss.IndexFlatIP(dimension)
        index.add(matrix)

        query_vector = np.array(query_embedding, dtype="float32").reshape(1, -1)
        k = min(TOP_K, len(case_ids))
        scores, indices = index.search(query_vector, k)

        results: list[dict[str, Any]] = []
        for rank, idx in enumerate(indices[0]):
            if idx < 0:
                continue
            case_id = case_ids[idx]
            case = self.repository.get_case(case_id)
            if not case:
                continue
            case_data = CaseRead.model_validate(case).model_dump()
            case_data["similarity_score"] = round(float(scores[0][rank]), 4)
            # Convert datetime fields to string for JSON serialization
            case_data["created_at"] = str(case_data["created_at"])
            case_data["updated_at"] = str(case_data["updated_at"])
            results.append(case_data)

        return results
