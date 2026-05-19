from langchain_community.chat_models import ChatOllama

async def generate_reply(prompt: str) -> str:
<<<<<<< HEAD
return "AI response generated successfully."

async def stream_reply(prompt: str):
yield "Streaming unavailable."

=======
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

>>>>>>> 933a6a626182219c3b8de9c3cbc3bf404dd35c10
def llm_available():
return {
"provider": "ollama",
"configured": True,
}
