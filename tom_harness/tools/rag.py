"""RAG Engine.

Generic retrieval over a corpus of text snippets. In the harness spec this
is used for social-norm knowledge, but the engine itself is domain-agnostic:
hand it any JSONL corpus with `{id, text, metadata}` records and it will
index them with the same embedder interface the MemoryStore uses.

Design: identical embedder contract to MemoryStore so both can share a
production-grade embedder once one is plugged in.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..schemas import ToolType
from .base import Tool


def _trigram_embed(text: str, dim: int = 256) -> list[float]:
    text = text.lower()
    grams = [text[i:i + 3] for i in range(max(0, len(text) - 2))]
    buckets: Counter[int] = Counter()
    for g in grams:
        buckets[hash(g) % dim] += 1
    vec = [float(buckets.get(i, 0)) for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


@dataclass
class RAGDocument:
    doc_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGEngine(Tool):
    """Minimal retrieval engine with pluggable embedder."""

    corpus_path: Path | None = None
    embedder: Callable[[str], list[float]] = field(default=_trigram_embed)
    _docs: dict[str, RAGDocument] = field(default_factory=dict, init=False)
    _embeddings: dict[str, list[float]] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.corpus_path and self.corpus_path.exists():
            self.load_corpus(self.corpus_path)

    # ── Tool interface ─────────────────────────────────────────────────────
    @property
    def tool_type(self) -> ToolType:
        return ToolType.RAG

    @property
    def tool_name(self) -> str:
        return "rag_retrieve"

    @property
    def description(self) -> str:
        return "Retrieve top_k passages from the knowledge corpus. Params: query:str, top_k:int=5, domain_filter:list[str]|None"

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        out = dict(params)
        out.setdefault("top_k", 5)
        out.setdefault("domain_filter", None)
        if "query" not in out:
            raise ValueError("rag_retrieve requires `query`")
        return out

    def run(
        self,
        *,
        query: str,
        top_k: int = 5,
        domain_filter: list[str] | None = None,
    ) -> dict[str, Any]:
        q_emb = self.embedder(query)
        scored: list[tuple[float, RAGDocument]] = []
        for did, doc in self._docs.items():
            if domain_filter:
                if doc.metadata.get("domain") not in domain_filter:
                    continue
            score = _cosine(q_emb, self._embeddings[did])
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]
        return {
            "passages": [
                {"doc_id": d.doc_id, "text": d.text, "score": float(s), "metadata": d.metadata}
                for s, d in top
            ]
        }

    # ── corpus management ─────────────────────────────────────────────────
    def load_corpus(self, path: Path) -> None:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                doc = RAGDocument(
                    doc_id=rec["id"],
                    text=rec["text"],
                    metadata=rec.get("metadata", {}),
                )
                self._docs[doc.doc_id] = doc
                self._embeddings[doc.doc_id] = self.embedder(doc.text)

    def add_document(self, doc: RAGDocument) -> None:
        self._docs[doc.doc_id] = doc
        self._embeddings[doc.doc_id] = self.embedder(doc.text)

    def size(self) -> int:
        return len(self._docs)
