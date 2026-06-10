from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.logging_config import logger
from app.database.session import get_db
from app.schemas.case import CaseCreate, CaseRead, CaseUpdate, CaseType
from app.schemas.common import (
    CaseListData,
    CaseListResponseEnvelope,
    CaseResponseEnvelope,
    MessageResponse,
    PaginationMeta,
    UploadResultData,
    UploadResultEnvelope,
)
from app.services.case_service import CaseService

router = APIRouter(prefix="/cases")


def get_case_service(db: Session = Depends(get_db)) -> CaseService:
    return CaseService(db)


@router.post("", response_model=CaseResponseEnvelope, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
def create_case(payload: CaseCreate, service: CaseService = Depends(get_case_service)):
    case = service.create_case(payload)
    return CaseResponseEnvelope(message="Case created successfully", data=case)


@router.get("", response_model=CaseListResponseEnvelope)
def list_cases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    service: CaseService = Depends(get_case_service),
):
    result = service.list_cases(page=page, page_size=page_size)
    return CaseListResponseEnvelope(
        message="Cases retrieved successfully",
        data=CaseListData(items=result["items"], pagination=PaginationMeta(**result["pagination"])),
    )


@router.get("/search", response_model=CaseListResponseEnvelope)
def search_cases(
    court_name: str | None = Query(default=None),
    case_type: CaseType | None = Query(default=None),
    year: int | None = Query(default=None, ge=1000),
    legal_section: str | None = Query(default=None),
    keywords: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    service: CaseService = Depends(get_case_service),
):
    result = service.search_cases(
        page=page,
        page_size=page_size,
        court_name=court_name,
        case_type=case_type.value if case_type else None,
        year=year,
        legal_section=legal_section,
        keywords=keywords,
    )
    return CaseListResponseEnvelope(
        message="Search completed successfully",
        data=CaseListData(items=result["items"], pagination=PaginationMeta(**result["pagination"])),
    )


@router.get("/{case_id}", response_model=CaseResponseEnvelope)
def get_case(case_id: int, service: CaseService = Depends(get_case_service)):
    case = service.get_case(case_id)
    return CaseResponseEnvelope(message="Case retrieved successfully", data=case)


@router.put("/{case_id}", response_model=CaseResponseEnvelope, dependencies=[Depends(get_current_user)])
def update_case(case_id: int, payload: CaseUpdate, service: CaseService = Depends(get_case_service)):
    case = service.update_case(case_id, payload)
    return CaseResponseEnvelope(message="Case updated successfully", data=case)


@router.delete("/{case_id}", response_model=MessageResponse, dependencies=[Depends(get_current_user)])
def delete_case(case_id: int, service: CaseService = Depends(get_case_service)):
    service.delete_case(case_id)
    return MessageResponse(message="Case deleted successfully")


@router.post("/upload/pdf", response_model=UploadResultEnvelope, dependencies=[Depends(get_current_user)])
async def upload_pdf(
    file: UploadFile = File(...),
    service: CaseService = Depends(get_case_service),
):
    default_year = datetime.utcnow().year
    result = await service.process_pdf_upload(file, default_case_type=CaseType.CIVIL.value, default_year=default_year)
    return UploadResultEnvelope(
        message="PDF processed successfully",
        data=UploadResultData(
            saved_file_path=result["saved_file_path"],
            imported_records=result["imported_records"],
            errors=result.get("errors", []),
        ),
    )


@router.post("/upload/csv", response_model=UploadResultEnvelope, dependencies=[Depends(get_current_user)])
async def upload_csv(
    file: UploadFile = File(...),
    service: CaseService = Depends(get_case_service),
):
    default_year = datetime.utcnow().year
    result = await service.process_csv_upload(file, default_case_type=CaseType.CIVIL.value, default_year=default_year)
    return UploadResultEnvelope(
        message="CSV import completed successfully",
        data=UploadResultData(
            saved_file_path=result["saved_file_path"],
            imported_records=result["imported_records"],
            errors=result.get("errors", []),
        ),
    )


@router.post("/upload/json", response_model=UploadResultEnvelope, dependencies=[Depends(get_current_user)])
async def upload_json(
    file: UploadFile = File(...),
    service: CaseService = Depends(get_case_service),
):
    default_year = datetime.utcnow().year
    result = await service.process_json_upload(file, default_case_type=CaseType.CIVIL.value, default_year=default_year)
    return UploadResultEnvelope(
        message="JSON import completed successfully",
        data=UploadResultData(
            saved_file_path=result["saved_file_path"],
            imported_records=result["imported_records"],
            errors=result.get("errors", []),
        ),
    )
