"""
ChromaDB vector store wrapper.
Stores all concepts extracted from the lecture notes.
Used by GapDetectNode to check if a concept is explained.
"""
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

_client = None
_collection = None


def get_collection(session_id: str = "default"):
    """Return (or create) a ChromaDB collection for this session."""
    global _client, _collection

    if _client is None:
        _client = chromadb.Client()  # In-memory for session

    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    _collection = _client.get_or_create_collection(
        name=f"lecture_{session_id}",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )
    return _collection


def index_chunks(chunks: list[str], session_id: str = "default"):
    """Embed and store text chunks from the lecture notes."""
    collection = get_collection(session_id)
    collection.add(
        documents=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )


def is_concept_explained(concept: str, session_id: str = "default", threshold: float = 0.75) -> tuple[bool, str]:
    """
    Query ChromaDB: is this concept actually explained in the notes?
    Returns (is_explained, best_matching_snippet)
    """
    collection = get_collection(session_id)

    if collection.count() == 0:
        return False, ""

    results = collection.query(
        query_texts=[f"what is {concept} and how does it work"],
        n_results=min(3, collection.count()),
        include=["documents", "distances"]
    )

    docs = results["documents"][0]
    distances = results["distances"][0]

    # Distance < (1 - threshold) means high similarity in cosine space
    for doc, dist in zip(docs, distances):
        similarity = 1 - dist
        if similarity >= threshold:
            return True, doc

    return False, ""


def reset_session(session_id: str = "default"):
    """Clear collection for a new upload."""
    global _client
    if _client:
        try:
            _client.delete_collection(f"lecture_{session_id}")
        except Exception:
            pass
