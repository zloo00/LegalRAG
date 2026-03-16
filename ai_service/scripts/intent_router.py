"""Intent routing for the LegalRAG assistant.

This module classifies user queries into broad intent categories so that
we can apply different handling strategies (e.g., bypass retrieval for
social small talk, use encyclopedic prompts for general questions, or
run a full case-specific RAG + "detective" analysis).

The classification is intentionally light-weight and heuristic.
"""

import re
from enum import Enum, auto
from typing import Optional


class Intent(Enum):
    SOCIAL = auto()
    GENERAL_LEGAL = auto()
    CASE_SPECIFIC = auto()


# Tokens that clearly indicate a conversational intent rather than a legal query.
_SOCIAL_PATTERNS = [
    r"\bпривет\b",
    r"\bздравствуйте\b",
    r"\bздра(в)?ствуйте\b",
    r"\bкак дела\b",
    r"\bкак жизнь\b",
    r"\bчто нового\b",
    r"\bты кто\b",
    r"\bкто ты\b",
    r"\bспасибо\b",
    r"\bблагодарю\b",
    r"\bдо свидания\b",
    r"\bпока\b",
    r"\bхорошего дня\b",
]


# Patterns that are typical for general legal questions (encyclopedic).
_GENERAL_PATTERNS = [
    r"\bчто такое\b",
    r"\bкакие (?:бывают|есть)\b",
    r"\bобъясни\b",
    r"\bпоясни\b",
    r"\bв чем разница\b",
    r"\bкуда обращаться\b",
    r"\bкак (?:работает|действует)\b",
    r"\bосновы\b",
    r"\bтермины\b",
]


# Words that indicate a personal or concrete case (case-specific).
_CASE_KEYWORDS = [
    r"\bя\b",
    r"\bменя\b",
    r"\bмне\b",
    r"\bмой\b",
    r"\bнаши\b",
    r"\bнам\b",
    r"\bсосед\b",
    r"\bработодател\b",
    r"\bколлег\b",
    r"\bвзыскан\b",
    r"\bштраф\b",
    r"\bзаплатить\b",
    r"\bне плат[и]т\b",
    r"\bнарушил\b",
    r"\bнарушение\b",
    r"\bдоговор\b",
    r"\bиск\b",
    r"\bпотерял\b",
    r"\bтерял\b",
    r"\bжалу\b",
]


def _matches_any(patterns: list[str], text: str) -> bool:
    for p in patterns:
        if re.search(p, text, flags=re.IGNORECASE):
            return True
    return False


def classify_intent(query: Optional[str]) -> Intent:
    """Classify a user query into one of the supported intent categories.

    Returns:
        Intent.SOCIAL       - simple greeting / small talk
        Intent.GENERAL_LEGAL - general informational legal question
        Intent.CASE_SPECIFIC - concrete case / problem requiring contextual analysis
    """
    if not query or not query.strip():
        return Intent.SOCIAL

    q = query.strip().lower()

    # Prefer social classification if it clearly matches.
    if _matches_any(_SOCIAL_PATTERNS, q):
        return Intent.SOCIAL

    # If it looks like a general encyclopedia-style question, treat as general.
    if _matches_any(_GENERAL_PATTERNS, q) and not _matches_any(_CASE_KEYWORDS, q):
        return Intent.GENERAL_LEGAL

    # Default to case-specific if none of the above matched.
    return Intent.CASE_SPECIFIC
