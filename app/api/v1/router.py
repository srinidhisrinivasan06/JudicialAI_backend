from fastapi import APIRouter
from app.api.v1.endpoints import cases
from app.api.v1.endpoints import embeddings
from app.api.v1.endpoints import health

api_router = APIRouter()

# Register endpoint sub-routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(cases.router, tags=["cases"])
api_router.include_router(embeddings.router, tags=["embeddings"])
