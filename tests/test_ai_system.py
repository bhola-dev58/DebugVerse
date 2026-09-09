"""
Automated Test Suite for DebugVerse AI Engine, RAG, and Sandbox Execution.
"""

import pytest
import os
from backend.ai import RAGEngine, ConversationMemoryManager, ModelRouter, AIProviderManager


def test_rag_engine_retrieval():
    """Verify that Python recursion code retrieves the official recursion docs."""
    engine = RAGEngine()
    code = "def factorial(n):\n    return n * factorial(n - 1)"
    results = engine.retrieve(code, "python")
    
    assert len(results) > 0, "RAG engine should return at least 1 document"
    assert results[0]["id"] == "py-recursion"
    assert results[0]["score"] > 0.2


def test_rag_javascript_optional_chaining():
    """Verify that null/undefined access triggers optional chaining docs."""
    engine = RAGEngine()
    code = "const user = null;\nconsole.log(user.name);"
    results = engine.retrieve(code, "javascript")
    
    assert len(results) > 0
    assert any("optional" in doc["title"].lower() for doc in results)


def test_conversation_buffer_memory():
    """Verify multi-turn conversational memory buffer retains dialogue."""
    manager = ConversationMemoryManager()
    memory = manager.get_or_create_memory("test-session")
    
    memory.add_turn("user", "Fix my factorial function", code_snippet="def f(n): ...")
    memory.add_turn("assistant", "Add a base condition if n <= 1: return 1")
    
    context = memory.get_formatted_context()
    assert "Fix my factorial function" in context
    assert "Add a base condition" in context
    assert len(memory.history) == 2


def test_model_router_classification():
    """Verify complexity routing correctly triages code snippets."""
    # Simple syntax / one-liner
    simple_result = ModelRouter.classify_complexity("print('hello')", "python")
    assert simple_result["tier"] == "simple"
    assert simple_result["recommended_model"] == "gemini-2-5-flash"
    
    # Complex multithreaded code
    complex_result = ModelRouter.classify_complexity(
        "import asyncio\nimport threading\nlock = threading.Lock()", "python"
    )
    assert complex_result["tier"] == "complex"
    assert complex_result["recommended_model"] == "claude-3-5-sonnet"


def test_ai_provider_manager_status():
    """Verify AI provider status reports availability correctly."""
    manager = AIProviderManager()
    status = manager.get_status()
    
    assert "bedrock" in status
    assert "gemini" in status
    assert "models" in status["bedrock"]


def test_codebase_indexer_chunking():
    """Verify codebase indexer splits code into language-aware chunks."""
    from backend.ai.codebase_indexer import CodebaseIndexer
    indexer = CodebaseIndexer()
    sample_code = """
class DataProcessor:
    def __init__(self, data):
        self.data = data

    def process(self):
        return [x * 2 for x in self.data]

    def validate(self):
        return len(self.data) > 0
"""
    chunks = indexer.chunk_source_code(sample_code, "processor.py", "python", chunk_size_lines=6, overlap_lines=2)
    assert len(chunks) > 0
    assert chunks[0]["file_path"] == "processor.py"
    assert "language" in chunks[0]


def test_security_input_sanitization():
    """Verify security sanitization strips null bytes and directory traversal."""
    from backend.middleware.security import sanitize_user_input, sanitize_filename
    
    dirty_input = "hello\x00world\x08test"
    cleaned = sanitize_user_input(dirty_input)
    assert "\x00" not in cleaned
    assert "helloworldtest" == cleaned

    dirty_file = "../../etc/passwd"
    clean_file = sanitize_filename(dirty_file)
    assert ".." not in clean_file
    assert "/" not in clean_file

