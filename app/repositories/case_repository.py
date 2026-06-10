from typing import Any, Iterable

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.case import Case


class CaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_case(self, case_data: dict[str, Any]) -> Case:
        case = Case(**case_data)
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def bulk_create_cases(self, cases_data: Iterable[dict[str, Any]]) -> list[Case]:
        cases = [Case(**case_data) for case_data in cases_data]
        self.db.add_all(cases)
        self.db.commit()
        for case in cases:
            self.db.refresh(case)
        return cases

    def get_case(self, case_id: int) -> Case | None:
        return self.db.get(Case, case_id)

    def list_cases(self, page: int, page_size: int) -> tuple[list[Case], int]:
        query = select(Case).order_by(Case.created_at.desc())
        total_records = self.db.execute(select(func.count()).select_from(Case)).scalar_one()
        cases = self.db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()
        return cases, total_records

    def update_case(self, case: Case, update_data: dict[str, Any]) -> Case:
        for field_name, field_value in update_data.items():
            setattr(case, field_name, field_value)
        case.embedding_generated = False
        case.embedding_updated_at = None
        self.db.commit()
        self.db.refresh(case)
        return case

    def delete_case(self, case: Case) -> None:
        self.db.delete(case)
        self.db.commit()

    def search_cases(
        self,
        page: int,
        page_size: int,
        court_name: str | None = None,
        case_type: str | None = None,
        year: int | None = None,
        legal_section: str | None = None,
        keywords: str | None = None,
    ) -> tuple[list[Case], int]:
        filters = []

        if court_name:
            filters.append(Case.court_name.ilike(f"%{court_name}%"))
        if case_type:
            filters.append(Case.case_type.ilike(f"%{case_type}%"))
        if year:
            filters.append(Case.year == year)
        if legal_section:
            filters.append(Case.legal_sections.contains([legal_section]))
        if keywords:
            keyword_filter = or_(
                Case.title.ilike(f"%{keywords}%"),
                Case.facts.ilike(f"%{keywords}%"),
                Case.judgment_text.ilike(f"%{keywords}%"),
                Case.court_name.ilike(f"%{keywords}%"),
                Case.judge_name.ilike(f"%{keywords}%"),
                Case.sentence.ilike(f"%{keywords}%"),
            )
            filters.append(keyword_filter)

        where_clause = and_(*filters) if filters else None

        base_query = select(Case)
        count_query = select(func.count()).select_from(Case)

        if where_clause is not None:
            base_query = base_query.where(where_clause)
            count_query = count_query.where(where_clause)

        total_records = self.db.execute(count_query).scalar_one()
        cases = self.db.execute(
            base_query.order_by(Case.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        ).scalars().all()
        return cases, total_records
