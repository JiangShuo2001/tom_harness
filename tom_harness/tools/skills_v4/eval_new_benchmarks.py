"""Small prompt/answer helpers used by skills_v4 experiments."""
from __future__ import annotations

import re
from collections.abc import Iterable


def build_vanilla_prompt(
    story: str,
    question: str,
    options: Iterable[str],
    labels: Iterable[str],
) -> str:
    opts = "\n".join(f"{label}. {option}" for label, option in zip(labels, options))
    return (
        "Read the story and answer the multiple-choice question.\n\n"
        f"Story:\n{story}\n\n"
        f"Question:\n{question}\n\n"
        f"Options:\n{opts}\n\n"
        "Choose exactly one option letter."
    )


def extract_answer_letter(response: str, labels: Iterable[str]):
    if not response:
        return None
    valid = {str(label).upper() for label in labels}
    patterns = [
        r"(?:FINAL\s+ANSWER|ANSWER)\s*[:\-]\s*\(?([A-Z])\)?",
        r"\b([A-Z])\b",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, response, flags=re.IGNORECASE):
            letter = match.upper()
            if letter in valid:
                return letter
    return None
