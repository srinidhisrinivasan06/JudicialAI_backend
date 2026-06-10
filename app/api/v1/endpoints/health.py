from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health", response_model=dict)
def get_health():
    """
    Returns API operational status, service name, and version.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
