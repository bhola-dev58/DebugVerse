---
name: rag
description: Retrieval-Augmented Generation (RAG) intelligence inspired by microsoft/rag_skills. Implements semantic search, vector indexing, conversation memory buffers, context distillation, and token budgeting for intelligent code debugging and domain knowledge augmentation.
---

# RAG Skills & Architecture Guide

This skill encapsulates patterns from `microsoft/rag_skills` for building high-precision, token-efficient, and context-aware RAG pipelines in production developer platforms.

## Core RAG Components

### 1. Document Chunking & Token Budgeting
- **Chunk Size:** 500–1000 tokens for technical code documentation, with 10–15% overlap.
- **Header Metadata:** Every chunk must preserve structural metadata (`file_path`, `section_title`, `language`, `version`).
- **Token Guard:** Never exceed 40% of the target LLM's context window on retrieval context alone. Reserve 60% for reasoning and output generation.

### 2. Conversational Memory Patterns (`microsoft/rag_skills`)
- **`ConversationBufferMemory`**:
  - Retains the exact transcript of recent exchanges (ideal for short 2–5 turn debugging sessions).
  - Fast, zero token compression cost, high fidelity.
- **`ConversationSummaryMemory`**:
  - Automatically summarizes earlier conversation turns once the exchange exceeds `max_buffer_turns` (default: 4).
  - Maintains code diffs and core user intent while shrinking token overhead by ~70%.

### 3. Error Code & Documentation Retrieval
When a user submits code with an error or stack trace:
1. **Query Extraction:** Extract error message, exception type, framework, and language.
2. **Hybrid Search:** Combine lexical search (exact error code, e.g. `RecursionError`, `ERR_HTTP_HEADERS_SENT`) with dense semantic vector similarity.
3. **Context Injection:** Inject the verified fix snippet, reference link, and warning context directly into the system prompt.

### 4. Model Routing & Fallback Protocol
- **Fast Tier (Gemini 2.5 Flash / Claude 3.5 Haiku):** For syntax errors, one-liners, formatting, and high-confidence cached queries.
- **Reasoning Tier (Claude 3.5 Sonnet on AWS Bedrock):** For multi-threaded bugs, memory leaks, race conditions, and complex system architectures.
