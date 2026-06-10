from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.case import Case


class EmbeddingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_case(self, case_id: int) -> Case | None:
        return self.db.get(Case, case_id)

    def list_cases(self, only_pending: bool = False) -> list[Case]:
        query = select(Case).order_by(Case.id.asc())
        if only_pending:
            query = query.where(Case.embedding_generated.is_(False))
        return self.db.execute(query).scalars().all()

    def count_status(self) -> dict[str, int]:
        total_cases = self.db.execute(select(func.count()).select_from(Case)).scalar_one()
        embedded_cases = self.db.execute(
            select(func.count()).select_from(Case).where(Case.embedding_generated.is_(True))
        ).scalar_one()
        return {
            "total_cases": total_cases,
            "embedded_cases": embedded_cases,
            "pending_cases": total_cases - embedded_cases,
        }

    def mark_embedding_generated(self, case: Case) -> Case:
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case