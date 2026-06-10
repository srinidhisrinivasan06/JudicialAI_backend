import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.services.case_normalization import normalize_import_record
from app.services.upload_storage import save_upload_file


class JSONImportService:
    def __init__(self, db: Session):
        self.db = db

    async def import_json_file(self, upload_file, default_case_type: str, default_year: int) -> dict[str, Any]:
        saved_path = await save_upload_file(upload_file, "json")
        try:
            records, errors = self._read_and_validate_json(saved_path, default_case_type, default_year)
            stored_records = self._store_records(records)

            logger.info("JSON import completed: %s records stored from %s", len(stored_records), saved_path)
            return {
                "saved_file_path": saved_path,
                "imported_records": len(stored_records),
                "errors": errors,
            }
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("JSON import failed for %s", saved_path)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to process JSON upload") from exc

    def _read_and_validate_json(
        self,
        file_path: str,
        default_case_type: str,
        default_year: int,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        errors: list[str] = []
        valid_records: list[dict[str, Any]] = []

        with open(file_path, "r", encoding="utf-8") as json_file:
            payload = json.load(json_file)

        raw_records = payload.get("cases") if isinstance(payload, dict) and "cases" in payload else payload
        if isinstance(raw_records, dict):
            raw_records = [raw_records]

        if not isinstance(raw_records, list):
            raise ValueError("JSON upload must contain an object or a list of case records")

        for index, raw_record in enumerate(raw_records, start=1):
            try:
                if not isinstance(raw_record, dict):
                    raise ValueError("Each JSON case record must be an object")
                normalized = normalize_import_record(
                    raw_record,
                    default_case_type=default_case_type,
                    default_year=default_year,
                )
                valid_records.append(normalized)
            except ValueError as exc:
                errors.append(f"Record {index}: {exc}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Record {index}: Unexpected error - {exc}")

        return valid_records, errors

    def _store_records(self, records: list[dict[str, Any]]) -> list[Any]:
        from app.repositories.case_repository import CaseRepository

        repository = CaseRepository(self.db)
        if not records:
            return []
        return repository.bulk_create_cases(records)
