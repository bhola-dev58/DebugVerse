"""
Agent Orchestrator for DebugVerse.
Coordinates parallel execution of 4 specialized AI agents:
  1. Security Auditor (OWASP, injections, secret leaks)
  2. Performance Profiler (Big-O, memory, hotspots)
  3. Test Generator (pytest, Jest, edge cases)
  4. Root Cause Explainer (deep diagnostic, diffs, lessons)

Streams all events concurrently via an async queue to WebSockets or SSE.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable, Awaitable

from backend.agents.security_agent import SecurityAgent
from backend.agents.performance_agent import PerformanceAgent
from backend.agents.test_generator_agent import TestGeneratorAgent
from backend.agents.explain_agent import ExplainAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates parallel execution and real-time streaming of all 4 agents."""

    def __init__(self, provider_manager=None):
        self.agents = [
            ExplainAgent(provider_manager),
            SecurityAgent(provider_manager),
            PerformanceAgent(provider_manager),
            TestGeneratorAgent(provider_manager),
        ]
        self.agent_map = {agent.agent_id: agent for agent in self.agents}

    def get_agent_metadata(self) -> List[Dict[str, Any]]:
        """Return catalog of available agents for UI setup."""
        return [
            {
                "id": agent.agent_id,
                "name": agent.display_name,
                "description": agent.description,
                "model_preference": agent.model_preference,
            }
            for agent in self.agents
        ]

    async def stream_all_parallel(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        selected_agents: Optional[List[str]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Concurrently executes agents and yields events in real-time as they arrive.
        Yields typed events:
          - {"type": "session_init", "agents": [...]}
          - {"agent": agent_id, "type": "start|chunk|complete|error", ...}
          - {"type": "all_complete", "summary": {...}}
        """
        active_agents = (
            [self.agent_map[aid] for aid in selected_agents if aid in self.agent_map]
            if selected_agents
            else self.agents
        )

        yield {
            "type": "session_init",
            "active_agents": [
                {"id": a.agent_id, "name": a.display_name, "description": a.description}
                for a in active_agents
            ],
            "total_agents": len(active_agents),
        }

        queue: asyncio.Queue = asyncio.Queue()
        pending_agents = len(active_agents)

        async def _run_single_agent(agent):
            try:
                async for event in agent.run(code, language, context):
                    await queue.put(event)
            except Exception as e:
                logger.error(f"Unhandled error in agent {agent.agent_id}: {e}", exc_info=True)
                await queue.put({
                    "agent": agent.agent_id,
                    "type": "error",
                    "message": str(e),
                })
            finally:
                await queue.put({"agent": agent.agent_id, "type": "_agent_finished"})

        # Spawn all agent worker tasks concurrently
        tasks = [asyncio.create_task(_run_single_agent(agent)) for agent in active_agents]

        # Consume from the shared queue until all agents are finished
        while pending_agents > 0:
            event = await queue.get()
            if event.get("type") == "_agent_finished":
                pending_agents -= 1
            else:
                yield event
            queue.task_done()

        # Ensure all tasks are gathered cleanly
        await asyncio.gather(*tasks, return_exceptions=True)

        yield {
            "type": "all_complete",
            "status": "success",
            "completed_agents": [a.agent_id for a in active_agents],
        }
        yield {
            "type": "pipeline_complete",
            "status": "done",
            "completed_agents": [a.agent_id for a in active_agents],
        }

    async def broadcast_to_websocket(
        self,
        websocket,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        selected_agents: Optional[List[str]] = None,
    ):
        """Streams events directly into an open FastAPI WebSocket."""
        async for event in self.stream_all_parallel(code, language, context, selected_agents):
            await websocket.send_json(event)
