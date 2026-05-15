"""Chat and conversation routes."""

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agents.orchestrator import AgentOrchestrator
from app.core.dependencies import CurrentUser, DbSession
from app.schemas.chat import ChatRequest
from app.schemas.common import APIResponse, success_response
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])
orchestrator = AgentOrchestrator()


@router.post("/stream")
async def chat_stream_endpoint(payload: ChatRequest, current_user: CurrentUser, db: DbSession):
    """Server-Sent Events streaming chat."""
    return await _stream_chat(payload, current_user, db)


@router.post("", response_model=APIResponse)
async def chat(payload: ChatRequest, current_user: CurrentUser, db: DbSession):
    if payload.use_agents:
        session_id = f"user_{current_user.id}_conv_{payload.conversation_id or 'new'}"
        reply, agent_results = await orchestrator.run(payload.message, session_id=session_id)
        conv = await chat_service.get_or_create_conversation(
            db, current_user, payload.conversation_id, payload.message
        )
        from app.models.message import MessageRole

        await chat_service.save_message(db, conv.id, MessageRole.USER, payload.message)
        await chat_service.save_message(db, conv.id, MessageRole.ASSISTANT, reply)
        return success_response(
            data={
                "conversation_id": conv.id,
                "reply": reply,
                "agent_used": [r.agent_name for r in agent_results],
            },
            message="Agent orchestration complete",
        )

    conv, reply = await chat_service.chat_reply(
        db, current_user, payload.message, payload.conversation_id
    )
    return success_response(
        data={"conversation_id": conv.id, "reply": reply, "agent_used": None},
        message="Chat response generated",
    )


async def _stream_chat(payload: ChatRequest, current_user: CurrentUser, db: DbSession):
    async def event_generator():
        async for conv_id, token in chat_service.chat_stream(
            db, current_user, payload.message, payload.conversation_id
        ):
            chunk = {"conversation_id": conv_id, "token": token}
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history", response_model=APIResponse)
async def chat_history(current_user: CurrentUser, db: DbSession):
    conversations = await chat_service.list_conversations(db, current_user)
    data = []
    for conv in conversations:
        data.append(
            {
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "messages": [
                    {
                        "id": m.id,
                        "role": m.role.value,
                        "content": m.content,
                        "timestamp": m.timestamp.isoformat(),
                    }
                    for m in conv.messages
                ],
            }
        )
    return success_response(data=data, message="Chat history retrieved")


@router.delete("/history", response_model=APIResponse)
async def delete_history(current_user: CurrentUser, db: DbSession):
    count = await chat_service.delete_all_history(db, current_user)
    return success_response(data={"deleted": count}, message="Chat history cleared")
