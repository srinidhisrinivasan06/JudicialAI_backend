from __future__ import annotations

from typing import Any


def build_recommendation_prompt(case_text: str, similar_cases: list[dict[str, Any]]) -> str:
    precedents_block = ""
    for i, case in enumerate(similar_cases, start=1):
        precedents_block += (
            f"\nPrecedent {i}:\n"
            f"  Title: {case.get('title', 'N/A')}\n"
            f"  Case Type: {case.get('case_type', 'N/A')}\n"
            f"  Legal Sections: {', '.join(case.get('legal_sections', []))}\n"
            f"  Facts: {case.get('facts', 'N/A')[:500]}\n"
            f"  Judgment: {case.get('judgment_text', 'N/A')[:500]}\n"
            f"  Sentence: {case.get('sentence', 'N/A')}\n"
            f"  Year: {case.get('year', 'N/A')}\n"
            f"  Similarity Score: {case.get('similarity_score', 'N/A')}\n"
        )

    return f"""You are an expert Indian legal AI assistant supporting judicial decision-making.

Analyze the following current case and the retrieved legal precedents.
Return ONLY a valid JSON object with no markdown, no code fences, no explanation outside JSON.

Current Case:
{case_text}

Retrieved Precedents:
{precedents_block if precedents_block else "No similar cases found."}

Return this exact JSON structure:
{{
  "case_type": "<string>",
  "recommended_sections": ["<IPC/Act Section>"],
  "severity_level": "<Low | Medium | High | Critical>",
  "historical_outcomes": {{
    "fine": "<percentage>",
    "probation": "<percentage>",
    "imprisonment": "<percentage>"
  }},
  "recommended_punishment": {{
    "fine_range": "<string or null>",
    "probation_period": "<string or null>",
    "imprisonment_range": "<string or null>"
  }},
  "aggravating_factors": ["<string>"],
  "mitigating_factors": ["<string>"],
  "reasoning": "<detailed legal reasoning>",
  "confidence_score": <integer 0-100>,
  "key_influencing_factors": ["<string>"],
  "disclaimer": "This recommendation is advisory only. Final judicial authority remains with the judge."
}}"""
