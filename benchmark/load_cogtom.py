"""Load CogToM JSONL into the format expected by run_cogtom_harness.py.

Each returned sample is a dict with:
  - id:       str   (original id, e.g. "e1_001_1")
  - story:    str   (scene text)
  - question: str
  - options:  dict  {"A": "...", "B": "...", "C": "...", "D": "..."}
  - answer:   str   ("A" | "B" | "C" | "D")
  - metadata: dict  {"category": "...", "subcategory": "...", "scene_id": int, "question_id": int}
"""

from __future__ import annotations

import json
from pathlib import Path

_COGTOM_DIR = Path(__file__).resolve().parent / "cogtom"


def load_cogtom(
    data_dir: Path | str | None = None,
    lang: str = "en",
) -> list[dict]:
    """Load CogToM JSONL and return a flat list of samples."""
    root = Path(data_dir) if data_dir else _COGTOM_DIR
    jsonl_path = root / f"CogToM-{lang}.jsonl"
    if not jsonl_path.exists():
        raise FileNotFoundError(f"CogToM data file not found: {jsonl_path}")

    samples: list[dict] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)

            answer = str(raw.get("answer", "")).strip().upper()
            if answer not in {"A", "B", "C", "D"}:
                answer = ""

            samples.append({
                "id": raw.get("id", ""),
                "story": raw.get("scene", ""),
                "question": raw.get("question", ""),
                "options": raw.get("options", {}),
                "answer": answer,
                "metadata": {
                    "category": raw.get("category", ""),
                    "subcategory": raw.get("subcategory", ""),
                    "scene_id": raw.get("scene_id", 0),
                    "question_id": raw.get("question_id", 0),
                },
            })
    return samples
