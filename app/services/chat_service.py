"""Chat persistence and AI conversation handling."""

from collections.abc import AsyncIterator

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.user import User
from app.services.llm import generate_reply, stream_reply
from app.utils.redis_client import cache_get, cache_set


async def get_or_create_conversation(
    db: AsyncSession,
    user: User,
    conversation_id: int | None,
    first_message: str,
) -> Conversation:
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id,
            )
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv

    title = first_message[:80] + ("..." if len(first_message) > 80 else "")
    conv = Conversation(user_id=user.id, title=title)
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    return conv


async def load_history(db: AsyncSession, conversation_id: int, limit: int = 20) -> list[dict[str, str]]:
    cache_key = f"chat_history:{conversation_id}"
    cached = await cache_get(cache_key)
    if cached:
        import json

        return json.loads(cached)

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.asc())
        .limit(limit)
    )
    messages = result.scalars().all()
    history = [{"role": m.role.value, "content": m.content} for m in messages]
    if history:
        import json

        await cache_set(cache_key, json.dumps(history), ttl_seconds=600)
    return history


async def save_message(db: AsyncSession, conversation_id: int, role: MessageRole, content: str) -> Message:
    msg = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    cache_key = f"chat_history:{conversation_id}"
    await cache_set(cache_key, "[]", ttl_seconds=1)  # invalidate
    return msg


async def chat_reply(
    db: AsyncSession,
    user: User,
    message: str,
    conversation_id: int | None,
    system_prompt: str | None = None,
) -> tuple[Conversation, str]:
    conv = await get_or_create_conversation(db, user, conversation_id, message)
    history = await load_history(db, conv.id)
    await save_message(db, conv.id, MessageRole.USER, message)
    reply = await generate_reply(message, history=history, system_prompt=system_prompt)
    await save_message(db, conv.id, MessageRole.ASSISTANT, reply)
    return conv, reply


async def chat_stream(
    db: AsyncSession,
    user: User,
    message: str,
    conversation_id: int | None,
    system_prompt: str | None = None,
) -> AsyncIterator[tuple[int, str]]:
    conv = await get_or_create_conversation(db, user, conversation_id, message)
    history = await load_history(db, conv.id)
    await save_message(db, conv.id, MessageRole.USER, message)

    full_reply: list[str] = []
    async for token in stream_reply(message, history=history, system_prompt=system_prompt):
        full_reply.append(token)
        yield conv.id, token

    await save_message(db, conv.id, MessageRole.ASSISTANT, "".join(full_reply))


async def list_conversations(db: AsyncSession, user: User) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_all_history(db: AsyncSession, user: User) -> int:
    subq = select(Conversation.id).where(Conversation.user_id == user.id)
    result = await db.execute(delete(Message).where(Message.conversation_id.in_(subq)))
    await db.execute(delete(Conversation).where(Conversation.user_id == user.id))
    return result.rowcount or 0
