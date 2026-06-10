from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.recommendation.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations")


class RecommendationRequest(BaseModel):
    case_text: str = Field(..., min_length=10, description="Description of the current case")


def get_recommendation_service(db: Session = Depends(get_db)) -> RecommendationService:
    return RecommendationService(db)


@router.post(
    "/analyze",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
def analyze_case(
    payload: RecommendationRequest,
    service: RecommendationService = Depends(get_recommendation_service),
):
    return service.analyze_case(payload.case_text)
