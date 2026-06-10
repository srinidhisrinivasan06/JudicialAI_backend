import csv
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.services.case_normalization import normalize_import_record
from app.services.upload_storage import save_upload_file


class CSVImportService:
    def __init__(self, db: Session):
        self.db = db

    async def import_csv_file(self, upload_file, default_case_type: str, default_year: int) -> dict[str, Any]:
        saved_path = await save_upload_file(upload_file, "csv")
        try:
            records, errors = self._read_and_validate_csv(saved_path, default_case_type, default_year)
            imported = self._store_records(records)

            logger.info("CSV import completed: %s records stored from %s", len(imported), saved_path)
            return {
                "saved_file_path": saved_path,
                "imported_records": len(imported),
                "errors": errors,
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("CSV import failed for %s", saved_path)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to process CSV upload") from exc

    def _read_and_validate_csv(
        self,
        file_path: str,
        default_case_type: str,
        default_year: int,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        valid_records: list[dict[str, Any]] = []
        errors: list[str] = []

        with Path(file_path).open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for index, row in enumerate(reader, start=2):
                try:
                    normalized = normalize_import_record(
                        row,
                        default_case_type=default_case_type,
                        default_year=default_year,
                    )
                    valid_records.append(normalized)
                except ValueError as exc:
                    errors.append(f"Row {index}: {exc}")
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"Row {index}: Unexpected error - {exc}")

        return valid_records, errors

    def _store_records(self, records: list[dict[str, Any]]) -> list[Any]:
        from app.repositories.case_repository import CaseRepository

        repository = CaseRepository(self.db)
        if not records:
            return []
        return repository.bulk_create_cases(records)
