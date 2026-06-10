from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmbeddingGenerationResponse(BaseModel):
    case_id: int
    embedding_generated: bool
    embedding_updated_at: datetime | None
    vector_dimension: int
    processing_time_seconds: float
    storage_path: str


class EmbeddingBatchResponse(BaseModel):
    total_cases: int
    processed_cases: int
    failed_cases: int
    vector_dimension: int
    processing_time_seconds: float
    results: list[EmbeddingGenerationResponse]


class EmbeddingStatusResponse(BaseModel):
    total_cases: int
    embedded_cases: int
    pending_cases: int

    model_config = ConfigDict(from_attributes=True)