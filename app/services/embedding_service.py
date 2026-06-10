from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.models.case import Case
from app.repositories.embedding_repository import EmbeddingRepository


@dataclass(slots=True)
class EmbeddingResult:
    case_id: int
    embedding_generated: bool
    embedding_updated_at: Any
    vector_dimension: int
    processing_time_seconds: float
    storage_path: str


class EmbeddingService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = EmbeddingRepository(db)
        self._model = None
        self._vector_store_dir = Path(__file__).resolve().parents[1] / "vector_store" / "embeddings"
        self._vector_store_dir.mkdir(parents=True, exist_ok=True)

    def _load_model(self):
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Embedding model dependency is not installed",
            ) from exc

        try:
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            return self._model
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to load embedding model")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to load embedding model",
            ) from exc

    def _normalize_sections(self, legal_sections: list[str] | None) -> str:
        cleaned = [section.strip() for section in (legal_sections or []) if section and section.strip()]
        return ", ".join(cleaned)

    def _build_case_document(self, case: Case) -> str:
        parts = [
            f"Title: {case.title.strip() if case.title else ''}",
            f"Facts: {case.facts.strip() if case.facts else ''}",
            f"Judgment: {case.judgment_text.strip() if case.judgment_text else ''}",
            f"Sections: {self._normalize_sections(case.legal_sections)}",
        ]
        document = "\n".join(parts).strip()
        if not document or document.replace("\n", "").replace(":", "").strip() == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Case {case.id} does not contain enough text for embedding generation",
            )
        return document

    def generate_embedding(self, text: str) -> list[float]:
        cleaned_text = text.strip()
        if not cleaned_text:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Embedding text cannot be empty")

        model = self._load_model()
        try:
            vector = model.encode(cleaned_text, convert_to_numpy=True, normalize_embeddings=True)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Embedding generation failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate embedding",
            ) from exc

        return vector.tolist()

    def generate_case_embedding(self, case: Case) -> EmbeddingResult:
        start_time = time.perf_counter()
        document = self._build_case_document(case)
        embedding = self.generate_embedding(document)
        storage_path = self._save_embedding(case.id, embedding)
        case.embedding_generated = True
        case.embedding_updated_at = self._utc_now()
        self.repository.mark_embedding_generated(case)
        processing_time = time.perf_counter() - start_time
        logger.info(
            "Generated embedding for Case %s | Vector Dimension: %s | Processing Time: %.2f sec",
            case.id,
            len(embedding),
            processing_time,
        )
        return EmbeddingResult(
            case_id=case.id,
            embedding_generated=True,
            embedding_updated_at=case.embedding_updated_at,
            vector_dimension=len(embedding),
            processing_time_seconds=processing_time,
            storage_path=storage_path,
        )

    def generate_batch_embeddings(self, cases: list[Case]) -> tuple[list[EmbeddingResult], int, int, float]:
        start_time = time.perf_counter()
        results: list[EmbeddingResult] = []
        failed_cases = 0

        for case in cases:
            try:
                results.append(self.generate_case_embedding(case))
            except HTTPException:
                failed_cases += 1
            except Exception as exc:  # noqa: BLE001
                failed_cases += 1
                logger.exception("Unexpected failure while generating embedding for case %s", case.id)
                logger.error("Embedding generation error: %s", exc)

        processing_time = time.perf_counter() - start_time
        return results, len(cases), failed_cases, processing_time

    def update_embedding(self, case_id: int) -> EmbeddingResult:
        case = self.repository.get_case(case_id)
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        return self.generate_case_embedding(case)

    def generate_all_embeddings(self) -> tuple[list[EmbeddingResult], int, int, float]:
        cases = self.repository.list_cases(only_pending=True)
        return self.generate_batch_embeddings(cases)

    def get_status(self) -> dict[str, int]:
        return self.repository.count_status()

    def _save_embedding(self, case_id: int, embedding: list[float]) -> str:
        try:
            import numpy as np
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="NumPy dependency is not installed",
            ) from exc

        file_path = self._vector_store_dir / f"case_{case_id}.npy"
        np.save(file_path, np.array(embedding, dtype="float32"))
        return str(file_path)

    def _utc_now(self):
        from datetime import datetime, timezone

        return datetime.now(timezone.utc)