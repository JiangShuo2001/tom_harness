"""RAG Engine — adapter wrapping ToMRAG (FAISS + bge-m3).

Provides the standard ``Tool`` interface so the rest of the harness
(Registry, Planner, Executor) interacts with RAG through the same
dispatch path as Memory and Skill.

When *data_dir* is ``None`` or the directory does not exist the engine
operates in **empty mode**: every search returns zero results.  This
preserves backward compatibility for no-tools / cold-start runs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..schemas import ToolType
from .base import Tool

logger = logging.getLogger(__name__)

_TOMRAG_DATA_DIR = str(Path(__file__).resolve().parent / "tomrag" / "data")
_TOMRAG_INDEX_DIR = str(Path(__file__).resolve().parent / "tomrag" / "index")


@dataclass
class RAGEngine(Tool):
    """FAISS-backed retrieval over social-norm knowledge bases.

    Wraps :class:`tom_harness.tools.tomrag.ToMRAG` behind the harness
    ``Tool`` interface.  Call :meth:`build_index` once (idempotent) before
    running searches; subsequent calls load the cached FAISS index from
    disk in seconds.

    Parameters
    ----------
    data_dir:
        Directory containing ``{atomic,social_chem,normbank}.jsonl``.
        Defaults to ``tom_harness/tools/tomrag/data/``.
    index_dir:
        Directory for persisted FAISS indices (auto-created).
        Defaults to ``tom_harness/tools/tomrag/index/``.
    model_name:
        Path or HuggingFace name of the embedding model (default bge-m3).
    """

    data_dir: str | None = _TOMRAG_DATA_DIR
    index_dir: str | None = _TOMRAG_INDEX_DIR
    model_name: str = "model/bge-m3"

    _backend: Any = field(default=None, init=False, repr=False)
    _ready: bool = field(default=False, init=False, repr=False)

    # ── Tool interface ─────────────────────────────────────────────────────
    @property
    def tool_type(self) -> ToolType:
        return ToolType.RAG

    @property
    def tool_name(self) -> str:
        return "rag_retrieve"

    @property
    def description(self) -> str:
        return (
            "Retrieve top_k passages of social-norm / commonsense knowledge. "
            "Params: query:str, top_k:int=5, source_filter:list[str]|None"
        )

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        out = dict(params)
        out.setdefault("top_k", 5)
        out.setdefault("source_filter", None)
        if "query" not in out:
            raise ValueError("rag_retrieve requires `query`")
        return out

    def run(
        self,
        *,
        query: str,
        top_k: int = 5,
        source_filter: list[str] | None = None,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        """Search the knowledge corpus and return ranked passages."""
        if not self._ready:
            return {"passages": []}

        results = self._backend.search(
            query=query,
            top_k=top_k,
            source_filter=source_filter,
        )
        return {
            "passages": [
                {
                    "doc_id": r["id"],
                    "text": r["content"],
                    "source": r["source"],
                    "category": r["category"],
                    "title": r["title"],
                    "metadata": r.get("metadata", {}),
                }
                for r in results
            ]
        }

    # ── lifecycle ──────────────────────────────────────────────────────────
    def build_index(
        self,
        *,
        force_rebuild: bool = False,
        num_samples: int = -1,
    ) -> None:
        """Build (or load cached) FAISS indices for all knowledge sources.

        Must be called once before :meth:`run`. Subsequent calls are
        near-instant when indices already exist on disk.
        """
        if self.data_dir is None:
            logger.info("[RAG] No data_dir configured — running in empty mode")
            return

        data_path = Path(self.data_dir)
        if not data_path.exists():
            logger.warning("[RAG] data_dir %s does not exist — running in empty mode", data_path)
            return

        index_dir = self.index_dir or str(data_path.parent / "index")

        from .tomrag import ToMRAG

        logger.info("[RAG] Initializing ToMRAG (model=%s, data=%s, index=%s)",
                     self.model_name, self.data_dir, index_dir)
        self._backend = ToMRAG(
            data_dir=str(data_path),
            index_dir=index_dir,
            model_name=self.model_name,
        )
        self._backend.build_index(force_rebuild=force_rebuild, num_samples=num_samples)
        self._ready = True

        total = sum(store.index.ntotal for store in self._backend.stores.values())
        logger.info("[RAG] Index ready — %d documents across %d sources",
                     total, len(self._backend.stores))

    def format_context(self, results: list[dict], max_length: int = 2000) -> str:
        """Format search results as a text block for prompt injection."""
        if not self._ready:
            return ""
        search_results = [
            {
                "content": r.get("text", r.get("content", "")),
                "source": r.get("source", ""),
                "category": r.get("category", ""),
                "title": r.get("title", ""),
                "id": r.get("doc_id", r.get("id", "")),
                "metadata": r.get("metadata", {}),
            }
            for r in results
        ]
        return self._backend.format_context(search_results, max_length=max_length)

    def size(self) -> int:
        """Total number of indexed documents across all sources."""
        if not self._ready:
            return 0
        return sum(store.index.ntotal for store in self._backend.stores.values())
