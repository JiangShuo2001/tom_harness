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
