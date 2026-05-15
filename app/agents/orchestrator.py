"""Multi-agent orchestrator — routes prompts and combines outputs."""

from app.agents.analytics_agent import AnalyticsAgent
from app.agents.base import AgentResult, BaseAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.research_agent import ResearchAgent
from app.agents.summary_agent import SummaryAgent
from app.services.llm import generate_reply


class AgentOrchestrator:
    """Routes user prompts to specialized agents and synthesizes a final response."""

    def __init__(self) -> None:
        self.agents: dict[str, BaseAgent] = {
            "research": ResearchAgent(),
            "summary": SummaryAgent(),
            "memory": MemoryAgent(),
            "analytics": AnalyticsAgent(),
        }

    def _select_agents(self, prompt: str) -> list[str]:
        lower = prompt.lower()
        selected = ["memory"]
        if any(w in lower for w in ("research", "find", "explain", "what is", "how does")):
            selected.append("research")
        if any(w in lower for w in ("summarize", "summary", "tldr", "brief")):
            selected.append("summary")
        if any(w in lower for w in ("analyze", "analytics", "insight", "trend", "metric")):
            selected.append("analytics")
        if len(selected) == 1:
            selected.append("research")
        return list(dict.fromkeys(selected))

    async def run(self, prompt: str, session_id: str | None = None) -> tuple[str, list[AgentResult]]:
        context = {"session_id": session_id or "default"}
        agent_names = self._select_agents(prompt)
        results: list[AgentResult] = []

        for name in agent_names:
            agent = self.agents[name]
            if name == "summary" and results:
                ctx = {**context, "content": results[-1].output}
                result = await agent.run(prompt, context=ctx)
            else:
                result = await agent.run(prompt, context=context)
            results.append(result)

        synthesis_prompt = self._build_synthesis_prompt(prompt, results)
        final = await generate_reply(
            synthesis_prompt,
            system_prompt=(
                "You are the orchestrator. Combine agent outputs into one coherent, helpful answer."
            ),
        )
        return final, results

    def _build_synthesis_prompt(self, prompt: str, results: list[AgentResult]) -> str:
        parts = [f"User question: {prompt}\n\nAgent outputs:"]
        for r in results:
            parts.append(f"\n[{r.agent_name}]\n{r.output}")
        return "\n".join(parts)

    def list_agents(self) -> list[dict[str, str]]:
        return [{"name": a.name, "description": a.description} for a in self.agents.values()]
