from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.schemas.embedding import EmbeddingBatchResponse, EmbeddingGenerationResponse, EmbeddingStatusResponse
from app.services.embedding_service import EmbeddingService

router = APIRouter(prefix="/embeddings")


def get_embedding_service(db: Session = Depends(get_db)) -> EmbeddingService:
    return EmbeddingService(db)


@router.post("/generate/{case_id}", response_model=EmbeddingGenerationResponse, dependencies=[Depends(get_current_user)])
def generate_case_embedding(case_id: int, service: EmbeddingService = Depends(get_embedding_service)):
    result = service.update_embedding(case_id)
    return EmbeddingGenerationResponse(**result.__dict__)


@router.post("/generate-all", response_model=EmbeddingBatchResponse, dependencies=[Depends(get_current_user)])
def generate_all_embeddings(service: EmbeddingService = Depends(get_embedding_service)):
    results, total_cases, failed_cases, processing_time = service.generate_all_embeddings()
    payload = [EmbeddingGenerationResponse(**result.__dict__) for result in results]
    return EmbeddingBatchResponse(
        total_cases=total_cases,
        processed_cases=len(payload),
        failed_cases=failed_cases,
        vector_dimension=payload[0].vector_dimension if payload else 0,
        processing_time_seconds=processing_time,
        results=payload,
    )


@router.get("/status", response_model=EmbeddingStatusResponse)
def embedding_status(service: EmbeddingService = Depends(get_embedding_service)):
    return EmbeddingStatusResponse(**service.get_status())