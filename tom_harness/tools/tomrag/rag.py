#!/usr/bin/env python3
"""RAG retrieval system for social norms and commonsense knowledge using LangChain."""

import json
from pathlib import Path
from typing import List, Dict, Optional

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings
from tqdm import tqdm


class ToMRAG:
    """RAG system for retrieving social norms and commonsense knowledge."""

    def __init__(
        self,
        data_dir: str = "./data",
        index_dir: str = "./index",
        model_name: str = "./models/bge-m3",
        trust_index: bool = True,
    ):
        """Initialize RAG system.

        Args:
            data_dir: Directory containing JSONL files
            index_dir: Directory to store FAISS indices
            model_name: HuggingFace embedding model name
            trust_index: Allow deserialization of FAISS index (set False for untrusted dirs)
        """
        self.data_dir = Path(data_dir)
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.trust_index = trust_index

        # Initialize embeddings
        # bge-m3 uses encode_kwargs for retrieval normalization
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": True},
        )

        # Vector stores for each source
        self.stores = {}
        self.loaded = False

    def _load_jsonl(self, file_path: Path, num_samples: int = -1) -> List[Document]:
        """Load JSONL file and convert to LangChain Documents.

        Args:
            file_path: Path to JSONL file
            num_samples: Number of samples to load. -1 or "all" means load all.
        """
        documents = []
        count = 0

        # Count total lines for progress bar only when loading all samples
        total_lines = None
        if num_samples <= 0:
            with open(file_path, 'r', encoding='utf-8') as f_count:
                total_lines = sum(1 for _ in f_count)
        else:
            total_lines = num_samples

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in tqdm(f, total=total_lines, desc=f"Loading {file_path.stem}", unit="doc"):
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
                        'category': record['category'],
                        **record.get('metadata', {})
                    }
                )
                documents.append(doc)
                count += 1
        return documents

    def build_index(self, force_rebuild: bool = False, num_samples: int = -1):
        """Build FAISS indices for all data sources.

        Args:
            force_rebuild: If True, rebuild indices even if they exist
            num_samples: Number of samples per source to index. -1 means all samples.
        """
        sources = ['atomic', 'social_chem', 'normbank']

        for source in sources:
            jsonl_file = self.data_dir / f"{source}.jsonl"
            index_path = self.index_dir / source

            if not jsonl_file.exists():
                print(f"Warning: {jsonl_file} not found, skipping {source}")
                continue

            # Check if index exists
            if index_path.exists() and not force_rebuild:
                print(f"Loading existing index for {source} from {index_path}")
                # allow_dangerous_deserialization is required by FAISS.load_local;
                # index_dir is trusted (locally built or checked-in).
                if not self.trust_index:
                    raise RuntimeError(
                        f"Refusing to load FAISS index from {index_path} — "
                        "set trust_index=True if you trust this directory."
                    )
                self.stores[source] = FAISS.load_local(
                    str(index_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                continue

            # Load documents
            documents = self._load_jsonl(jsonl_file, num_samples=num_samples)
            print(f"Loaded {len(documents)} documents from {source}")

            # Embed documents with progress bar
            print(f"Embedding documents for {source}...")
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]

            # Embed in batches with progress tracking
            batch_size = 32
            all_embeddings = []
            for i in tqdm(range(0, len(texts), batch_size), desc=f"Embedding {source}", unit="batch"):
                batch_texts = texts[i:i+batch_size]
                batch_embeddings = self.embeddings.embed_documents(batch_texts)
                all_embeddings.extend(batch_embeddings)

            # Create FAISS index from embeddings
            print(f"Building FAISS index for {source}...")
            store = FAISS.from_embeddings(
                text_embeddings=list(zip(texts, all_embeddings)),
                embedding=self.embeddings,
                metadatas=metadatas
            )
            store.save_local(str(index_path))
            self.stores[source] = store
            print(f"Saved index to {index_path}")

        self.loaded = True

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_filter: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Search for relevant documents.

        Args:
            query: Search query
            top_k: Number of results per source
            source_filter: List of sources to search (None = all)

        Returns:
            List of result dicts with content and metadata
        """
        if not self.loaded:
            raise RuntimeError("Index not built. Call build_index() first.")

        sources = source_filter or list(self.stores.keys())
        results = []

        for source in sources:
            if source not in self.stores:
                continue

            store = self.stores[source]
            docs = store.similarity_search(query, k=top_k)

            for doc in docs:
                results.append({
                    'content': doc.page_content,
                    'source': doc.metadata['source'],
                    'category': doc.metadata['category'],
                    'title': doc.metadata['title'],
                    'id': doc.metadata['id'],
                    'metadata': {k: v for k, v in doc.metadata.items()
                                if k not in ['source', 'category', 'title', 'id']}
                })

        return results

    def format_context(self, results: List[Dict], max_length: int = 2000) -> str:
        """Format search results as context for LLM prompt.

        Args:
            results: List of search results
            max_length: Maximum length of formatted context

        Returns:
            Formatted context string
        """
        context_parts = []
        total_length = 0

        for i, result in enumerate(results, 1):
            part = f"[{i}] ({result['source']}/{result['category']}) {result['title']}\n{result['content']}"
            part_length = len(part)

            if total_length + part_length > max_length:
                break

            context_parts.append(part)
            total_length += part_length

        return "\n\n".join(context_parts)


if __name__ == "__main__":
    # Example usage
    rag = ToMRAG()

    # Build index with 50 samples per source (for testing)
    # Use num_samples=-1 or omit to index all data
    rag.build_index(num_samples=-1)

    # Test query
    query = "Ah Ming, Xiao Hua, and Xiao Yao are good friends, they often go out together. This time, Ah Ming has an idea, he wants to go out alone with Xiao Hua. So, when discussing the next travel plan, Ah Ming brings out a detailed itinerary, the itinerary deliberately avoids the places Xiao Yao loves to go. Then, Ah Ming looks at Xiao Hua, he blinks. Xiao Hua looks at Ah Ming, his expression is quite serious, and he cautiously says he hopes everyone can participate in the next trip. Xiao Yao watches the interaction between the two. What do you think Xiao Yao thinks?\n\nA. Xiao Yao feels relieved, he thinks Xiao Hua always considers him when planning.\nB. Xiao Yao is very happy, he thinks Ah Ming already makes the plan and actively invites everyone to participate.\nC. Xiao Yao feels nervous because he is not ready to join this trip.\nD. Xiao Yao doesn't care, they are just having a friendly exchange, it has no impact on the plan to travel together.\n\nChoose the most likely answer from the 4 options above. Output only the answer letter (e.g. A, B, C, D)."
    results = rag.search(query, top_k=3)

    print(f"\nQuery: {query}")
    print(f"Found {len(results)} results:\n")

    for i, result in enumerate(results, 1):
        print(f"[{i}] {result['source']}/{result['category']}")
        print(f"    Title: {result['title']}")
        print(f"    Content: {result['content'][:100]}...")
        print()
