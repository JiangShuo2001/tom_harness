# V2 Skill/RAG Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the v1 skill/RAG systems with Skills v4 (22 SKILL.md + LLM router) and RAG v2 (category-aware retrieval) inside the existing HarnessRuntime single-shot architecture.

**Architecture:** Three independent prompt-injection modules (Skill, RAG, Playbook) each controlled by CLI flags. SkillV4Router wraps `skills_v4/llm_router.py` behind the `Router` interface. RAGv2Engine wraps `ToMRAGv2`. Both plug into `HarnessRuntime.answer_one()` which assembles the final prompt.

**Tech Stack:** Python 3.10+, langchain-community, langchain-core, faiss-cpu, FAISS indices, HuggingFace bge-m3 embeddings.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `tom_harness/tools/skills_v4/` | Move from `skills_v4/` | 22 skill dirs + llm_router.py + ROUTING.md |
| `tom_harness/tools/skills_v4/__init__.py` | Create | Package init |
| `tom_harness/tools/rag_v2.py` | Create (from `rag_v2/src/rag_v2.py`) | RAGv2Engine wrapping ToMRAGv2 |
| `tom_harness/tools/rag_v2_data/` | Move from `rag_v2/data/` | JSONL knowledge bases |
| `tom_harness/tools/rag_v2_index/` | Move from `rag_v2/index_rewritten/` | Pre-built FAISS indices |
| `tom_harness/routing/base.py` | Modify | Relax Router docstring |
| `tom_harness/routing/skill_v4_router.py` | Create | SkillV4Router(Router) adapter |
| `tom_harness/routing/__init__.py` | Modify | Export SkillV4Router |
| `tom_harness/runtime.py` | Modify | 3-module prompt assembly, new fields |
| `tom_harness/tools/__init__.py` | Modify | Export RAGv2Engine |
| `tom_harness/__init__.py` | Modify | Export SkillV4Router |
| `examples/run_tombench_harness.py` | Modify | Use new components |
| `tom_harness/skill_router.py` | Delete | Replaced by skills_v4 |
| `tom_harness/plugins/tom/skills/handlers.py` | Delete | Procedural handlers removed |
| `tom_harness/plugins/tom/router.py` | Delete | Signature-based routing removed |
| `tom_harness/tools/tomrag/` | Delete | Old RAG backend |
| `tom_harness/tools/rag.py` | Delete | Old RAGEngine |
| `tom_harness/tools/skills.py` | Delete | Old SkillLib |

---

### Task 1: Move skills_v4 into tom_harness/tools/

**Files:**
- Move: `skills_v4/` → `tom_harness/tools/skills_v4/`
- Create: `tom_harness/tools/skills_v4/__init__.py`

- [ ] **Step 1: Copy skills_v4 directory into the package**

```bash
cp -r skills_v4/ tom_harness/tools/skills_v4/
```

This copies all 22 skill directories (`skill1/`..`skill22/`), `llm_router.py`, `ROUTING.md`, `README.md`, and supporting files.

- [ ] **Step 2: Create `__init__.py`**

Create `tom_harness/tools/skills_v4/__init__.py`:

```python
"""Skills v4 — 22 declarative SKILL.md skills with LLM-based routing."""
```

- [ ] **Step 3: Verify llm_router.py works from new location**

The `llm_router.py` uses `ROOT = Path(__file__).resolve().parent` to find `skill*/SKILL.md` and `ROUTING.md`. Since these files are co-located in the same directory, the move preserves all path references. Verify:

```bash
cd /Users/surprise/Documents/code/tom_harness
python -c "
from tom_harness.tools.skills_v4.llm_router import ROUTER_CATALOG, get_skill_prompt
print(f'Catalog has {len(ROUTER_CATALOG)} entries')
body = get_skill_prompt('skill1')
print(f'skill1 body length: {len(body)} chars')
print('OK')
"
```

Expected: `Catalog has 23 entries` (22 skills + NONE), skill1 body length > 0, `OK`.

- [ ] **Step 4: Commit**

```bash
git add tom_harness/tools/skills_v4/
git commit -m "feat: move skills_v4 into tom_harness/tools/skills_v4/"
```

---

### Task 2: Move rag_v2 data and create RAGv2Engine

**Files:**
- Move: `rag_v2/data/` → `tom_harness/tools/rag_v2_data/`
- Move: `rag_v2/index_rewritten/` → `tom_harness/tools/rag_v2_index/`
- Create: `tom_harness/tools/rag_v2.py` (from `rag_v2/src/rag_v2.py`)

- [ ] **Step 1: Copy data and index directories**

```bash
cp -r rag_v2/data/ tom_harness/tools/rag_v2_data/
cp -r rag_v2/index_rewritten/ tom_harness/tools/rag_v2_index/
```

- [ ] **Step 2: Create `tom_harness/tools/rag_v2.py`**

This file embeds the `ToMRAGv2` class from `rag_v2/src/rag_v2.py` and adds the `RAGv2Engine` wrapper on top. The `ToMRAGv2` class is copied in directly (not imported from the repo-root `rag_v2/` package) so the harness package is self-contained.

Create `tom_harness/tools/rag_v2.py`:

```python
"""RAG v2 Engine — category-aware retrieval with keyword reranking.

Wraps ToMRAGv2 (FAISS + bge-m3 + LangChain) behind a simple facade
that HarnessRuntime calls directly. Not a Tool subclass — the runtime
invokes it explicitly rather than through the registry.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = str(Path(__file__).resolve().parent / "rag_v2_data")
_DEFAULT_INDEX_DIR = str(Path(__file__).resolve().parent / "rag_v2_index")


class ToMRAGv2:
    """Category-aware RAG with keyword reranking.

    Ported from rag_v2/src/rag_v2.py — kept as a single class to avoid
    external package dependency on the repo-root rag_v2/ directory.
    """

    CATEGORY_RELATIONS = {
        'Belief': {'xWant', 'xNeed', 'xIntent', 'xAttr', 'oWant', 'oNeed'},
        'Desire': {'xWant', 'xNeed', 'Desires', 'NotDesires'},
        'Emotion': {'xReact', 'oReact', 'xEffect', 'oEffect'},
        'Intention': {'xIntent', 'xWant', 'xNeed'},
        'Knowledge': {'xAttr', 'xNeed', 'xWant'},
        'Non-literal': None,
        'Comprehensive': None,
        'Percept': 'skip',
        'Ambiguous Story Task': None,
        'Completion of Failed Actions': {'xIntent', 'xWant'},
        'Discrepant Desires': {'xWant', 'Desires', 'NotDesires'},
        'Discrepant Emotions': {'xReact', 'oReact'},
        'Discrepant Intentions': {'xIntent', 'xWant'},
        'Emotion Regulation': {'xReact', 'oReact'},
        'False Belief Task': {'xWant', 'xNeed', 'xIntent', 'xAttr'},
        'Faux-pas Recognition Test': None,
        'Hidden Emotions': {'xReact', 'oReact'},
        'Hinting Task Test': None,
        'Knowledge-Attention Links': {'xAttr', 'xWant'},
        'Knowledge-Pretend Play Links': {'xAttr', 'xWant'},
        'Moral Emotions': {'xReact', 'oReact'},
        'Multiple Desires': {'xWant', 'Desires'},
        'Percepts-Knowledge Links': {'xAttr', 'xWant'},
        'Persuasion Story Task': None,
        'Prediction of Actions': {'xIntent', 'xWant'},
        'Scalar Implicature Test': None,
        'Strange Story Task': None,
        'Unexpected Outcome Test': {'xWant', 'xIntent'},
    }

    CATEGORY_TO_SOURCES = {
        'Belief': ['atomic'],
        'Desire': ['atomic'],
        'Emotion': ['atomic'],
        'Intention': ['atomic'],
        'Knowledge': ['atomic'],
        'Knowledge-Attention Links': ['atomic'],
        'Knowledge-Pretend Play Links': ['atomic'],
        'Percepts-Knowledge Links': ['atomic'],
        'Discrepant Desires': ['atomic'],
        'Discrepant Emotions': ['atomic', 'social_chem'],
        'Discrepant Intentions': ['atomic'],
        'Completion of Failed Actions': ['atomic'],
        'Prediction of Actions': ['atomic'],
        'False Belief Task': ['atomic'],
        'Hidden Emotions': ['atomic', 'social_chem'],
        'Emotion Regulation': ['atomic', 'social_chem', 'normbank'],
        'Moral Emotions': ['atomic', 'social_chem', 'normbank'],
        'Multiple Desires': ['atomic'],
        'Faux-pas Recognition Test': ['normbank', 'social_chem'],
        'Hinting Task Test': ['social_chem'],
        'Strange Story Task': ['social_chem', 'atomic'],
        'Unexpected Outcome Test': ['atomic', 'social_chem'],
        'Persuasion Story Task': ['social_chem'],
        'Scalar Implicature Test': ['social_chem'],
        'Non-literal': ['atomic', 'social_chem', 'normbank'],
        'Comprehensive': ['atomic', 'social_chem', 'normbank'],
        'Ambiguous Story Task': ['atomic', 'social_chem', 'normbank'],
        'Percept': [],
    }

    STOPWORDS = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'and', 'or', 'but', 'not',
        'no', 'yes', 'what', 'who', 'where', 'when', 'why', 'how', 'which',
        'that', 'this', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
        'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his',
        'her', 'its', 'our', 'their', 'of', 'in', 'on', 'at', 'to', 'for',
        'from', 'with', 'by', 'as', 'if', 'then', 'so', 'than', 'about',
        'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further',
        'once', 'here', 'there', 'all', 'each', 'every', 'both', 'few',
        'more', 'most', 'other', 'some', 'such', 'only', 'own', 'same',
        'too', 'very', 'just', 'now', 'also', 'because', 'while',
    }

    def __init__(
        self,
        data_dir: str = "./data",
        index_dir: str = "./index",
        model_name: str = "./models/bge-m3",
        use_rewritten: bool = False,
    ):
        self.use_rewritten = use_rewritten
        self.data_dir = Path(data_dir)
        self.index_dir = Path(index_dir)

        if self.use_rewritten:
            self.index_dir = Path(str(self.index_dir) + "_rewritten")

        self.index_dir.mkdir(parents=True, exist_ok=True)

        from langchain_community.embeddings import HuggingFaceEmbeddings

        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": True},
        )

        self.stores: dict = {}
        self.loaded = False

    def _load_jsonl(self, file_path: Path, num_samples: int = -1) -> list:
        from langchain_core.documents import Document

        documents = []
        count = 0

        total_lines = sum(1 for _ in open(file_path, 'r', encoding='utf-8'))
        if num_samples > 0:
            total_lines = min(total_lines, num_samples)

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                if num_samples > 0 and count >= num_samples:
                    break
                record = json.loads(line)
                doc = Document(
                    page_content=record['text'],
                    metadata={
                        'id': record['id'],
                        'title': record['title'],
                        'source': record['source'],
                        'category': record.get('category', ''),
                        **record.get('metadata', {})
                    }
                )
                documents.append(doc)
                count += 1
        return documents

    def build_index(self, force_rebuild: bool = False, num_samples: int = -1):
        from langchain_community.vectorstores import FAISS

        sources = ['atomic', 'social_chem', 'normbank']

        for source in sources:
            if self.use_rewritten:
                jsonl_file = self.data_dir / f"{source}_rewritten_clusters.jsonl"
            else:
                jsonl_file = self.data_dir / f"{source}.jsonl"
            index_path = self.index_dir / source

            if not jsonl_file.exists():
                logger.warning("RAG data file %s not found, skipping %s", jsonl_file, source)
                continue

            if index_path.exists() and not force_rebuild:
                logger.info("Loading existing RAG index for %s from %s", source, index_path)
                self.stores[source] = FAISS.load_local(
                    str(index_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                continue

            documents = self._load_jsonl(jsonl_file, num_samples=num_samples)
            logger.info("Loaded %d documents from %s", len(documents), source)

            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]

            batch_size = 32
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                batch_embeddings = self.embeddings.embed_documents(batch_texts)
                all_embeddings.extend(batch_embeddings)

            store = FAISS.from_embeddings(
                text_embeddings=list(zip(texts, all_embeddings)),
                embedding=self.embeddings,
                metadatas=metadatas
            )
            store.save_local(str(index_path))
            self.stores[source] = store
            logger.info("Saved RAG index for %s to %s", source, index_path)

        self.loaded = True

    def _extract_keywords(self, text: str) -> Set[str]:
        words = text.lower().split()
        return {w for w in words if w not in self.STOPWORDS and len(w) > 2}

    def _rerank_by_keywords(self, results: List[Dict], query: str, top_k: int = 10) -> List[Dict]:
        query_keywords = self._extract_keywords(query)
        if not query_keywords:
            return results[:top_k]

        scored = []
        for r in results:
            content_keywords = self._extract_keywords(r['content'])
            overlap = len(query_keywords & content_keywords)
            scored.append((overlap, r))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [r for _, r in scored[:top_k]]

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> List[Dict]:
        if category and not self.CATEGORY_TO_SOURCES.get(category):
            return []

        if not self.loaded:
            raise RuntimeError("Index not built. Call build_index() first.")

        if self.use_rewritten and category:
            allowed_sources = set(self.CATEGORY_TO_SOURCES.get(category, list(self.stores.keys())))
        else:
            allowed_sources = set(self.stores.keys())

        results = []

        for source in self.stores.keys():
            if source not in allowed_sources:
                continue

            store = self.stores[source]
            docs = store.similarity_search(query, k=top_k)

            for doc in docs:
                if source == 'atomic' and category and not self.use_rewritten and self.CATEGORY_RELATIONS.get(category) is not None:
                    relation = doc.metadata.get('category', '')
                    if relation not in self.CATEGORY_RELATIONS[category]:
                        continue

                results.append({
                    'content': doc.page_content,
                    'source': doc.metadata['source'],
                    'category': doc.metadata['category'],
                    'title': doc.metadata['title'],
                    'id': doc.metadata['id'],
                    'metadata': {k: v for k, v in doc.metadata.items()
                                if k not in ['source', 'category', 'title', 'id']}
                })

        reranked = self._rerank_by_keywords(results, query, top_k=top_k)
        return reranked

    def format_context(self, results: List[Dict], max_length: int = 1500) -> str:
        context_parts = []
        total_length = 0

        for i, result in enumerate(results, 1):
            part = f"[{i}] {result['content']}"
            part_length = len(part)

            if total_length + part_length > max_length:
                break

            context_parts.append(part)
            total_length += part_length

        return "\n".join(context_parts)


@dataclass
class RAGv2Engine:
    """Facade over ToMRAGv2 for use by HarnessRuntime."""

    data_dir: str = _DEFAULT_DATA_DIR
    index_dir: str = _DEFAULT_INDEX_DIR
    model_name: str = "model/bge-m3"
    use_rewritten: bool = True

    _backend: Any = field(default=None, init=False, repr=False)
    _ready: bool = field(default=False, init=False, repr=False)

    def build_index(self, force_rebuild: bool = False, num_samples: int = -1) -> None:
        """Build or load FAISS indices."""
        data_path = Path(self.data_dir)
        if not data_path.exists():
            logger.warning("[RAGv2] data_dir %s does not exist — running in empty mode", data_path)
            return

        self._backend = ToMRAGv2(
            data_dir=self.data_dir,
            index_dir=self.index_dir,
            model_name=self.model_name,
            use_rewritten=self.use_rewritten,
        )
        self._backend.build_index(force_rebuild=force_rebuild, num_samples=num_samples)
        self._ready = True

        total = sum(store.index.ntotal for store in self._backend.stores.values())
        logger.info("[RAGv2] Index ready — %d documents across %d sources",
                    total, len(self._backend.stores))

    def retrieve(self, query: str, category: str | None = None, top_k: int = 5) -> str:
        """Search and return formatted context string for prompt injection."""
        if not self._ready:
            return ""
        results = self._backend.search(query=query, top_k=top_k, category=category)
        return self._backend.format_context(results)

    def size(self) -> int:
        """Total number of indexed documents across all sources."""
        if not self._ready:
            return 0
        return sum(store.index.ntotal for store in self._backend.stores.values())
```

- [ ] **Step 3: Verify import works**

```bash
cd /Users/surprise/Documents/code/tom_harness
python -c "
from tom_harness.tools.rag_v2 import RAGv2Engine
e = RAGv2Engine()
print(f'data_dir: {e.data_dir}')
print(f'index_dir: {e.index_dir}')
print('OK')
"
```

Expected: prints default paths and `OK`. (Actual index building requires the embedding model, tested in Task 8.)

- [ ] **Step 4: Commit**

```bash
git add tom_harness/tools/rag_v2.py tom_harness/tools/rag_v2_data/ tom_harness/tools/rag_v2_index/
git commit -m "feat: add RAGv2Engine and move rag_v2 data/index into package"
```

---

### Task 3: Create SkillV4Router

**Files:**
- Modify: `tom_harness/routing/base.py`
- Create: `tom_harness/routing/skill_v4_router.py`
- Modify: `tom_harness/routing/__init__.py`

- [ ] **Step 1: Relax Router base class docstring**

Edit `tom_harness/routing/base.py`. Replace the entire file content with:

```python
"""Router abstract base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RouteDecision:
    """Output of `router.route(...)`. None skill_id means "no skill, raw LLM"."""
    skill_id: str | None
    rationale: str = ""


class Router(ABC):
    """Route a sample to a skill_id.

    Implementations may use LLM calls (e.g. SkillV4Router) or pure
    lookup tables (e.g. OraclePicksRouter).
    """

    @abstractmethod
    def route(
        self,
        *,
        question: str,
        story: str = "",
        options: dict[str, str] | None = None,
        task_type: str | None = None,
    ) -> RouteDecision: ...
```

- [ ] **Step 2: Create `tom_harness/routing/skill_v4_router.py`**

```python
"""SkillV4Router — LLM-based router over 22 skills from skills_v4."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from ..llm import LLMClient
from .base import Router, RouteDecision

logger = logging.getLogger(__name__)

_DEFAULT_SKILLS_DIR = Path(__file__).resolve().parent.parent / "tools" / "skills_v4"


@dataclass
class SkillV4Router(Router):
    """Routes a ToM question to one of 22 skills via a single LLM call."""

    llm: LLMClient
    skills_dir: Path = _DEFAULT_SKILLS_DIR

    def __post_init__(self) -> None:
        import sys
        skills_dir_str = str(self.skills_dir)
        if skills_dir_str not in sys.path:
            sys.path.insert(0, skills_dir_str)

        from tom_harness.tools.skills_v4 import llm_router
        self._router_mod = llm_router

    def route(
        self,
        *,
        question: str,
        story: str = "",
        options: dict[str, str] | None = None,
        task_type: str | None = None,
    ) -> RouteDecision:
        opts = options or {}
        labels = list(opts.keys())
        values = list(opts.values())

        prompt = self._router_mod.build_router_prompt(
            story=story,
            question=question,
            options=values,
            labels=labels,
        )

        try:
            resp = self.llm.chat(
                "You are a skill router. Output only the skill ID.",
                prompt,
                max_tokens=64,
            )
        except Exception as e:
            logger.warning("[SkillV4Router] LLM call failed: %s", e)
            return RouteDecision(skill_id=None, rationale=f"LLM error: {e}")

        skill_id = self._router_mod.parse_router_choice(resp)
        if skill_id is None or skill_id == "NONE":
            return RouteDecision(skill_id=None, rationale=f"router chose NONE (raw: {resp.strip()[:80]})")

        logger.info("[SkillV4Router] Routed to: %s (raw: %s)", skill_id, resp.strip()[:80])
        return RouteDecision(skill_id=skill_id, rationale=f"router chose {skill_id}")

    def get_skill_body(self, skill_id: str) -> str | None:
        """Return the full SKILL.md body (without frontmatter) for the given skill."""
        return self._router_mod.get_skill_prompt(skill_id)
```

- [ ] **Step 3: Update `tom_harness/routing/__init__.py`**

Replace the entire file content with:

```python
"""Routing layer: Router ABC + concrete routers."""

from .base import Router, RouteDecision
from .oracle_picks import ORACLE_PICKS, OraclePicksRouter
from .skill_v4_router import SkillV4Router

__all__ = [
    "Router", "RouteDecision",
    "ORACLE_PICKS", "OraclePicksRouter",
    "SkillV4Router",
]
```

- [ ] **Step 4: Verify SkillV4Router imports cleanly**

```bash
cd /Users/surprise/Documents/code/tom_harness
python -c "
from tom_harness.routing import SkillV4Router
print('SkillV4Router imported OK')
"
```

Expected: `SkillV4Router imported OK` (no LLM client needed for import).

- [ ] **Step 5: Commit**

```bash
git add tom_harness/routing/base.py tom_harness/routing/skill_v4_router.py tom_harness/routing/__init__.py
git commit -m "feat: add SkillV4Router — LLM-based router for 22 skills"
```

---

### Task 4: Modify HarnessRuntime for 3-module prompt assembly

**Files:**
- Modify: `tom_harness/runtime.py`

- [ ] **Step 1: Update `_build_user_prompt` to support 3 modules**

In `tom_harness/runtime.py`, replace the existing `_build_user_prompt` function (lines 65-79) with:

```python
def _build_user_prompt(*, story: str, question: str, options: dict[str, str],
                       skill_body: str | None = None,
                       rag_context: str | None = None,
                       playbook: str | None = None) -> str:
    sections: list[str] = []
    if skill_body:
        sections.append(f"## Reasoning Skill (apply before answering)\n{skill_body}")
    if rag_context:
        sections.append(
            "## Background Knowledge\n"
            "The following information may be relevant to the current question and is for reference only:\n"
            f"{rag_context}"
        )
    if playbook:
        sections.append(f"## Playbook\n{playbook}")
    sections.append(f"## Story\n{story}")
    sections.append(f"## Question\n{question}")
    opts = "\n".join(f"{k}. {v}" for k, v in options.items() if v)
    sections.append(f"## Options\n{opts}")
    sections.append('## Answer\nAfter applying any guidance above, reply with ONLY a JSON object: {"answer": "A"|"B"|"C"|"D"}')
    return "\n\n".join(sections)
```

- [ ] **Step 2: Update HarnessRuntime dataclass and answer_one**

Replace the `HarnessRuntime` class definition (lines 100-201) with:

```python
@dataclass
class HarnessRuntime:
    """Single-shot harness with optional validator-retry."""
    llm: LLMClient
    router: "Router"
    validators: list["Validator"] = field(default_factory=list)
    rag_engine: Any = None
    playbook: str | None = None
    max_retries: int = 1

    def answer_one(
        self,
        *,
        question: str,
        story: str,
        options: dict[str, str],
        task_type: str | None = None,
    ) -> RuntimeResult:
        decision: RouteDecision = self.router.route(
            question=question, story=story, options=options, task_type=task_type
        )
        skill_id = decision.skill_id
        skill_body = None
        if skill_id and hasattr(self.router, 'get_skill_body'):
            skill_body = self.router.get_skill_body(skill_id)
            if skill_body is None:
                logger.warning("router picked skill_id=%s but get_skill_body returned None", skill_id)

        rag_context = None
        if self.rag_engine is not None:
            try:
                rag_context = self.rag_engine.retrieve(
                    query=question, category=task_type
                )
            except Exception as e:
                logger.warning("RAG retrieve failed: %s", e)

        base_user = _build_user_prompt(
            story=story, question=question, options=options,
            skill_body=skill_body, rag_context=rag_context or None,
            playbook=self.playbook,
        )

        # ── 1. initial LLM call ───────────────────────────────────────────
        n_calls = 1
        try:
            text = self.llm.chat(SYSTEM_RAW, base_user, max_tokens=1024)
        except Exception as e:
            logger.warning("initial LLM call failed: %s", e)
            text = ""
        answer = _parse_letter(text)
        events: list[dict] = []

        # ── 2. validators ─────────────────────────────────────────────────
        for v in self.validators:
            if not v.applies(task_type):
                continue
            result: ValidationResult = v.validate(
                question=question, story=story, options=options,
                task_type=task_type, current_answer=answer,
            )
            events.append({
                "validator": v.__class__.__name__,
                "valid": result.valid,
                "rationale": result.rationale,
                "had_suggestion": bool(result.suggested_answer),
            })

            if result.valid:
                continue

            if result.suggested_answer:
                logger.info(
                    "[%s] substituting %s -> %s (%s)",
                    v.__class__.__name__, answer, result.suggested_answer, result.rationale,
                )
                answer = result.suggested_answer
                continue

            for retry_idx in range(self.max_retries):
                retry_user = _build_retry_prompt(
                    base_user=base_user, prior_answer=answer,
                    validator_feedback=result.feedback,
                )
                n_calls += 1
                try:
                    text = self.llm.chat(SYSTEM_RAW, retry_user, max_tokens=1024)
                except Exception as e:
                    logger.warning("retry LLM call failed: %s", e)
                    break
                new_answer = _parse_letter(text)
                if new_answer:
                    answer = new_answer
                result = v.validate(
                    question=question, story=story, options=options,
                    task_type=task_type, current_answer=answer,
                )
                events.append({
                    "validator": v.__class__.__name__,
                    "valid": result.valid,
                    "rationale": result.rationale,
                    "retry": retry_idx + 1,
                })
                if result.valid:
                    break

        return RuntimeResult(
            answer=answer, skill_id=skill_id, n_llm_calls=n_calls,
            validator_events=events,
        )
```

- [ ] **Step 3: Update `build_default_runtime` factory**

Replace the existing `build_default_runtime` function (lines 204-216) with:

```python
def build_default_runtime(
    *,
    llm: LLMClient,
    router: "Router",
    rag_engine: Any = None,
    playbook: str | None = None,
    enable_scalar_validator: bool = True,
) -> HarnessRuntime:
    """Convenience factory: wires the default validator stack."""
    validators: list["Validator"] = []
    if enable_scalar_validator:
        from .validators.scalar_procedural import ScalarProceduralValidator
        validators.append(ScalarProceduralValidator())
    return HarnessRuntime(
        llm=llm, router=router, validators=validators,
        rag_engine=rag_engine, playbook=playbook,
    )
```

- [ ] **Step 4: Remove the `skill_lib` import from runtime.py**

In the imports section at the top of `tom_harness/runtime.py`, remove this line:

```python
from .tools.skills import SkillLib
```

The `SkillLib` is no longer used by the runtime — skill content is accessed via `router.get_skill_body()`.

- [ ] **Step 5: Verify runtime imports cleanly**

```bash
cd /Users/surprise/Documents/code/tom_harness
python -c "
from tom_harness.runtime import HarnessRuntime, build_default_runtime
print('runtime imports OK')
"
```

Expected: `runtime imports OK`.

- [ ] **Step 6: Commit**

```bash
git add tom_harness/runtime.py
git commit -m "feat: extend HarnessRuntime for 3-module prompt assembly (skill/RAG/playbook)"
```

---

### Task 5: Update package exports

**Files:**
- Modify: `tom_harness/tools/__init__.py`
- Modify: `tom_harness/__init__.py`

- [ ] **Step 1: Update `tom_harness/tools/__init__.py`**

Replace the entire file content with:

```python
from .base import Tool, ToolResult
from .memory import MemoryStore
from .rag_v2 import RAGv2Engine
from .playbook import MemoryPlaybook

__all__ = ["Tool", "ToolResult", "MemoryStore", "RAGv2Engine", "MemoryPlaybook"]
```

Note: `SkillLib` and `RAGEngine` are removed. `RAGv2Engine` replaces `RAGEngine`.

- [ ] **Step 2: Update `tom_harness/__init__.py`**

Replace the entire file content with:

```python
"""tom_harness — ToM Agent Harness.

CANONICAL single-shot path (use this by default):
  runtime.HarnessRuntime
    · Router      — routing/ (SkillV4Router or OraclePicksRouter)
    · RAGv2Engine — tools/rag_v2.py (optional, category-aware retrieval)
    · Validators  — validators/ (e.g. ScalarProceduralValidator)
  One LLM call per sample, optional validator-driven retry.

LEGACY Plan/Execute path (kept for research scenarios):
  Scheduler -> Planner -> Executor -> Tool Layer
"""

# ── Canonical (single-shot) ────────────────────────────────────────────────
from .llm import LLMClient
from .runtime import HarnessRuntime, RuntimeResult, build_default_runtime
from .routing import Router, RouteDecision, OraclePicksRouter, SkillV4Router
from .validators import Validator, ValidationResult, ScalarProceduralValidator

# ── Legacy (Plan/Execute) — kept for back-compat, not recommended for ToMBench
from .schemas import (
    Plan, Phase, Step, ToolCall, ToolType,
    ExecutionTrace, Memory, ExecutionContext, FinalResult,
)
from .scheduler import Scheduler
from .planner import Planner
from .executor import Executor
from .registry import ToolRegistry
from .context import ContextManager

__all__ = [
    # canonical
    "LLMClient", "HarnessRuntime", "RuntimeResult", "build_default_runtime",
    "Router", "RouteDecision", "OraclePicksRouter", "SkillV4Router",
    "Validator", "ValidationResult", "ScalarProceduralValidator",
    # legacy
    "Plan", "Phase", "Step", "ToolCall", "ToolType",
    "ExecutionTrace", "Memory", "ExecutionContext", "FinalResult",
    "Scheduler", "Planner", "Executor",
    "ToolRegistry", "ContextManager",
]
__version__ = "0.5.0"
```

- [ ] **Step 3: Verify top-level imports**

```bash
cd /Users/surprise/Documents/code/tom_harness
python -c "
from tom_harness import SkillV4Router, HarnessRuntime, build_default_runtime
from tom_harness.tools import RAGv2Engine
print('All exports OK')
"
```

Expected: `All exports OK`.

- [ ] **Step 4: Commit**

```bash
git add tom_harness/tools/__init__.py tom_harness/__init__.py
git commit -m "feat: update package exports for v2 skill/RAG components"
```

---

### Task 6: Delete old v1 files

**Files:**
- Delete: `tom_harness/skill_router.py`
- Delete: `tom_harness/plugins/tom/skills/handlers.py`
- Delete: `tom_harness/plugins/tom/router.py`
- Delete: `tom_harness/tools/tomrag/` (entire directory)
- Delete: `tom_harness/tools/rag.py`
- Delete: `tom_harness/tools/skills.py`
- Modify: `tom_harness/plugins/tom/skills/__init__.py`
- Modify: `tom_harness/plugins/tom/__init__.py`

- [ ] **Step 1: Delete old files**

```bash
cd /Users/surprise/Documents/code/tom_harness
rm tom_harness/skill_router.py
rm tom_harness/plugins/tom/skills/handlers.py
rm tom_harness/plugins/tom/router.py
rm -rf tom_harness/tools/tomrag/
rm tom_harness/tools/rag.py
rm tom_harness/tools/skills.py
```

- [ ] **Step 2: Fix `tom_harness/plugins/tom/skills/__init__.py`**

The old `__init__.py` imports `register_all` from `handlers.py`. Check and update:

```bash
cat tom_harness/plugins/tom/skills/__init__.py
```

If it imports from `handlers`, replace the content with:

```python
"""ToM skills plugin — procedural handlers removed in v2 migration."""
```

- [ ] **Step 3: Fix `tom_harness/plugins/tom/__init__.py`**

Check if it imports from the deleted `router.py`:

```bash
cat tom_harness/plugins/tom/__init__.py
```

If it imports from `router`, remove those imports. The `__init__.py` should still work without them.

- [ ] **Step 4: Fix `tom_harness/plugins/tom/install.py`**

The `install.py` imports from deleted modules. Update it to be a no-op for the procedural handler and router parts. Replace the file content with:

```python
"""One-call ToM plugin installer.

Note: In v2 migration, procedural handlers and signature-based routing
were removed. This installer now only wires hooks and loads plan templates.
Reasoning skills are loaded via SkillV4Router from tools/skills_v4/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ...hooks import HookRegistry

_PLUGIN_ROOT = Path(__file__).resolve().parent


@dataclass
class ToMInstallation:
    """Record of what was installed."""
    hooks_registered: list[str] = field(default_factory=list)


def install(
    *,
    hooks: HookRegistry,
    **_kwargs,
) -> ToMInstallation:
    """Install ToM plugin hooks."""
    from . import failure_handlers, memory_index, validators

    out = ToMInstallation()
    hooks.register("on_step_failure", failure_handlers.on_step_failure)
    hooks.register("enrich_memory", memory_index.enrich_memory)
    hooks.register("after_step", validators.after_step)
    out.hooks_registered = ["on_step_failure", "enrich_memory", "after_step"]
    return out
```

- [ ] **Step 5: Verify no broken imports in the package**

```bash
cd /Users/surprise/Documents/code/tom_harness
python -c "
from tom_harness import HarnessRuntime, SkillV4Router, build_default_runtime
from tom_harness.tools import RAGv2Engine, MemoryPlaybook
print('All imports OK after deletion')
"
```

Expected: `All imports OK after deletion`.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: remove v1 skill_router, SkillLib, RAGEngine, procedural handlers"
```

---

### Task 7: Update run_tombench_harness.py

**Files:**
- Modify: `examples/run_tombench_harness.py`

- [ ] **Step 1: Rewrite the runner to use v2 components**

Replace the entire content of `examples/run_tombench_harness.py` with:

```python
"""Run the harness on ToMBench — single-shot runtime with v2 skill/RAG.

Usage examples:
  # Run 10 samples per task, no tools
  python examples/run_tombench_harness.py --limit 10

  # Run with skill routing + RAG + memory playbook
  python examples/run_tombench_harness.py --limit 10 --skill --rag --memory

  # Run only "False Belief Task", 5 samples
  python examples/run_tombench_harness.py --tasks "False Belief Task" --limit 5 --skill

  # Run ALL samples across all tasks
  python examples/run_tombench_harness.py --all_tasks --limit 0

Outputs (saved to <out_dir>/):
  - results.jsonl        per-sample records
  - stats.json           per-task + overall accuracy
"""

from __future__ import annotations

import argparse
import json
import logging
import logging.handlers
import os
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmark.load_tombench import load_tombench  # noqa: E402

from tom_harness import LLMClient, build_default_runtime  # noqa: E402
from tom_harness.routing import SkillV4Router  # noqa: E402
from tom_harness.tools.rag_v2 import RAGv2Engine  # noqa: E402
from tom_harness.tools.playbook import MemoryPlaybook  # noqa: E402


class _FrameworkConsoleFilter(logging.Filter):
    """Block tom_harness.* messages on console unless --verbose."""
    def filter(self, record: logging.LogRecord) -> bool:
        return not record.name.startswith("tom_harness")


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("harness_bench")

_framework_logger = logging.getLogger("tom_harness")
_framework_logger.setLevel(logging.DEBUG)
_console_handler = logging.getLogger().handlers[0] if logging.getLogger().handlers else None
_console_filter = _FrameworkConsoleFilter()
if _console_handler:
    _console_handler.addFilter(_console_filter)

from dotenv import load_dotenv  # noqa: E402
load_dotenv()


def build_harness(
    *,
    shared_rag: RAGv2Engine | None = None,
    shared_playbook: MemoryPlaybook | None = None,
    cache_dir: str | None = None,
    enable_skill: bool = False,
    enable_validator: bool = True,
):
    api_base = os.environ.get("TOM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("TOM_API_KEY")
    model = os.environ.get("TOM_MODEL", "qwen3-32b")
    if not api_key:
        raise SystemExit("ERROR: set the TOM_API_KEY env var")

    llm = LLMClient(
        api_base=api_base, api_key=api_key, model=model,
        temperature=0.0, max_tokens=2048, timeout=120.0, max_retries=3,
    )
    if cache_dir:
        llm.set_cache_dir(cache_dir)

    router = SkillV4Router(llm=llm) if enable_skill else None

    playbook_text = None
    if shared_playbook is not None and shared_playbook.ready:
        playbook_text = shared_playbook.content

    from tom_harness.routing.oracle_picks import OraclePicksRouter

    return build_default_runtime(
        llm=llm,
        router=router or OraclePicksRouter(),
        rag_engine=shared_rag if (shared_rag is not None and shared_rag.size() > 0) else None,
        playbook=playbook_text,
        enable_scalar_validator=enable_validator,
    )


def select_samples(
    samples: list[dict],
    *,
    tasks: set[str] | None,
    offset: int,
    limit: int,
) -> list[dict]:
    if tasks:
        samples = [s for s in samples if s["metadata"].get("task", "") in tasks]

    buckets: dict[str, list[dict]] = defaultdict(list)
    for s in samples:
        buckets[s["metadata"].get("task", "")].append(s)

    pool: list[dict] = []
    for t in sorted(buckets):
        bucket = buckets[t]
        sliced = bucket[offset:]
        if limit > 0:
            sliced = sliced[:limit]
        pool.extend(sliced)

    return pool


def process_one(runtime_factory, sample, timeout_sec: float = 180.0):
    buf_handler = logging.handlers.MemoryHandler(capacity=10000, flushLevel=logging.CRITICAL + 1)
    buf_handler.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    buf_handler.setFormatter(fmt)
    framework_logger = logging.getLogger("tom_harness")
    framework_logger.addHandler(buf_handler)

    t0 = time.time()
    rec = {
        "id": sample["id"],
        "task": sample["metadata"].get("task"),
        "answer": sample["answer"],
        "predicted": "",
        "correct": False,
        "skill_id": None,
        "n_llm_calls": 0,
        "elapsed_sec": 0.0,
        "error": None,
    }
    try:
        runtime = runtime_factory()
        result = runtime.answer_one(
            question=sample["question"],
            story=sample["story"],
            options=sample["options"],
            task_type=sample["metadata"].get("task"),
        )
        rec["predicted"] = result.answer
        rec["correct"] = (result.answer == sample["answer"])
        rec["skill_id"] = result.skill_id
        rec["n_llm_calls"] = result.n_llm_calls
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
    rec["elapsed_sec"] = round(time.time() - t0, 2)

    log_lines = []
    for log_record in buf_handler.buffer:
        log_lines.append(fmt.format(log_record))
    framework_logger.removeHandler(buf_handler)
    buf_handler.close()

    return rec, log_lines


def main():
    ap = argparse.ArgumentParser(
        description="Run ToM harness on ToMBench (single-shot runtime).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    data_grp = ap.add_argument_group("data selection")
    data_grp.add_argument("--data_dir", type=str, default=None)
    data_grp.add_argument("--tasks", type=str, default=None,
                          help='Comma-separated task names.')
    data_grp.add_argument("--limit", type=int, default=20,
                          help="Max samples PER TASK (default: 20, 0 = no limit).")
    data_grp.add_argument("--offset", type=int, default=0)

    exec_grp = ap.add_argument_group("execution")
    exec_grp.add_argument("--workers", type=int, default=8)
    exec_grp.add_argument("--verbose", "-v", action="store_true")

    out_grp = ap.add_argument_group("output")
    out_grp.add_argument("--out_dir", default="results")

    rag_grp = ap.add_argument_group("RAG retrieval (v2)")
    rag_grp.add_argument("--rag", action="store_true", help="Enable RAG v2 retrieval.")
    rag_grp.add_argument("--rag_data_dir", type=str, default="tom_harness/tools/rag_v2_data")
    rag_grp.add_argument("--rag_index_dir", type=str, default="tom_harness/tools/rag_v2_index")
    rag_grp.add_argument("--rag_model", type=str, default="model/bge-m3")
    rag_grp.add_argument("--rag_rewritten", action="store_true", default=True,
                         help="Use rewritten cluster data (default: True).")
    rag_grp.add_argument("--no_rag_rewritten", action="store_false", dest="rag_rewritten")

    mem_grp = ap.add_argument_group("Memory playbook")
    mem_grp.add_argument("--memory", action="store_true")
    mem_grp.add_argument("--memory_dir", type=str, default="memory_playbook/")

    skill_grp = ap.add_argument_group("Skill injection (v4)")
    skill_grp.add_argument("--skill", action="store_true",
                           help="Enable LLM-routed skill injection (22 skills).")

    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "results.jsonl"
    stats_path = out_dir / "stats.json"
    log_path = out_dir / "run.log"

    if args.verbose and _console_handler:
        _console_handler.removeFilter(_console_filter)

    _log_file_lock = threading.Lock()
    log_path.write_text("", encoding="utf-8")

    if results_path.exists():
        results_path.unlink()

    samples = load_tombench(data_dir=args.data_dir)
    logger.info("Loaded %d total ToMBench samples", len(samples))

    task_filter = {t.strip() for t in args.tasks.split(",")} if args.tasks else None

    pool = select_samples(samples, tasks=task_filter, offset=args.offset, limit=args.limit)

    task_counts = defaultdict(int)
    for s in pool:
        task_counts[s["metadata"]["task"]] += 1
    logger.info("Selected %d samples across %d tasks (offset=%d, limit=%s per task)",
                len(pool), len(task_counts), args.offset, args.limit or "all")
    for t in sorted(task_counts):
        logger.info("  %-40s %4d", t, task_counts[t])

    if not pool:
        logger.info("Nothing to run.")
        return

    # ── RAG setup ────────────────────────────────────────────────────────
    shared_rag: RAGv2Engine | None = None
    if args.rag:
        shared_rag = RAGv2Engine(
            data_dir=args.rag_data_dir,
            index_dir=args.rag_index_dir,
            model_name=args.rag_model,
            use_rewritten=args.rag_rewritten,
        )
        shared_rag.build_index()
        if shared_rag.size() > 0:
            logger.info("RAG v2 enabled: %d documents indexed", shared_rag.size())
        else:
            logger.info("RAG data not found — running without RAG")
            shared_rag = None

    # ── Memory Playbook setup ────────────────────────────────────────────
    shared_playbook: MemoryPlaybook | None = None
    if args.memory:
        shared_playbook = MemoryPlaybook(playbook_dir=args.memory_dir)
        shared_playbook.load()
        if shared_playbook.ready:
            logger.info("Memory playbook enabled: %d chars loaded", shared_playbook.size())
        else:
            logger.info("Memory playbook data not found — running without playbook")
            shared_playbook = None

    if args.skill:
        logger.info("Skill injection enabled (v4: 22 LLM-routed skills)")

    # ── run ───────────────────────────────────────────────────────────────
    llm_cache_dir = str(out_dir / "llm_cache")
    runtime_factory = lambda: build_harness(  # noqa: E731
        shared_rag=shared_rag,
        shared_playbook=shared_playbook,
        cache_dir=llm_cache_dir,
        enable_skill=args.skill,
    )
    t_start = time.time()
    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as exe:
        futs = {exe.submit(process_one, runtime_factory, s): s for s in pool}
        for fut in as_completed(futs):
            s = futs[fut]
            try:
                rec, log_lines = fut.result(timeout=360)
            except Exception as e:
                rec = {"id": s["id"], "task": s["metadata"].get("task"), "answer": s["answer"],
                       "predicted": "", "correct": False, "error": f"outer: {e}",
                       "skill_id": None, "n_llm_calls": 0, "elapsed_sec": 0.0}
                log_lines = []
            with open(results_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if log_lines:
                with _log_file_lock:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write("\n".join(log_lines) + "\n")
            completed += 1
            if completed % 10 == 0:
                acc_so_far = _live_accuracy(results_path)
                elapsed = (time.time() - t_start) / 60
                logger.info("progress=%d/%d elapsed=%.1fmin running_acc=%.3f",
                            completed, len(pool), elapsed, acc_so_far)

    _print_and_save_stats(results_path, stats_path, pool)


def _print_and_save_stats(results_path: Path, stats_path: Path, pool: list) -> None:
    all_records = _load_all(results_path)
    if not all_records:
        logger.info("No results to summarize.")
        return
    stats = _compute_stats(all_records, pool)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    sep = "=" * 60
    logger.info("\n%s\nHarness results  →  %s\n%s", sep, stats_path, sep)
    logger.info("Overall: %d/%d = %.1f%%  (errors: %d)",
                stats["overall"]["correct"], stats["overall"]["total"],
                stats["overall"]["accuracy"] * 100, stats["overall"]["errors"])
    logger.info("%-40s %4s %7s  %4s", "Task", "N", "Acc", "Err")
    logger.info("-" * 60)
    for t in sorted(stats["per_task"]):
        ts = stats["per_task"][t]
        logger.info("  %-38s %4d %6.1f%%  %4d", t, ts["total"], ts["accuracy"] * 100, ts["errors"])
    logger.info("\nResults saved to: %s", results_path)
    logger.info("Stats   saved to: %s", stats_path)
    logger.info("Log     saved to: %s", results_path.parent / "run.log")


def _live_accuracy(path: Path) -> float:
    n = c = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                n += 1
                c += int(bool(r.get("correct")))
            except Exception:
                pass
    return c / n if n else 0.0


def _load_all(path: Path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def _compute_stats(records, pool):
    total = len(records)
    correct = sum(1 for r in records if r.get("correct"))
    errors = sum(1 for r in records if r.get("error"))
    per_task = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0, "avg_elapsed": 0.0})
    elapsed_sum = defaultdict(float)
    for r in records:
        t = r.get("task", "unknown")
        per_task[t]["total"] += 1
        per_task[t]["correct"] += int(bool(r.get("correct")))
        per_task[t]["errors"] += int(bool(r.get("error")))
        elapsed_sum[t] += float(r.get("elapsed_sec", 0.0) or 0.0)
    for t, d in per_task.items():
        n = d["total"] or 1
        d["accuracy"] = d["correct"] / n
        d["avg_elapsed"] = round(elapsed_sum[t] / n, 2)
    return {
        "overall": {
            "total": total, "correct": correct, "errors": errors,
            "accuracy": round(correct / total, 4) if total else 0,
        },
        "per_task": dict(per_task),
        "mode": "single_shot_v2",
    }


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify syntax**

```bash
cd /Users/surprise/Documents/code/tom_harness
python -c "import ast; ast.parse(open('examples/run_tombench_harness.py').read()); print('Syntax OK')"
```

Expected: `Syntax OK`.

- [ ] **Step 3: Commit**

```bash
git add examples/run_tombench_harness.py
git commit -m "feat: rewrite runner to use v2 skill/RAG via HarnessRuntime"
```

---

### Task 8: Smoke test

- [ ] **Step 1: Verify full import chain**

```bash
cd /Users/surprise/Documents/code/tom_harness
python -c "
from tom_harness import HarnessRuntime, SkillV4Router, build_default_runtime, LLMClient
from tom_harness.tools import RAGv2Engine, MemoryPlaybook
from tom_harness.tools.skills_v4.llm_router import ROUTER_CATALOG, get_skill_prompt
print(f'Router catalog: {len(ROUTER_CATALOG)} entries')
print(f'skill1 body: {len(get_skill_prompt(\"skill1\") or \"\")} chars')

e = RAGv2Engine()
print(f'RAGv2Engine default data_dir: {e.data_dir}')

pb = MemoryPlaybook()
pb.load()
print(f'Playbook ready: {pb.ready}, size: {pb.size()}')

print('ALL IMPORTS AND BASIC CHECKS PASSED')
"
```

Expected: All print statements succeed, `ALL IMPORTS AND BASIC CHECKS PASSED`.

- [ ] **Step 2: Verify CLI help works**

```bash
cd /Users/surprise/Documents/code/tom_harness
python examples/run_tombench_harness.py --help
```

Expected: Help text showing `--skill`, `--rag`, `--rag_rewritten`, `--memory` flags.

- [ ] **Step 3: Dry-run without API key (verify setup path)**

```bash
cd /Users/surprise/Documents/code/tom_harness
TOM_API_KEY="" python examples/run_tombench_harness.py --limit 1 2>&1 || true
```

Expected: Should fail with `ERROR: set the TOM_API_KEY env var` — confirming the runner loads and reaches the API key check without import errors.

- [ ] **Step 4: Commit the full integration**

```bash
git add -A
git commit -m "chore: v2 skill/RAG integration complete — smoke tests pass"
```

---

## Summary

| Task | Description | Key files |
|---|---|---|
| 1 | Move skills_v4 into package | `tom_harness/tools/skills_v4/` |
| 2 | Move rag_v2 data + create RAGv2Engine | `tom_harness/tools/rag_v2.py` |
| 3 | Create SkillV4Router | `tom_harness/routing/skill_v4_router.py` |
| 4 | Modify HarnessRuntime | `tom_harness/runtime.py` |
| 5 | Update package exports | `tom_harness/__init__.py`, `tools/__init__.py` |
| 6 | Delete old v1 files | 6 files/dirs removed |
| 7 | Rewrite runner | `examples/run_tombench_harness.py` |
| 8 | Smoke test | Verification only |
