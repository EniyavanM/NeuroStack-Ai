"""LangChain LLM factory — Ollama only."""

from collections.abc import AsyncIterator
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
AIMessage,
BaseMessage,
HumanMessage,
SystemMessage,
)

from langchain_community.chat_models import ChatOllama

from app.core.config import Settings, get_settings

def get_chat_model(settings: Settings | None = None) -> BaseChatModel:
settings = settings or get_settings()

```
return ChatOllama(
    base_url=settings.ollama_base_url,
    model=settings.ollama_model,
    temperature=0.7,
)
```

def to_langchain_messages(
history: list[dict[str, str]]
) -> list[BaseMessage]:

```
messages: list[BaseMessage] = []

for item in history:

    role = item.get("role", "user")
    content = item.get("content", "")

    if role == "assistant":
        messages.append(AIMessage(content=content))

    elif role == "system":
        messages.append(SystemMessage(content=content))

    else:
        messages.append(HumanMessage(content=content))

return messages
```

async def generate_reply(
prompt: str,
history: list[dict[str, str]] | None = None,
system_prompt: str | None = None,
) -> str:

```
try:

    model = get_chat_model()

    messages: list[BaseMessage] = []

    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))

    if history:
        messages.extend(to_langchain_messages(history))

    messages.append(HumanMessage(content=prompt))

    response = await model.ainvoke(messages)

    return str(response.content)

except Exception:
    return "AI service unavailable in deployment environment."
```

async def stream_reply(
prompt: str,
history: list[dict[str, str]] | None = None,
system_prompt: str | None = None,
) -> AsyncIterator[str]:

```
try:

    model = get_chat_model()

    messages: list[BaseMessage] = []

    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))

    if history:
        messages.extend(to_langchain_messages(history))

    messages.append(HumanMessage(content=prompt))

    async for chunk in model.astream(messages):

        if chunk.content:
            yield str(chunk.content)

except Exception:
    yield "AI streaming unavailable."
```

def llm_available(
settings: Settings | None = None
) -> dict[str, Any]:

```
settings = settings or get_settings()

return {
    "provider": "ollama",
    "configured": True,
}
```
