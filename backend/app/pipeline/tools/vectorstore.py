import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

_embedding_fn = None
_chroma_client = None


def _get_embedding_fn():
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    return _embedding_fn


def _get_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.Client()
    return _chroma_client


def get_collection(analysis_id: str):
    client = _get_client()
    return client.get_or_create_collection(
        name=f"bridge_{analysis_id[:32]}",
        embedding_function=_get_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )


def index_chunks(chunks: list[str], analysis_id: str):
    collection = get_collection(analysis_id)
    collection.add(
        documents=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))],
    )


def is_concept_explained(concept: str, analysis_id: str, threshold: float = 0.75) -> tuple[bool, str]:
    collection = get_collection(analysis_id)
    if collection.count() == 0:
        return False, ""

    results = collection.query(
        query_texts=[f"what is {concept} and how does it work"],
        n_results=min(3, collection.count()),
        include=["documents", "distances"],
    )

    docs = results["documents"][0]
    distances = results["distances"][0]

    for doc, dist in zip(docs, distances):
        similarity = 1 - dist
        if similarity >= threshold:
            return True, doc

    return False, ""


def cleanup_collection(analysis_id: str):
    try:
        _get_client().delete_collection(f"bridge_{analysis_id[:32]}")
    except Exception:
        pass
