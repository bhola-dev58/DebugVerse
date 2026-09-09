"""
Codebase Indexer for DebugVerse.
Parses user codebases, chunks source files using language-aware sliding windows,
and indexes semantic vectors into the RAG Engine for contextual debugging.
"""

import os
import re
import uuid
import logging
from typing import List, Dict, Any, Optional

try:
    from backend.ai.rag_engine import rag_engine, compute_dense_vector
except ImportError:
    from ai.rag_engine import rag_engine, compute_dense_vector

logger = logging.getLogger("debugverse.codebase_indexer")

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".go": "go",
    ".rs": "rust",
}

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    ".agents",
    ".system_generated",
}


class CodebaseIndexer:
    """
    Scans files, chunks source code, and upserts semantic embeddings into the RAG vector index.
    """

    def __init__(self, engine=None):
        self.engine = engine or rag_engine

    def chunk_source_code(
        self,
        content: str,
        file_path: str,
        language: str,
        chunk_size_lines: int = 35,
        overlap_lines: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Splits source code into overlapping chunks preserving line number metadata.
        """
        lines = content.splitlines()
        if not lines:
            return []

        chunks = []
        step = max(1, chunk_size_lines - overlap_lines)

        for i in range(0, len(lines), step):
            window = lines[i : i + chunk_size_lines]
            chunk_text = "\n".join(window)
            start_line = i + 1
            end_line = min(len(lines), i + len(window))

            # Detect primary symbol in chunk (function or class definition)
            symbol_match = re.search(r"^\s*(?:def|class|function|async\s+def)\s+([A-Za-z0-9_]+)", chunk_text, re.MULTILINE)
            symbol_name = symbol_match.group(1) if symbol_match else os.path.basename(file_path)

            chunks.append({
                "content": chunk_text,
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "symbol": symbol_name,
                "language": language,
            })

        return chunks

    def index_single_file(
        self,
        file_path: str,
        content: str,
        session_id: Optional[str] = None,
    ) -> int:
        """
        Indexes a single file's content into the RAG engine.
        Returns the number of chunks indexed.
        """
        ext = os.path.splitext(file_path)[1].lower()
        language = SUPPORTED_EXTENSIONS.get(ext, "text")

        chunks = self.chunk_source_code(content, file_path, language)
        for c in chunks:
            chunk_id = f"chunk-{uuid.uuid4().hex[:8]}"
            metadata = {
                "title": f"{c['file_path']} (L{c['start_line']}-{c['end_line']})",
                "file_path": c["file_path"],
                "start_line": c["start_line"],
                "end_line": c["end_line"],
                "symbol": c["symbol"],
                "language": c["language"],
                "keywords": [c["symbol"].lower(), os.path.basename(c["file_path"]).lower()],
                "session_id": session_id,
                "source": "user_codebase",
            }
            self.engine.index_document(
                doc_id=chunk_id,
                content=c["content"],
                metadata=metadata,
            )

        logger.info(f"Indexed {len(chunks)} chunks for file: {file_path}")
        return len(chunks)

    def index_directory(
        self,
        root_dir: str,
        session_id: Optional[str] = None,
        max_files: int = 100,
    ) -> Dict[str, Any]:
        """
        Walks a local directory and indexes all supported source files.
        """
        total_files = 0
        total_chunks = 0

        for root, dirs, files in os.walk(root_dir):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in SUPPORTED_EXTENSIONS:
                    if total_files >= max_files:
                        break
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_dir)
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        chunks_count = self.index_single_file(rel_path, content, session_id=session_id)
                        total_chunks += chunks_count
                        total_files += 1
                    except Exception as e:
                        logger.warning(f"Error reading file {full_path}: {e}")

        return {
            "indexed_files": total_files,
            "indexed_chunks": total_chunks,
            "session_id": session_id,
        }


# Singleton indexer
codebase_indexer = CodebaseIndexer()
