from langchain_groq import ChatGroq
from app.config import get_settings

_llm = None


def get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="openai/gpt-oss-20b",
            api_key=get_settings().groq_api_key,
            temperature=0.2,
            max_tokens=8000,
        )
    return _llm
