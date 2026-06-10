from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.repositories.case_repository import CaseRepository
from app.schemas.case import CaseCreate, CaseRead, CaseUpdate
from app.services.case_normalization import coerce_case_type, coerce_year
from app.services.csv_import_service import CSVImportService
from app.services.json_import_service import JSONImportService
from app.services.pdf_processor import PDFProcessor


class CaseService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CaseRepository(db)

    def create_case(self, payload: CaseCreate) -> CaseRead:
        logger.info("Creating legal case: %s", payload.title)
        created_case = self.repository.create_case(payload.model_dump())
        return CaseRead.model_validate(created_case)

    def get_case(self, case_id: int) -> CaseRead:
        case = self.repository.get_case(case_id)
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        return CaseRead.model_validate(case)

    def list_cases(self, page: int, page_size: int) -> dict[str, Any]:
        cases, total_records = self.repository.list_cases(page, page_size)
        return self._build_paginated_response(cases, total_records, page, page_size)

    def update_case(self, case_id: int, payload: CaseUpdate) -> CaseRead:
        case = self.repository.get_case(case_id)
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

        update_data = payload.model_dump(exclude_unset=True)
        logger.info("Updating legal case %s", case_id)
        updated_case = self.repository.update_case(case, update_data)
        return CaseRead.model_validate(updated_case)

    def delete_case(self, case_id: int) -> None:
        case = self.repository.get_case(case_id)
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

        logger.info("Deleting legal case %s", case_id)
        self.repository.delete_case(case)

    def search_cases(
        self,
        page: int,
        page_size: int,
        court_name: str | None = None,
        case_type: str | None = None,
        year: int | None = None,
        legal_section: str | None = None,
        keywords: str | None = None,
    ) -> dict[str, Any]:
        cases, total_records = self.repository.search_cases(
            page=page,
            page_size=page_size,
            court_name=court_name,
            case_type=case_type,
            year=year,
            legal_section=legal_section,
            keywords=keywords,
        )
        logger.info(
            "Search executed with filters court_name=%s case_type=%s year=%s legal_section=%s keywords=%s",
            court_name,
            case_type,
            year,
            legal_section,
            keywords,
        )
        return self._build_paginated_response(cases, total_records, page, page_size)

    async def process_pdf_upload(self, upload_file: UploadFile, default_case_type: str, default_year: int) -> dict[str, Any]:
        if not upload_file.filename or not upload_file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PDF file")

        from app.services.upload_storage import save_upload_file

        saved_path = await save_upload_file(upload_file, "pdfs")

        try:
            extracted_data = PDFProcessor.extract_case_data(saved_path)
            normalized = self._normalize_import_record(extracted_data, default_case_type, default_year)
            self.repository.create_case(normalized)
            logger.info("PDF import completed: %s", saved_path)
            return {
                "saved_file_path": saved_path,
                "imported_records": 1,
                "errors": [],
            }
        except ValueError as exc:
            logger.warning("PDF upload validation failed for %s: %s", saved_path, exc)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("PDF import failed for %s", saved_path)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to process PDF upload") from exc

    async def process_csv_upload(self, upload_file: UploadFile, default_case_type: str, default_year: int) -> dict[str, Any]:
        if not upload_file.filename or not upload_file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CSV file")
        service = CSVImportService(self.db)
        return await service.import_csv_file(upload_file, default_case_type, default_year)

    async def process_json_upload(self, upload_file: UploadFile, default_case_type: str, default_year: int) -> dict[str, Any]:
        if not upload_file.filename or not upload_file.filename.lower().endswith(".json"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON file")
        service = JSONImportService(self.db)
        return await service.import_json_file(upload_file, default_case_type, default_year)

    def _normalize_import_record(self, raw_record: dict[str, Any], default_case_type: str, default_year: int) -> dict[str, Any]:
        from app.services.case_normalization import normalize_import_record

        return normalize_import_record(raw_record, default_case_type=default_case_type, default_year=default_year)

    def _build_paginated_response(self, cases: list[Any], total_records: int, page: int, page_size: int) -> dict[str, Any]:
        total_pages = max(1, (total_records + page_size - 1) // page_size) if total_records else 0
        items = [CaseRead.model_validate(case) for case in cases]
        return {
            "items": items,
            "pagination": {
                "total_records": total_records,
                "current_page": page,
                "total_pages": total_pages,
                "page_size": page_size,
            },
        }
