import json
import re
from langchain_core.messages import HumanMessage, AIMessage
from app.pipeline.state import GapFinderState
from app.pipeline.llm import get_llm


def _extract_json(text: str):
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        return json.loads(text.strip())
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text.strip())


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

    text_for_llm = raw_text[:8000]
    prompt = f"""You are analyzing lecture notes or slides.

Extract ALL concepts, terms, formulas, algorithms, and technical jargon mentioned in the text below.
Return ONLY a JSON array of strings. No explanation.

Example: ["attention mechanism", "backpropagation", "gradient descent", "softmax"]

LECTURE TEXT:
{text_for_llm}
"""
    response = get_llm().invoke([HumanMessage(content=prompt)])
    content = response.content.strip()

    try:
        concepts = _extract_json(content)
    except Exception:
        concepts = [c.strip() for c in re.findall(r'"([^"]+)"', content)]

    return {
        "all_concepts": concepts,
        "status": f"Parsed {len(chunks)} chunks, found {len(concepts)} concepts",
        "messages": [AIMessage(content=f"Extracted {len(concepts)} concepts from {file_name}")],
    }
