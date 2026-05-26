"""Load TactfulToM dataset into the harness-compatible format.

Supports two evaluation modes:
  - Multiple-choice (mcq/binary): unified A/B/C/D format via HarnessRuntime
  - List generation (list): model outputs character names, scored by set match

Each returned sample is a dict with:
  - id:       str   (e.g. "0-1-0-0-belief-3")
  - story:    str   (the full_context conversation)
  - question: str
  - options:  dict  {"A": "...", "B": "...", ...}   (for mcq/binary)
  - answer:   str   ("A" | "B" | "C" | "D")         (for mcq/binary)
  - answer_list: list[str]                           (for list mode, ground truth names)
  - metadata: dict  {"task": ..., "eval_mode": "mcq"|"binary"|"list", ...}

Question categories (for per-category analysis):
  - comprehension       (binary: was the lie true?)
  - justification       (multi-choice: why did the liar lie?)
  - fact                (multi-choice: who discussed X?)
  - belief              (multi-choice: what does X believe about Y?)
  - info_accessibility  (binary + list: who knows X?)
  - answerability       (binary + list: who can answer X?)
  - liedetectability    (binary + list: who can detect the lie?)
  - lieability          (multi-choice: why can the liar lie?)
"""

from __future__ import annotations

import json
import random
from pathlib import Path

_TACTFUL_DIR = Path(__file__).resolve().parent / "tactful-tom" / "dataset" / "final_set"

# Question type -> high-level category for grouping
_CATEGORY_MAP = {
    "comprehension": "comprehension",
    "justification:liar": "justification",
    "justification:liar:accompliance": "justification",
    "fact:real_reason": "fact",
    "fact:truth": "fact",
    "tom:belief:accessible:reason": "belief",
    "tom:belief:accessible:truth": "belief",
    "tom:belief:inaccessible:reason": "belief",
    "tom:belief:inaccessible:truth": "belief",
    "tom:info_accessibility:binary:real_reason": "info_accessibility",
    "tom:info_accessibility:binary:truth": "info_accessibility",
    "tom:info_accessibility:list:real_reason": "info_accessibility",
    "tom:info_accessibility:list:truth": "info_accessibility",
    "tom:answerability:binary:real_reason": "answerability",
    "tom:answerability:binary:truth": "answerability",
    "tom:answerability:list:real_reason": "answerability",
    "tom:answerability:list:truth": "answerability",
    "tom:liedetectability:binary": "liedetectability",
    "tom:liedetectability:list": "liedetectability",
    "tom:lieability:liar:real_reason": "lieability",
    "tom:lieability:liar:truth": "lieability",
    "tom:lieability:accomplice:real_reason": "lieability",
    "tom:lieability:accomplice:truth": "lieability",
}


def _format_list_answer(names: list[str]) -> str:
    """Format a list of character names into a readable string."""
    if len(names) == 1:
        return names[0]
    elif len(names) == 2:
        return f"{names[0]} and {names[1]}"
    else:
        return ", ".join(names[:-1]) + f", and {names[-1]}"


def _build_mc_sample(
    *,
    q_id: str,
    story: str,
    question: str,
    correct: str,
    wrongs: list[str],
    question_type: str,
    set_id: str,
    lie_type: str,
    seed: int | None = None,
) -> dict:
    """Build a standard multi-choice sample from correct + wrong answers."""
    rng = random.Random(seed if seed is not None else hash(q_id))

    all_options = [correct] + wrongs[:3]
    while len(all_options) < 2:
        all_options.append("(no answer)")
    all_options = all_options[:4]

    indices = list(range(len(all_options)))
    rng.shuffle(indices)

    labels = "ABCD"
    options = {}
    answer_letter = ""
    for new_pos, old_idx in enumerate(indices):
        options[labels[new_pos]] = all_options[old_idx]
        if old_idx == 0:
            answer_letter = labels[new_pos]

    category = _CATEGORY_MAP.get(question_type, question_type.split(":")[0])

    return {
        "id": q_id,
        "story": story,
        "question": question,
        "options": options,
        "answer": answer_letter,
        "metadata": {
            "task": question_type,
            "category": category,
            "set_id": set_id,
            "lie_type": lie_type,
            "q_id": q_id,
        },
    }


def _build_binary_sample(
    *,
    q_id: str,
    story: str,
    question: str,
    correct: str,
    question_type: str,
    set_id: str,
    lie_type: str,
    seed: int | None = None,
) -> dict:
    """Build a binary (yes/no) sample as a 2-option multiple-choice."""
    correct_lower = correct.strip().lower()
    if correct_lower == "yes":
        options_raw = ["Yes", "No"]
    else:
        options_raw = ["No", "Yes"]

    rng = random.Random(seed if seed is not None else hash(q_id))
    indices = [0, 1]
    rng.shuffle(indices)

    labels = "AB"
    options = {}
    answer_letter = ""
    for new_pos, old_idx in enumerate(indices):
        options[labels[new_pos]] = options_raw[old_idx]
        if old_idx == 0:
            answer_letter = labels[new_pos]

    category = _CATEGORY_MAP.get(question_type, question_type.split(":")[0])

    return {
        "id": q_id,
        "story": story,
        "question": question,
        "options": options,
        "answer": answer_letter,
        "metadata": {
            "task": question_type,
            "category": category,
            "set_id": set_id,
            "lie_type": lie_type,
            "q_id": q_id,
        },
    }


def _build_list_sample(
    *,
    q_id: str,
    story: str,
    question: str,
    correct_list: list[str],
    wrong_list: list[str],
    question_type: str,
    set_id: str,
    lie_type: str,
    all_characters: list[str],
    seed: int | None = None,
) -> dict:
    """Build a list-generation sample (model outputs names, scored by set match).

    The model is asked to output a comma-separated list of character names.
    Scoring uses exact set match (precision=1 AND recall=1).
    """
    category = _CATEGORY_MAP.get(question_type, question_type.split(":")[0])

    return {
        "id": q_id,
        "story": story,
        "question": question,
        "options": {},
        "answer": "",
        "answer_list": sorted(correct_list),
        "all_characters": sorted(all_characters),
        "metadata": {
            "task": question_type,
            "category": category,
            "set_id": set_id,
            "lie_type": lie_type,
            "q_id": q_id,
            "eval_mode": "list",
        },
    }


# QA keys in each conversation item that we extract
_QA_KEYS = [
    "comprehensionQA",
    "justificationQA",
    "fact_reasonQA",
    "fact_truthQA",
    "beliefQAs",
    "infoAccessibilityQA_list",
    "infoAccessibilityQAs_binary",
    "answerabilityQA_list",
    "answerabilityQAs_binary",
    "liedetectabilityQAs_list",
    "liedetectabilityQAs_binary",
    "lieabilityQAs",
]


def _extract_samples_from_item(item: dict, story: str) -> list[dict]:
    """Extract all QA samples from a single conversation item."""
    set_id = item.get("set_id", "")
    lie_type = item.get("lie_type", "")
    characters_dict = item.get("characters", {})
    all_characters = list(characters_dict.values()) if characters_dict else []
    samples: list[dict] = []

    for qa_key in _QA_KEYS:
        qa_list = item.get(qa_key)
        if not qa_list or not isinstance(qa_list, list):
            continue

        for qa in qa_list:
            q_id = qa.get("q_id", f"{set_id}-{qa_key}")
            question_type = qa.get("question_type", qa_key)
            question = qa.get("question", "")
            correct = qa.get("correct_answer")
            wrong = qa.get("wrong_answer")

            if not question:
                continue

            if isinstance(correct, list) and isinstance(wrong, list):
                sample = _build_list_sample(
                    q_id=q_id,
                    story=story,
                    question=question,
                    correct_list=correct,
                    wrong_list=wrong,
                    question_type=question_type,
                    set_id=set_id,
                    lie_type=lie_type,
                    all_characters=all_characters,
                )
            elif isinstance(correct, str) and isinstance(wrong, list):
                sample = _build_mc_sample(
                    q_id=q_id,
                    story=story,
                    question=question,
                    correct=correct,
                    wrongs=wrong,
                    question_type=question_type,
                    set_id=set_id,
                    lie_type=lie_type,
                )
            elif isinstance(correct, str) and (wrong is None or isinstance(wrong, str)):
                sample = _build_binary_sample(
                    q_id=q_id,
                    story=story,
                    question=question,
                    correct=correct,
                    question_type=question_type,
                    set_id=set_id,
                    lie_type=lie_type,
                )
            else:
                continue

            samples.append(sample)

    return samples


def load_tactful_tom(
    data_dir: Path | str | None = None,
    *,
    sets: list[int] | None = None,
    categories: set[str] | None = None,
    question_types: set[str] | None = None,
) -> list[dict]:
    """Load TactfulToM dataset and return a flat list of harness-compatible samples.

    Args:
        data_dir: Path to final_set/ directory. Defaults to bundled location.
        sets: Which set indices to load (0-4). None = all.
        categories: Filter by high-level category (comprehension, belief, etc.). None = all.
        question_types: Filter by specific question_type. None = all.

    Returns:
        List of sample dicts compatible with HarnessRuntime.answer_one().
    """
    root = Path(data_dir) if data_dir else _TACTFUL_DIR
    if not root.exists():
        raise FileNotFoundError(f"TactfulToM data directory not found: {root}")

    set_indices = sets if sets is not None else list(range(5))
    all_samples: list[dict] = []

    for idx in set_indices:
        path = root / f"Tactful_conv_set_{idx}.json"
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as f:
            conversations = json.load(f)

        for item in conversations:
            story = item.get("full_context", "")
            if not story:
                continue
            samples = _extract_samples_from_item(item, story)
            all_samples.extend(samples)

    if categories:
        all_samples = [
            s for s in all_samples
            if s["metadata"].get("category") in categories
        ]

    if question_types:
        all_samples = [
            s for s in all_samples
            if s["metadata"].get("task") in question_types
        ]

    return all_samples
