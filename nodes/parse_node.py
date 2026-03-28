"""
ParseNode — Step 1
Extracts raw text from PDF, PPTX, or TXT files,
then uses the LLM to identify every concept and term mentioned.
Also chunks and indexes the text into ChromaDB.
"""
import os
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from state import GapFinderState
from tools.vectorstore import index_chunks, reset_session

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2
)


def chunk_text(text: str, chunk_size: int = 400) -> list[str]:
    """Split text into overlapping chunks for embedding."""
    words = text.split()
    chunks = []
    step = chunk_size // 2
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def extract_text_from_file(file_path: str) -> str:
    """Extract raw text from PDF, PPTX, or TXT."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text

    elif ext in (".pptx", ".ppt"):
        from pptx import Presentation
        prs = Presentation(file_path)
        lines = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    lines.append(shape.text.strip())
        return "\n".join(lines)

    else:  # .txt or anything else
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


def parse_node(state: GapFinderState) -> dict:
    """LangGraph node: parse file and extract concepts."""
    raw_text = state.get("raw_text", "")
    file_name = state.get("file_name", "notes")

    if not raw_text:
        return {"status": "❌ No text found in file", "all_concepts": [], "gaps": []}

    # Index all chunks into ChromaDB
    reset_session()
    chunks = chunk_text(raw_text)
    if chunks:
        index_chunks(chunks)

    # Use LLM to extract all concepts mentioned in the notes
    prompt = f"""You are analyzing lecture notes or slides.

Extract ALL concepts, terms, formulas, algorithms, and technical jargon mentioned in the text below.
Return ONLY a JSON array of strings. No explanation.

Example: ["attention mechanism", "backpropagation", "gradient descent", "softmax"]

LECTURE TEXT:
{raw_text[:4000]}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()

    # Parse JSON from response
    try:
        # Handle markdown code blocks
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        concepts = json.loads(content.strip())
    except Exception:
        # Fallback: extract line by line
        concepts = [
            line.strip().strip('",[]')
            for line in content.split("\n")
            if line.strip().strip('",[]')
        ]

    return {
        "all_concepts": concepts,
        "status": f"✅ Parsed {len(chunks)} chunks, found {len(concepts)} concepts",
        "messages": [AIMessage(content=f"Extracted {len(concepts)} concepts from {file_name}")]
    }
