import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from app.pipeline.state import GapFinderState
from app.pipeline.tools.vectorstore import index_chunks
from app.config import get_settings

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=get_settings().groq_api_key,
    temperature=0.2,
)


def chunk_text(text: str, chunk_size: int = 400) -> list[str]:
    words = text.split()
    chunks = []
    step = chunk_size // 2
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def parse_node(state: GapFinderState) -> dict:
    raw_text = state.get("raw_text", "")
    file_name = state.get("file_name", "notes")
    analysis_id = state.get("analysis_id", "default")

    if not raw_text:
        return {"status": "No text found in file", "all_concepts": [], "gaps": []}

    chunks = chunk_text(raw_text)
    if chunks:
        index_chunks(chunks, analysis_id)

    text_for_llm = raw_text[:8000]
    prompt = f"""You are analyzing lecture notes or slides.

Extract ALL concepts, terms, formulas, algorithms, and technical jargon mentioned in the text below.
Return ONLY a JSON array of strings. No explanation.

Example: ["attention mechanism", "backpropagation", "gradient descent", "softmax"]

LECTURE TEXT:
{text_for_llm}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()

    try:
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        concepts = json.loads(content.strip())
    except Exception:
        concepts = [
            line.strip().strip('",[]')
            for line in content.split("\n")
            if line.strip().strip('",[]')
        ]

    return {
        "all_concepts": concepts,
        "status": f"Parsed {len(chunks)} chunks, found {len(concepts)} concepts",
        "messages": [AIMessage(content=f"Extracted {len(concepts)} concepts from {file_name}")],
    }
