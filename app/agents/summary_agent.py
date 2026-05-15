"""Summary agent — condenses long content."""

from app.agents.base import AgentResult, BaseAgent
from app.services.llm import generate_reply


class SummaryAgent(BaseAgent):
    name = "summary"
    description = "Summarizes long responses into concise takeaways."

    async def run(self, prompt: str, context: dict | None = None) -> AgentResult:
        content = context.get("content", prompt) if context else prompt
        system = "You are a summary agent. Produce a concise executive summary in 3-5 bullet points."
        output = await generate_reply(content, system_prompt=system)
        return AgentResult(agent_name=self.name, output=output, metadata={"type": "summary"})
