"""Analytics agent — generates insights from data or text."""

from app.agents.base import AgentResult, BaseAgent
from app.services.llm import generate_reply


class AnalyticsAgent(BaseAgent):
    name = "analytics"
    description = "Generates insights, trends, and actionable recommendations."

    async def run(self, prompt: str, context: dict | None = None) -> AgentResult:
        system = (
            "You are an analytics agent. Identify patterns, metrics, risks, and opportunities. "
            "Present insights with clear headings and actionable recommendations."
        )
        output = await generate_reply(prompt, system_prompt=system)
        return AgentResult(agent_name=self.name, output=output, metadata={"type": "analytics"})
