"""Load ToMBench JSONL files into the format expected by run_tombench_harness.py.

Each returned sample is a dict with:
  - id:       str   (e.g. "False Belief Task_001")
  - story:    str   (English)
  - question: str   (English)
  - options:  dict  {"A": "...", "B": "...", "C": "...", "D": "..."}
  - answer:   str   ("A" | "B" | "C" | "D")
  - metadata: dict  {"task": "<filename stem>", "ability": "...", "index": int}
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_TOMBENCH_DIR = Path(__file__).resolve().parent / "ToMBench"

_OPT_PREFIX = re.compile(r"^[A-D][\.\s]+", re.IGNORECASE)


def _strip_option_prefix(text: object) -> str:
    """Remove leading 'A. ' / 'B. ' etc. from option text if present."""
    s = str(text) if text is not None else ""
    return _OPT_PREFIX.sub("", s).strip()


def load_tombench(data_dir: Path | str | None = None) -> list[dict]:
    """Load all ToMBench JSONL files and return a flat list of samples."""
    root = Path(data_dir) if data_dir else _TOMBENCH_DIR
    if not root.exists():
        raise FileNotFoundError(f"ToMBench data directory not found: {root}")

    samples: list[dict] = []
    for jsonl_path in sorted(root.glob("*.jsonl")):
        task_name = jsonl_path.stem
        with open(jsonl_path, encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)

                sample_id = f"{task_name}_{line_no:04d}"

                answer_raw = raw.get("答案\nANSWER", "").strip().upper()
                answer = answer_raw if answer_raw in {"A", "B", "C", "D"} else ""

                samples.append({
                    "id": sample_id,
                    "story": raw.get("STORY", ""),
                    "question": raw.get("QUESTION", ""),
                    "options": {
                        "A": _strip_option_prefix(raw.get("OPTION-A", "")),
                        "B": _strip_option_prefix(raw.get("OPTION-B", "")),
                        "C": _strip_option_prefix(raw.get("OPTION-C", "")),
                        "D": _strip_option_prefix(raw.get("OPTION-D", "")),
                    },
                    "answer": answer,
                    "metadata": {
                        "task": task_name,
                        "ability": raw.get("能力\nABILITY", ""),
                        "index": line_no,
                    },
                })
    return samples
