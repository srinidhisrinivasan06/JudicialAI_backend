import re
from pathlib import Path
from typing import Any

from PyPDF2 import PdfReader

from app.core.logging_config import logger
from app.services.case_normalization import clean_text, normalize_legal_sections


SECTION_PATTERN = re.compile(
    r"\b(?:section|u/s|under section)\s+\d+[a-zA-Z0-9()\-/.,\s]*",
    re.IGNORECASE,
)


class PDFProcessor:
    @staticmethod
    def extract_text(file_path: str) -> str:
        reader = PdfReader(file_path)
        pages: list[str] = []
        for page in reader.pages:
            extracted = page.extract_text() or ""
            if extracted.strip():
                pages.append(extracted)
        return "\n".join(pages).strip()

    @staticmethod
    def extract_case_data(file_path: str) -> dict[str, Any]:
        text = PDFProcessor.extract_text(file_path)
        if not text:
            raise ValueError("No extractable text found in PDF")

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        title = lines[0] if lines else Path(file_path).stem
        facts = PDFProcessor._extract_block(text, ["facts", "facts of the case", "background"])
        judgment_text = PDFProcessor._extract_block(
            text,
            ["judgment", "order", "decision", "held"],
            fallback=text,
        )
        sections = normalize_legal_sections(SECTION_PATTERN.findall(text))

        court_name = PDFProcessor._find_court_name(lines)
        judge_name = PDFProcessor._find_judge_name(lines)
        sentence = PDFProcessor._extract_block(text, ["sentence", "punishment"], fallback=None)

        if not facts:
            facts = text[:4000]
        if not judgment_text:
            judgment_text = text

        logger.info("PDF processed successfully: %s", file_path)
        return {
            "title": clean_text(title) or Path(file_path).stem,
            "facts": clean_text(facts) or text,
            "judgment_text": clean_text(judgment_text) or text,
            "legal_sections": sections,
            "sentence": clean_text(sentence),
            "court_name": clean_text(court_name),
            "judge_name": clean_text(judge_name),
        }

    @staticmethod
    def _extract_block(text: str, start_keywords: list[str], fallback: str | None = "") -> str | None:
        lowered = text.lower()
        starts = [lowered.find(keyword.lower()) for keyword in start_keywords]
        start_positions = [position for position in starts if position >= 0]
        if not start_positions:
            return fallback

        start_index = min(start_positions)
        end_keywords = ["judgment", "order", "analysis", "held", "result", "conclusion", "decree"]
        end_index = len(text)
        for keyword in end_keywords:
            position = lowered.find(keyword.lower(), start_index + 1)
            if position > start_index and position < end_index:
                end_index = position

        block = text[start_index:end_index].strip()
        return block or fallback

    @staticmethod
    def _find_court_name(lines: list[str]) -> str | None:
        for line in lines[:20]:
            if "court" in line.lower() or "tribunal" in line.lower() or "commission" in line.lower():
                return line
        return None

    @staticmethod
    def _find_judge_name(lines: list[str]) -> str | None:
        for line in lines[:40]:
            if "judge" in line.lower() or "justice" in line.lower():
                return line
        return None
