from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CaseType(str, Enum):
    CRIMINAL = "Criminal"
    CIVIL = "Civil"
    CONSUMER = "Consumer"
    TAX = "Tax"
    PROPERTY = "Property"
    CONTRACT = "Contract"
    CYBER_CRIME = "Cyber Crime"


class CaseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    facts: str = Field(..., min_length=1)
    judgment_text: str = Field(..., min_length=1)
    legal_sections: list[str] = Field(..., min_length=1)
    sentence: Optional[str] = None
    court_name: Optional[str] = Field(default=None, max_length=255)
    judge_name: Optional[str] = Field(default=None, max_length=255)
    case_type: CaseType
    year: int
    case_status: str = Field(default="active", max_length=50)

    @field_validator("title", "facts", "judgment_text", "case_status", mode="before")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value

    @field_validator("legal_sections")
    @classmethod
    def validate_legal_sections(cls, value: list[str]) -> list[str]:
        cleaned = [section.strip() for section in value if isinstance(section, str) and section.strip()]
        if not cleaned:
            raise ValueError("At least one legal section is required")
        return cleaned

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int) -> int:
        current_year = datetime.utcnow().year
        if value < 1000 or value > current_year + 1:
            raise ValueError(f"Year must be between 1000 and {current_year + 1}")
        return value


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    facts: Optional[str] = None
    judgment_text: Optional[str] = None
    legal_sections: Optional[list[str]] = None
    sentence: Optional[str] = None
    court_name: Optional[str] = Field(default=None, max_length=255)
    judge_name: Optional[str] = Field(default=None, max_length=255)
    case_type: Optional[CaseType] = None
    year: Optional[int] = None
    case_status: Optional[str] = Field(default=None, max_length=50)

    @field_validator("title", "facts", "judgment_text", "case_status", mode="before")
    @classmethod
    def validate_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if isinstance(value, str):
            value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value

    @field_validator("legal_sections")
    @classmethod
    def validate_optional_legal_sections(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        cleaned = [section.strip() for section in value if isinstance(section, str) and section.strip()]
        if not cleaned:
            raise ValueError("At least one legal section is required")
        return cleaned

    @field_validator("year")
    @classmethod
    def validate_optional_year(cls, value: int | None) -> int | None:
        if value is None:
            return value
        current_year = datetime.utcnow().year
        if value < 1000 or value > current_year + 1:
            raise ValueError(f"Year must be between 1000 and {current_year + 1}")
        return value

    model_config = ConfigDict(extra="ignore")


class CaseRead(CaseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
