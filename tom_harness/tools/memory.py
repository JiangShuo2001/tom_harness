"""Memory Store.

Retrieval-augmented store of (task, plan) pairs. Supports:
  - pluggable embedding function (default: character-trigram hashing —
    dependency-free so the core runs out of the box; swap in a real
    embedder via `embedder=` at construction)
  - metadata filtering (plugins can post-filter by any metadata key)
  - optional similarity threshold
  - JSONL persistence for crash-resumability

The structure is kept generic on purpose — anything ToM-specific lives
in the memories' `metadata` dict, populated by plugins via the
`enrich_memory` hook when they are written.
"""

from __future__ import annotations

import json
import logging
import math
import threading
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


def _make_lock() -> threading.RLock:
    return threading.RLock()

from ..schemas import Memory, ToolType
from .base import Tool

logger = logging.getLogger(__name__)


def _trigram_embed(text: str, dim: int = 256) -> list[float]:
    """Zero-dependency deterministic sparse embedding.

    Hashes character trigrams into a fixed-dim vector and L2-normalizes.
    Not great, but repeatable and has no numpy/transformer dependency.
    Replace via the `embedder=` ctor arg for production use.
    """
    text = text.lower()
    grams = [text[i:i + 3] for i in range(max(0, len(text) - 2))]
    buckets: Counter[int] = Counter()
    for g in grams:
        buckets[hash(g) % dim] += 1
    vec = [float(buckets.get(i, 0)) for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))  # both L2-normalized


@dataclass
class MemoryStore(Tool):
    """Vector-index store of (task, plan) pairs."""

    persist_path: Path | None = None
    embedder: Callable[[str], list[float]] = field(default=_trigram_embed)
    _memories: dict[str, Memory] = field(default_factory=dict, init=False)
    _embeddings: dict[str, list[float]] = field(default_factory=dict, init=False)
    _lock: "threading.RLock" = field(default_factory=lambda: _make_lock(), init=False)

    def __post_init__(self) -> None:
        if self.persist_path and self.persist_path.exists():
            self._load()

    # ── Tool interface ──────────────────────────────────────────────────────
    @property
    def tool_type(self) -> ToolType:
        return ToolType.MEMORY

    @property
    def tool_name(self) -> str:
        return "memory_retrieve"

    @property
    def description(self) -> str:
        return "Retrieve (task, plan) pairs similar to the current query. Params: query:str, top_k:int=3, similarity_threshold:float=0.0, task_type_filter:str|None, metadata_filter:dict|None"

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        out = dict(params)
        out.setdefault("top_k", 3)
        out.setdefault("similarity_threshold", 0.0)
        out.setdefault("task_type_filter", None)
        out.setdefault("metadata_filter", None)
        if "query" not in out:
            raise ValueError("memory_retrieve requires `query`")
        return out

    def run(
        self,
        *,
        query: str,
        top_k: int = 3,
        similarity_threshold: float = 0.0,
        task_type_filter: str | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        q_emb = self.embedder(query)
        with self._lock:
            items = list(self._memories.items())
        scored: list[tuple[float, Memory]] = []
        for mid, mem in items:
            if task_type_filter and mem.task.task_type != task_type_filter:
                continue
            if metadata_filter and not self._match_metadata(mem.metadata, metadata_filter):
                continue
            with self._lock:
                emb = self._embeddings.get(mid)
            if emb is None:
                continue
            score = _cosine(q_emb, emb)
            if score < similarity_threshold:
                continue
            scored.append((score, mem))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]
        return {
            "memories": [
                {"memory_id": m.memory_id,
                 "similarity_score": float(s),
                 "task": m.task.model_dump(),
                 "plan_summary": _summarize_plan(m.plan),
                 "metadata": m.metadata,
                 "full_memory": m.model_dump()}
                for s, m in top
            ]
        }

    # ── Direct (non-tool) API used by Scheduler / plugins ──────────────────
    def insert(self, memory: Memory) -> None:
        key_text = f"{memory.task.question} | {memory.task.task_type}"
        emb = self.embedder(key_text)
        with self._lock:
            self._memories[memory.memory_id] = memory
            self._embeddings[memory.memory_id] = emb
            if self.persist_path:
                self._append_persist(memory)

    def size(self) -> int:
        with self._lock:
            return len(self._memories)

    # ── internals ──────────────────────────────────────────────────────────
    @staticmethod
    def _match_metadata(metadata: dict[str, Any], filter_: dict[str, Any]) -> bool:
        for k, v in filter_.items():
            if metadata.get(k) != v:
                return False
        return True

    def _append_persist(self, memory: Memory) -> None:
        assert self.persist_path is not None
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.persist_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(memory.model_dump(), ensure_ascii=False) + "\n")

    def _load(self) -> None:
        assert self.persist_path is not None
        with open(self.persist_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    m = Memory(**json.loads(line))
                    self._memories[m.memory_id] = m
                    key_text = f"{m.task.question} | {m.task.task_type}"
                    self._embeddings[m.memory_id] = self.embedder(key_text)
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Skipped malformed memory line: {e}")


def _summarize_plan(plan: Any) -> str:
    try:
        phases = plan.phases
        return " → ".join(f"{p.phase_name}({len(p.steps)} steps)" for p in phases)
    except Exception:  # noqa: BLE001
        return ""
