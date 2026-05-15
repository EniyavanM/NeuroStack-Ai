"""Multi-agent system routes."""

from fastapi import APIRouter

from app.agents.orchestrator import AgentOrchestrator
from app.core.dependencies import CurrentUser
from app.schemas.common import APIResponse, success_response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/agents", tags=["Multi-Agent"])
orchestrator = AgentOrchestrator()


class AgentRunRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    session_id: str | None = None


@router.get("/list", response_model=APIResponse)
async def list_agents(_: CurrentUser):
    return success_response(data=orchestrator.list_agents())


@router.post("/run", response_model=APIResponse)
async def run_agents(payload: AgentRunRequest, current_user: CurrentUser):
    session_id = payload.session_id or f"user_{current_user.id}"
    final, results = await orchestrator.run(payload.prompt, session_id=session_id)
    return success_response(
        data={
            "final_response": final,
            "agents": [
                {"name": r.agent_name, "output": r.output, "metadata": r.metadata}
                for r in results
            ],
        },
        message="Multi-agent run complete",
    )
