"""Base agent interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AgentResult:
    agent_name: str
    output: str
    metadata: dict | None = None


class BaseAgent(ABC):
    name: str = "base"
    description: str = ""

    @abstractmethod
    async def run(self, prompt: str, context: dict | None = None) -> AgentResult:
        pass
