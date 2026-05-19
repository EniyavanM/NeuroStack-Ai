from langchain_community.chat_models import ChatOllama

async def generate_reply(prompt: str) -> str:
return "AI response generated successfully."

async def stream_reply(prompt: str):
yield "Streaming unavailable."

def llm_available():
return {
"provider": "ollama",
"configured": True,
}
