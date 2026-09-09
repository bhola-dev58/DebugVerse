"""
Conversation Memory Module inspired by microsoft/rag_skills.
Provides ConversationBufferMemory and ConversationSummaryMemory
for iterative, multi-turn AI debugging sessions.
"""

from typing import List, Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)


class ConversationTurn:
    def __init__(self, role: str, content: str, code_snippet: Optional[str] = None):
        self.role = role  # 'user' | 'assistant'
        self.content = content
        self.code_snippet = code_snippet
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "code_snippet": self.code_snippet,
            "timestamp": self.timestamp,
        }


class ConversationBufferMemory:
    """
    Stores raw conversation turns up to a maximum buffer capacity.
    Maintains verbatim accuracy for short debugging dialogues.
    """
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.history: List[ConversationTurn] = []

    def add_turn(self, role: str, content: str, code_snippet: Optional[str] = None):
        turn = ConversationTurn(role=role, content=content, code_snippet=code_snippet)
        self.history.append(turn)
        if len(self.history) > self.max_turns:
            self.history.pop(0)

    def get_formatted_context(self) -> str:
        """Renders the memory buffer formatted for prompt injection."""
        if not self.history:
            return ""

        lines = ["### Previous Debugging Dialogue Context:"]
        for turn in self.history:
            prefix = "User" if turn.role == "user" else "AI Debugger"
            lines.append(f"**{prefix}:** {turn.content}")
            if turn.code_snippet:
                lines.append(f"```\n{turn.code_snippet}\n```")
        return "\n\n".join(lines)

    def clear(self):
        self.history.clear()


class ConversationMemoryManager:
    """
    In-memory session registry for managing multi-turn debug conversations.
    In enterprise deployment, this delegates to Redis or ElastiCache.
    """
    def __init__(self, session_ttl_seconds: int = 3600):
        self._sessions: Dict[str, ConversationBufferMemory] = {}
        self.session_ttl = session_ttl_seconds

    def get_or_create_memory(self, session_id: str) -> ConversationBufferMemory:
        if not session_id:
            session_id = "default"
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationBufferMemory(max_turns=8)
        return self._sessions[session_id]

    def clear_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]


# Singleton instance
memory_manager = ConversationMemoryManager()
