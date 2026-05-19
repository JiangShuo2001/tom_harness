"""ExperienceStore — file-based persistence for optimizer runs.

The optimizer never writes into the original ``tom_harness`` tree. All
its artefacts live under ``optimizer_runs/run_<NNN>/``:

    optimizer_runs/
      run_000/
        candidate_policy.yaml
        scores.json
        stats_by_task.json
        stats_by_ability.json
        traces/
          <sample_id>.json
        module_conflicts.jsonl
        wins_losses.json
        diagnosis.md

The store is deliberately small: it writes JSON/YAML and lets callers
decide what counts as a "score" or "trace". This keeps it usable by
proposer/evaluator implementations we have not yet written.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import dump_yaml


_SAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass
class ExperienceStore:
    """Filesystem-backed run store. Pure I/O — no business logic."""

    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    # ── run lifecycle ─────────────────────────────────────────────────
    def create_run(self, name: str | None = None) -> Path:
        """Create a new run directory and return its path.

        If ``name`` is provided it is sanitised and used verbatim;
        otherwise a sequential ``run_NNN`` directory is created.
        """
        if name:
            run_dir = self.root / _SAFE_ID.sub("_", name)
        else:
            existing = sorted(p.name for p in self.root.glob("run_*") if p.is_dir())
            n = 0
            for nm in existing:
                try:
                    n = max(n, int(nm.split("_", 1)[1]) + 1)
                except (IndexError, ValueError):
                    continue
            run_dir = self.root / f"run_{n:03d}"
        (run_dir / "traces").mkdir(parents=True, exist_ok=True)
        return run_dir

    def list_runs(self) -> list[Path]:
        return sorted(p for p in self.root.iterdir() if p.is_dir())

    # ── writes ────────────────────────────────────────────────────────
    def save_candidate_policy(self, run_dir: Path, policy: dict) -> Path:
        path = Path(run_dir) / "candidate_policy.yaml"
        dump_yaml(policy, path)
        return path

    def save_score(self, run_dir: Path, score: dict) -> Path:
        path = Path(run_dir) / "scores.json"
        path.write_text(
            json.dumps(score, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return path

    def save_stats(
        self, run_dir: Path, stats: dict, *, name: str = "stats_by_task"
    ) -> Path:
        path = Path(run_dir) / f"{_SAFE_ID.sub('_', name)}.json"
        path.write_text(
            json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return path

    def save_trace(self, run_dir: Path, sample_id: str, trace: dict) -> Path:
        sid = _SAFE_ID.sub("_", sample_id)
        path = Path(run_dir) / "traces" / f"{sid}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return path

    def append_module_conflict(self, run_dir: Path, record: dict) -> Path:
        path = Path(run_dir) / "module_conflicts.jsonl"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False))
            fh.write("\n")
        return path

    def save_wins_losses(self, run_dir: Path, payload: dict) -> Path:
        path = Path(run_dir) / "wins_losses.json"
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return path

    def save_diagnosis(self, run_dir: Path, markdown: str) -> Path:
        path = Path(run_dir) / "diagnosis.md"
        path.write_text(markdown, encoding="utf-8")
        return path

    # ── reads ─────────────────────────────────────────────────────────
    def load_traces(self, run_dir: Path) -> list[dict]:
        traces_dir = Path(run_dir) / "traces"
        if not traces_dir.exists():
            return []
        out: list[dict] = []
        for fp in sorted(traces_dir.glob("*.json")):
            try:
                out.append(json.loads(fp.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
        return out

    def load_score(self, run_dir: Path) -> dict | None:
        path = Path(run_dir) / "scores.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def load_module_conflicts(self, run_dir: Path) -> list[dict]:
        path = Path(run_dir) / "module_conflicts.jsonl"
        if not path.exists():
            return []
        out: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out
