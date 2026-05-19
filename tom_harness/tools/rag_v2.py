"""RAG v2 Engine — ToM rules retrieval with category-aware filtering.

Wraps ToMRulesV1RAG (FAISS + bge-m3 + LangChain) behind a simple facade
that HarnessRuntime calls directly.  Uses hand-crafted ToM reasoning rules
(tom_rules_v2.jsonl, ~294 entries) as the single knowledge source.

Optionally includes a CategoryClassifier that uses a helper LLM to predict
the ToM category when ground-truth metadata is unavailable.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = str(Path(__file__).resolve().parent / "rag_v2_data")
_DEFAULT_INDEX_DIR = str(Path(__file__).resolve().parent / "rag_v2_index")


# ── Known categories ────────────────────────────────────────────────────────

CATEGORY_TO_USE_RAG: dict[str, bool] = {
    'Belief': True,
    'Desire': True,
    'Emotion': True,
    'Intention': True,
    'Knowledge': True,
    'Knowledge-Attention Links': True,
    'Knowledge-Pretend Play Links': True,
    'Percepts-Knowledge Links': True,
    'Discrepant Desires': True,
    'Discrepant Emotions': True,
    'Discrepant Intentions': True,
    'Completion of Failed Actions': True,
    'Prediction of Actions': True,
    'False Belief Task': True,
    'Hidden Emotions': True,
    'Emotion Regulation': True,
    'Moral Emotions': True,
    'Multiple Desires': True,
    'Faux-pas Recognition Test': True,
    'Hinting Task Test': True,
    'Strange Story Task': True,
    'Unexpected Outcome Test': True,
    'Persuasion Story Task': False,
    'Scalar Implicature Test': True,
    'Non-literal': True,
    'Comprehensive': True,
    'Ambiguous Story Task': True,
    'Percept': False,
}

CATEGORY_MAPPING: dict[str, str] = {
    'Belief': 'Belief',
    'Comprehensive': 'Comprehensive',
    'Knowledge': 'Knowledge',
    'Ambiguous Story Task': 'Ambiguous Story Task',
    'Completion of Failed Actions': 'Completion of Failed Actions',
    'Discrepant Desires': 'Discrepant Desires',
    'Emotion Regulation': 'Emotion Regulation',
    'Knowledge-Attention Links': 'Knowledge-Attention Links',
    'Knowledge-Pretend Play Links': 'Knowledge-Pretend Play Links',
    'Moral Emotions': 'Moral Emotions',
    'Persuasion Story Task': 'Persuasion Story Task',
    'Scalar Implicature Test': 'Scalar Implicature Test',
    'Unexpected Outcome Test': 'Unexpected Outcome Test',
}

ALL_CATEGORIES = sorted(CATEGORY_TO_USE_RAG.keys())

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


# ── Category classifier ─────────────────────────────────────────────────────

_CLASSIFIER_PROMPT = (
    "You are a Theory of Mind task classifier. Given a story and question, "
    "classify the question into exactly one of the following categories.\n\n"
    "Categories:\n{categories}\n\n"
    "Story:\n{story}\n\n"
    "Question:\n{question}\n\n"
    'Output ONLY a JSON object: {{"category": "<one category from the list>"}}'
)


@dataclass
class CategoryClassifier:
    """LLM-based classifier: question + story -> ToM category."""

    api_base: str
    api_key: str
    model: str
    max_retries: int = 3
    timeout: float = 30.0

    def classify(self, question: str, story: str = "") -> str | None:
        """Return a category string or None on failure."""
        import requests

        categories_str = "\n".join(f"- {c}" for c in ALL_CATEGORIES)
        prompt = _CLASSIFIER_PROMPT.format(
            categories=categories_str,
            story=story or "(no story)",
            question=question,
        )

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 64,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(self.max_retries):
            try:
                resp = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers, json=payload, timeout=self.timeout,
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"].get("content", "")
                return self._parse(content)
            except Exception as e:
                logger.warning("[CategoryClassifier] attempt %d failed: %s", attempt + 1, e)
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        return None

    @staticmethod
    def _parse(text: str) -> str | None:
        import re
        text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
        try:
            d = json.loads(text)
            cat = d.get("category", "").strip()
            if cat in CATEGORY_TO_USE_RAG:
                return cat
        except json.JSONDecodeError:
            pass
        # fallback: try extracting from ```json``` block
        m = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if m:
            try:
                d = json.loads(m.group(1))
                cat = d.get("category", "").strip()
                if cat in CATEGORY_TO_USE_RAG:
                    return cat
            except json.JSONDecodeError:
                pass
        # fallback: exact substring match
        for cat in ALL_CATEGORIES:
            if cat in text:
                return cat
        return None


# ── ToMRulesV1RAG ────────────────────────────────────────────────────────────

class ToMRulesV1RAG:
    """RAG using tom_rules_v2 with optional category-aware filtering.

    Ported from rag_v2/src/rag_tom_rules_v1.py — kept self-contained.
    """

    def __init__(
        self,
        data_dir: str = "./data",
        index_dir: str = "./index",
        model_name: str = "./models/bge-m3",
        use_category_filter: bool = False,
    ):
        self.data_dir = Path(data_dir)
        self.index_dir = Path(index_dir) / "tom_rules_v2"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.use_category_filter = use_category_filter

        from langchain_community.embeddings import HuggingFaceEmbeddings

        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": True},
        )

        self.store = None
        self.loaded = False

    def _load_documents(self, file_path: Path, num_samples: int = -1) -> list:
        from langchain_core.documents import Document

        documents = []
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                if 0 < num_samples <= count:
                    break
                record = json.loads(line)
                doc = Document(
                    page_content=record.get('rule_en', ''),
                    metadata={
                        'id': record['id'],
                        'title': record.get('category', ''),
                        'source': 'tom_rules_v2',
                        'category': record.get('category', ''),
                    },
                )
                documents.append(doc)
                count += 1
        return documents

    def build_index(self, force_rebuild: bool = False, num_samples: int = -1):
        from langchain_community.vectorstores import FAISS

        jsonl_file = self.data_dir / "tom_rules_v2.jsonl"
        index_path = self.index_dir / "tom_rules_v2"

        if not jsonl_file.exists():
            logger.warning("[ToMRulesV1RAG] data file %s not found", jsonl_file)
            return

        if index_path.exists() and not force_rebuild:
            logger.info("[ToMRulesV1RAG] Loading existing index from %s", index_path)
            self.store = FAISS.load_local(
                str(index_path), self.embeddings,
                allow_dangerous_deserialization=True,
            )
            self.loaded = True
            return

        documents = self._load_documents(jsonl_file, num_samples=num_samples)
        logger.info("[ToMRulesV1RAG] Loaded %d documents", len(documents))

        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]

        batch_size = 32
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            all_embeddings.extend(self.embeddings.embed_documents(batch))

        self.store = FAISS.from_embeddings(
            text_embeddings=list(zip(texts, all_embeddings)),
            embedding=self.embeddings,
            metadatas=metadatas,
        )
        self.store.save_local(str(index_path))
        logger.info("[ToMRulesV1RAG] Saved index to %s", index_path)
        self.loaded = True

    def _extract_keywords(self, text: str) -> Set[str]:
        words = text.lower().split()
        return {w for w in words if w not in STOPWORDS and len(w) > 2}

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
        if category and not CATEGORY_TO_USE_RAG.get(category, True):
            return []

        if not self.loaded:
            raise RuntimeError("Index not built. Call build_index() first.")

        if self.use_category_filter and category and category in CATEGORY_MAPPING:
            rule_category = CATEGORY_MAPPING[category]
            docs = self.store.similarity_search(query, k=top_k * 3)
            docs = [doc for doc in docs if doc.metadata['category'] == rule_category][:top_k]
        else:
            docs = self.store.similarity_search(query, k=top_k)

        results = []
        for doc in docs:
            results.append({
                'content': doc.page_content,
                'source': doc.metadata['source'],
                'category': doc.metadata['category'],
                'title': doc.metadata['title'],
                'id': doc.metadata['id'],
            })

        return self._rerank_by_keywords(results, query, top_k=top_k)

    def format_context(self, results: List[Dict], max_length: int = 1500) -> str:
        context_parts = []
        total_length = 0

        for i, result in enumerate(results, 1):
            part = f"[{i}] {result['content']}"
            if total_length + len(part) > max_length:
                break
            context_parts.append(part)
            total_length += len(part)

        return "\n".join(context_parts)


# ── RAGv2Engine facade ───────────────────────────────────────────────────────

@dataclass
class RAGv2Engine:
    """Facade over ToMRulesV1RAG for use by HarnessRuntime."""

    data_dir: str = _DEFAULT_DATA_DIR
    index_dir: str = _DEFAULT_INDEX_DIR
    model_name: str = "model/bge-m3"
    use_category_filter: bool = False
    classifier: CategoryClassifier | None = None
    use_rewritten: bool = False  # kept for backward compat, ignored

    _backend: Any = field(default=None, init=False, repr=False)
    _ready: bool = field(default=False, init=False, repr=False)

    def build_index(self, force_rebuild: bool = False, num_samples: int = -1) -> None:
        data_path = Path(self.data_dir)
        if not data_path.exists():
            logger.warning("[RAGv2] data_dir %s does not exist — running in empty mode", data_path)
            return

        self._backend = ToMRulesV1RAG(
            data_dir=self.data_dir,
            index_dir=self.index_dir,
            model_name=self.model_name,
            use_category_filter=self.use_category_filter,
        )
        self._backend.build_index(force_rebuild=force_rebuild, num_samples=num_samples)
        self._ready = self._backend.loaded

        if self._ready:
            logger.info("[RAGv2] Index ready — %d documents", self._backend.store.index.ntotal)

    def retrieve(
        self,
        query: str,
        category: str | None = None,
        top_k: int = 5,
        story: str = "",
    ) -> str:
        if not self._ready:
            return ""
        if category is None and self.classifier is not None:
            category = self.classifier.classify(query, story=story)
            logger.info("[RAGv2] Classifier predicted category: %s", category)
        results = self._backend.search(query=query, top_k=top_k, category=category)
        ctx = self._backend.format_context(results)
        if ctx:
            logger.debug("[RAGv2] Retrieved %d rules for category=%s", len(results), category)
        return ctx

    def size(self) -> int:
        if not self._ready or self._backend.store is None:
            return 0
        return self._backend.store.index.ntotal
