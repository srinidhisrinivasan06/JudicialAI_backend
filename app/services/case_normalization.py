from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from app.schemas.case import CaseType


def normalize_legal_sections(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        sections = value
    elif isinstance(value, tuple) or isinstance(value, set):
        sections = list(value)
    elif isinstance(value, str):
        sections = [part.strip() for part in value.replace("|", ",").replace(";", ",").split(",")]
    else:
        sections = [str(value).strip()]

    cleaned: list[str] = []
    for section in sections:
        section_text = str(section).strip()
        if section_text and section_text not in cleaned:
            cleaned.append(section_text)
    return cleaned


def coerce_case_type(value: Any, default_case_type: str = CaseType.CIVIL.value) -> str:
    if value is None:
        return default_case_type

    candidate = str(value).strip().lower()
    for case_type in CaseType:
        if candidate == case_type.value.lower():
            return case_type.value
    return default_case_type


def coerce_year(value: Any, default_year: int | None = None) -> int:
    current_year = datetime.utcnow().year
    fallback_year = default_year or current_year

    if value is None or value == "":
        return fallback_year

    try:
        year_value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Year must be a valid integer") from exc

    if year_value < 1000 or year_value > current_year + 1:
        raise ValueError(f"Year must be between 1000 and {current_year + 1}")
    return year_value


def clean_text(value: Any, default: str | None = None) -> str | None:
    if value is None:
        return default
    text_value = str(value).strip()
    if not text_value:
        return default
    return text_value


def normalize_import_record(
    raw_record: dict[str, Any],
    default_case_type: str = CaseType.CIVIL.value,
    default_year: int | None = None,
    default_case_status: str = "active",
) -> dict[str, Any]:
    title = clean_text(raw_record.get("title") or raw_record.get("case_title"))
    facts = clean_text(raw_record.get("facts"))
    judgment_text = clean_text(
        raw_record.get("judgment_text")
        or raw_record.get("judgment")
        or raw_record.get("sentence")
        or raw_record.get("summary"),
    )
    legal_sections = normalize_legal_sections(
        raw_record.get("legal_sections") or raw_record.get("section") or raw_record.get("sections")
    )

    if not title:
        raise ValueError("Title is required")
    if not facts:
        raise ValueError("Facts are required")
    if not judgment_text:
        raise ValueError("Judgment text or sentence is required")
    if not legal_sections:
        raise ValueError("At least one legal section is required")

    return {
        "title": title,
        "facts": facts,
        "judgment_text": judgment_text,
        "legal_sections": legal_sections,
        "sentence": clean_text(raw_record.get("sentence"), judgment_text),
        "court_name": clean_text(raw_record.get("court_name") or raw_record.get("court")),
        "judge_name": clean_text(raw_record.get("judge_name") or raw_record.get("judge")),
        "case_type": coerce_case_type(raw_record.get("case_type"), default_case_type),
        "year": coerce_year(raw_record.get("year"), default_year),
        "case_status": clean_text(raw_record.get("case_status"), default_case_status) or default_case_status,
    }
