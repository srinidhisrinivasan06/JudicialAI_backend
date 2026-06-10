from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.case import CaseRead


class PaginationMeta(BaseModel):
    total_records: int
    current_page: int
    total_pages: int
    page_size: int


class CaseListData(BaseModel):
    items: list[CaseRead]
    pagination: PaginationMeta


class CaseResponseEnvelope(BaseModel):
    success: bool = True
    message: str
    data: CaseRead


class CaseListResponseEnvelope(BaseModel):
    success: bool = True
    message: str
    data: CaseListData


class MessageResponse(BaseModel):
    success: bool = True
    message: str
    data: dict | None = None


class UploadResultData(BaseModel):
    saved_file_path: str
    imported_records: int
    errors: list[str] = Field(default_factory=list)


class UploadResultEnvelope(BaseModel):
    success: bool = True
    message: str
    data: UploadResultData
