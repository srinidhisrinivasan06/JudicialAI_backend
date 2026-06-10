import time
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.logging_config import logger
from app.database.base import Base
from app.database.session import engine
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed for strict production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Intercept and log HTTP requests & responses
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Request details
    client_host = request.client.host if request.client else "unknown"
    method = request.method
    url = str(request.url)
    
    logger.info(f"API Request: {method} {url} from {client_host}")
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"API Response: {method} {url} - Status: {response.status_code} - Duration: {process_time:.2f}ms"
        )
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"API Failure: {method} {url} - Exception: {str(e)} - Duration: {process_time:.2f}ms",
            exc_info=True
        )
        raise e

# Global unhandled Exception Interceptor
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception captured on {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator."},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation failed for %s: %s", request.url, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "message": "Validation failed", "data": exc.errors()},
    )


@app.on_event("startup")
def create_tables() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured at startup")

# Attach API endpoints router
app.include_router(api_router, prefix=settings.API_V1_STR)
