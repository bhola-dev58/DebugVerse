"""
Base Agent class for DebugVerse Multi-Agent Pipeline.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all specialized debugging agents.
    Every agent streams typed event dictionaries through an async generator.
    """

    agent_id: str = "base"
    display_name: str = "Base Agent"
    description: str = "Base agent"
    model_preference: str = "auto"

    def __init__(self, provider_manager=None):
        from backend.ai.providers import AIProviderManager
        self.providers = provider_manager or AIProviderManager()

    @abstractmethod
    def build_system_prompt(self, language: str) -> str:
        """Construct the specialized system prompt for this agent."""
        pass

    @abstractmethod
    def build_user_prompt(self, code: str, language: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Construct the prompt sent to the LLM."""
        pass

    async def run(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute agent reasoning and yield stream events.
        Events format:
          - {"agent": agent_id, "type": "start", "name": display_name}
          - {"agent": agent_id, "type": "chunk", "text": "..."}
          - {"agent": agent_id, "type": "complete", "full_text": "...", "model": "..."}
          - {"agent": agent_id, "type": "error", "message": "..."}
        """
        yield {
            "agent": self.agent_id,
            "type": "start",
            "name": self.display_name,
            "description": self.description,
        }

        system_prompt = self.build_system_prompt(language)
        user_prompt = self.build_user_prompt(code, language, context)

        full_content = []
        model_name = "AI Model"

        try:
            async for chunk in self.providers.stream_debug(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model_preference=self.model_preference,
            ):
                token = chunk.get("token", "")
                if chunk.get("model"):
                    model_name = chunk["model"]

                if token:
                    full_content.append(token)
                    yield {
                        "agent": self.agent_id,
                        "type": "chunk",
                        "text": token,
                    }

            complete_text = "".join(full_content)
            yield {
                "agent": self.agent_id,
                "type": "complete",
                "full_text": complete_text,
                "model": model_name,
            }

        except Exception as e:
            logger.error(f"Agent {self.agent_id} failed: {e}", exc_info=True)
            yield {
                "agent": self.agent_id,
                "type": "error",
                "message": f"Agent {self.display_name} encountered an error: {str(e)}",
            }
