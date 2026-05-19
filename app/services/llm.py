from langchain_community.chat_models import ChatOllama

async def generate_reply(prompt: str) -> str:
try:
llm = ChatOllama(
model="llama3",
base_url="http://localhost:11434",
temperature=0.7,
)

```
    response = await llm.ainvoke(prompt)

    return str(response.content)

except Exception:
    return "AI service unavailable."
```

async def stream_reply(prompt: str):
yield "Streaming unavailable."

def llm_available():
return {
"provider": "ollama",
"configured": True,
}
