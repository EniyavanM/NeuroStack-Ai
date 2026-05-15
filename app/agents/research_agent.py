"""Research agent — gathers structured knowledge from prompts."""

from app.agents.base import AgentResult, BaseAgent
from app.services.llm import generate_reply


class ResearchAgent(BaseAgent):
    name = "research"
    description = "Gathers knowledge and structured facts; web-ready architecture."

    async def run(self, prompt: str, context: dict | None = None) -> AgentResult:
        system = (
            "You are a research agent. Provide accurate, well-structured factual information. "
            "Use bullet points and cite logical reasoning. Flag uncertainty when needed."
        )
        output = await generate_reply(prompt, system_prompt=system)
        return AgentResult(agent_name=self.name, output=output, metadata={"type": "research"})
