"""Memory agent — maintains conversational context."""

from app.agents.base import AgentResult, BaseAgent
from app.services.llm import generate_reply
from app.utils.redis_client import cache_get, cache_set


class MemoryAgent(BaseAgent):
    name = "memory"
    description = "Stores and recalls conversational context."

    async def run(self, prompt: str, context: dict | None = None) -> AgentResult:
        session_id = (context or {}).get("session_id", "default")
        key = f"agent_memory:{session_id}"
        prior = await cache_get(key) or ""
        system = (
            "You are a memory agent. Update the running context with key facts from the user message. "
            "Return a compact memory block (max 500 words)."
        )
        combined = f"Prior memory:\n{prior}\n\nNew message:\n{prompt}"
        output = await generate_reply(combined, system_prompt=system)
        await cache_set(key, output, ttl_seconds=86400)
        return AgentResult(agent_name=self.name, output=output, metadata={"session_id": session_id})
