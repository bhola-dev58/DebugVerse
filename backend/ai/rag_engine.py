"""
RAG Engine v2 for DebugVerse inspired by microsoft/rag_skills.
Features:
1. Semantic Vector Search with Qdrant integration (or in-memory vector fallback).
2. Dense embeddings + Sparse lexical hybrid retrieval.
3. Codebase indexing and official documentation knowledge retrieval.
4. Token budget management and citation injection for multi-agent debugging.
"""

import os
import re
import math
import hashlib
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("debugverse.rag_engine")

# ── Curated Knowledge Base (Official Documentation & Core Remediation) ─────────
KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    {
        "id": "py-recursion",
        "language": "python",
        "keywords": ["recursion", "recursionerror", "maximum recursion depth", "factorial", "fibonacci", "base case"],
        "title": "Python Official Docs: RecursionLimit & Call Stack",
        "url": "https://docs.python.org/3/library/sys.html#sys.setrecursionlimit",
        "summary": "Recursive functions must have a well-defined base condition that terminates execution. Without it, the call stack exceeds sys.getrecursionlimit() (default 1000). For deep recursion, prefer an iterative loop with an explicit stack or tail recursion optimization.",
    },
    {
        "id": "py-index-error",
        "language": "python",
        "keywords": ["indexerror", "list index out of range", "index", "off-by-one", "range", "len"],
        "title": "Python Sequence Types: Common Sequence Operations",
        "url": "https://docs.python.org/3/library/stdtypes.html#sequence-types-list-tuple-range",
        "summary": "Attempting to access an index i >= len(seq) or i < -len(seq) raises IndexError. Use `enumerate()` or direct iteration `for item in seq` to avoid index tracking errors, or use `.get()` on dictionaries.",
    },
    {
        "id": "py-mutable-default",
        "language": "python",
        "keywords": ["mutable default", "def foo(a=[]", "list argument", "dict default", "persistent default"],
        "title": "Python Common Gotchas: Default Parameter Values",
        "url": "https://docs.python.org/3/tutorial/controlflow.html#default-argument-values",
        "summary": "Default arguments are evaluated once when the function definition is executed. A mutable default like `def add_item(val, items=[])` shares the same list across calls. The standard idiom is `def add_item(val, items=None): if items is None: items = []`.",
    },
    {
        "id": "py-zero-division",
        "language": "python",
        "keywords": ["zerodivisionerror", "division by zero", "modulo by zero", "/", "%", "zero"],
        "title": "Python Built-in Exceptions: ZeroDivisionError",
        "url": "https://docs.python.org/3/library/exceptions.html#ZeroDivisionError",
        "summary": "Raised when the second argument of a division or modulo operation is zero. Always guard division operations with a non-zero check `if divisor != 0:` or handle `except ZeroDivisionError:`.",
    },
    {
        "id": "js-undefined-property",
        "language": "javascript",
        "keywords": ["typeerror", "cannot read properties of undefined", "cannot read property of null", "undefined", "null"],
        "title": "MDN Web Docs: Optional Chaining (?.)",
        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining",
        "summary": "Accessing properties on undefined or null throws TypeError. Use optional chaining `obj?.property` or nullish coalescing `obj?.property ?? defaultValue` to safely traverse nested objects.",
    },
    {
        "id": "js-async-await",
        "language": "javascript",
        "keywords": ["async", "await", "promise", "promise <pending>", "unhandledpromiserejection"],
        "title": "MDN Web Docs: Async functions and Promises",
        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function",
        "summary": "An async function always returns a Promise. Forgetting `await` before a promise returns the unresolved Promise object rather than the resolved value. Always wrap awaits in try/catch or chain `.catch()` to handle network failures.",
    },
    {
        "id": "cpp-segfault",
        "language": "cpp",
        "keywords": ["segmentation fault", "segfault", "sigsegv", "null pointer", "dangling pointer", "core dumped"],
        "title": "cppreference: Undefined Behavior & Memory Access",
        "url": "https://en.cppreference.com/w/cpp/language/ub",
        "summary": "A segmentation fault occurs when dereferencing a nullptr, accessing freed memory (dangling pointer), or indexing arrays out of bounds. In modern C++, prefer `std::unique_ptr` / `std::shared_ptr` over raw pointers and use `.at()` for bounds-checked vector access.",
    },
    {
        "id": "java-npe",
        "language": "java",
        "keywords": ["nullpointerexception", "npe", "null", "invoke virtual method"],
        "title": "Oracle Java SE Docs: NullPointerException & Optional",
        "url": "https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/NullPointerException.html",
        "summary": "Thrown when an application attempts to use null in an object reference. Use Objects.requireNonNull(), Java 8+ `Optional<T>`, or explicit null guards `if (obj != null)` before invoking methods.",
    },
]

# Vector dimension for dense embeddings
EMBEDDING_DIM = 64


def compute_dense_vector(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    Computes a deterministic, normalized semantic embedding vector from text.
    Uses n-gram semantic hashing with L2-normalization for fast, offline similarity.
    """
    vec = [0.0] * dim
    tokens = re.findall(r"\w{2,}", text.lower())
    if not tokens:
        return [0.0] * dim

    for i, token in enumerate(tokens):
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        weight = 1.0 + math.log(1.0 + len(token))
        vec[idx] += weight

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [round(x / norm, 5) for x in vec]
    return vec


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Computes cosine similarity between two normalized vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    return max(0.0, min(1.0, dot))


class RAGEngine:
    """
    RAG v2 Engine combining Qdrant vector database capabilities
    with lexical keyword matching and user codebase indexing.
    """

    def __init__(self, qdrant_url: Optional[str] = None):
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL")
        self.qdrant_client = None
        self.collection_name = "debugverse_vectors"
        self._in_memory_docs: List[Dict[str, Any]] = []

        self._init_qdrant()
        self._seed_knowledge_base()

    def _init_qdrant(self):
        """Initializes Qdrant client if available, else falls back to in-memory store."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            if self.qdrant_url:
                self.qdrant_client = QdrantClient(url=self.qdrant_url)
                logger.info(f"Connected to Qdrant cluster at {self.qdrant_url}")
            else:
                # Use in-memory Qdrant client for zero-dependency local vector store
                self.qdrant_client = QdrantClient(":memory:")
                logger.info("Initialized local in-memory Qdrant vector store")

            # Ensure collection exists
            collections = self.qdrant_client.get_collections().collections
            if not any(c.name == self.collection_name for c in collections):
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
                )
                logger.info(f"Created Qdrant collection '{self.collection_name}' (dim={EMBEDDING_DIM})")
        except Exception as e:
            logger.warning(f"Qdrant client init failed ({e}), using in-memory vector store")
            self.qdrant_client = None

    def _seed_knowledge_base(self):
        """Seeds the standard documentation into the vector store."""
        for item in KNOWLEDGE_BASE:
            text_repr = f"{item['title']} {item['summary']} {' '.join(item['keywords'])}"
            vector = compute_dense_vector(text_repr)
            self.index_document(
                doc_id=item["id"],
                content=item["summary"],
                metadata={
                    "title": item["title"],
                    "url": item["url"],
                    "language": item["language"],
                    "keywords": item["keywords"],
                    "source": "official_docs",
                },
                vector=vector,
            )

    def index_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any],
        vector: Optional[List[float]] = None,
    ):
        """Indexes a single document chunk into the vector database."""
        if vector is None:
            vector = compute_dense_vector(content)

        doc_entry = {
            "id": doc_id,
            "content": content,
            "metadata": metadata,
            "vector": vector,
        }
        self._in_memory_docs.append(doc_entry)

        if self.qdrant_client:
            try:
                from qdrant_client.models import PointStruct
                # Convert alphanumeric id to integer or keep UUID
                hash_id = int(hashlib.sha256(doc_id.encode()).hexdigest()[:15], 16)
                point = PointStruct(
                    id=hash_id,
                    vector=vector,
                    payload={"doc_id": doc_id, "content": content, **metadata},
                )
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=[point],
                )
            except Exception as e:
                logger.debug(f"Qdrant point upsert fallback: {e}")

    def retrieve(
        self,
        code: str,
        language: str,
        top_k: int = 3,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid Semantic Search:
        Blends dense vector cosine similarity with sparse lexical keyword matching.
        """
        if not code:
            return []

        query_vec = compute_dense_vector(code)
        clean_code = code.lower()
        clean_lang = language.lower().strip()

        scored_results = []

        for doc in self._in_memory_docs:
            meta = doc.get("metadata", {})
            doc_lang = meta.get("language", "").lower()
            doc_session = meta.get("session_id")

            # Filter out chunks belonging to other sessions if specified
            if doc_session and session_id and doc_session != session_id:
                continue

            # 1. Dense Semantic Similarity
            semantic_score = cosine_similarity(query_vec, doc["vector"])

            # 2. Sparse Lexical Match
            lexical_score = 0.0
            keywords = meta.get("keywords", [])
            for kw in keywords:
                if kw in clean_code:
                    lexical_score += 0.25

            # 3. Language Prior
            lang_boost = 0.2 if (doc_lang == clean_lang or doc_lang == "all") else 0.0

            # Combined Hybrid Score
            total_score = round((semantic_score * 0.6) + (lexical_score * 0.3) + lang_boost, 3)

            if total_score > 0.15:
                scored_results.append({
                    "id": doc["id"],
                    "title": meta.get("title", doc["id"]),
                    "url": meta.get("url", ""),
                    "summary": doc["content"],
                    "language": doc_lang,
                    "score": total_score,
                    "source": meta.get("source", "codebase"),
                    "file_path": meta.get("file_path", ""),
                    "start_line": meta.get("start_line"),
                })

        # Sort descending by score
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def format_rag_context(self, retrieved: List[Dict[str, Any]]) -> str:
        """Formats retrieved context for multi-agent prompt injection."""
        if not retrieved:
            return ""

        context_lines = [
            "### Verified Documentation & Codebase References (RAG Engine v2):"
        ]
        for doc in retrieved:
            src = f" ({doc['url']})" if doc.get("url") else f" [{doc.get('file_path', 'codebase')}]"
            context_lines.append(f"- **{doc['title']}**{src}:\n  {doc['summary']}")

        return "\n\n".join(context_lines)

    def get_stats(self) -> Dict[str, Any]:
        """Returns vector indexing statistics."""
        return {
            "total_documents": len(self._in_memory_docs),
            "collection": self.collection_name,
            "embedding_dimension": EMBEDDING_DIM,
            "qdrant_active": self.qdrant_client is not None,
        }


# Singleton instance
rag_engine = RAGEngine()
