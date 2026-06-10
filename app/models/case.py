from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database.base import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    facts = Column(Text, nullable=False)
    judgment_text = Column(Text, nullable=False)
    legal_sections = Column(JSONB, nullable=False, default=list)
    sentence = Column(Text, nullable=True)
    court_name = Column(String(255), nullable=True, index=True)
    judge_name = Column(String(255), nullable=True, index=True)
    case_type = Column(String(50), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    case_status = Column(String(50), nullable=False, default="active", index=True)
    embedding_generated = Column(Boolean, nullable=False, default=False, index=True)
    embedding_updated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
