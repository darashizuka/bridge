import sys
import psutil
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/debug/memory")
async def memory_debug():
    process = psutil.Process()
    mem = process.memory_info()

    top_modules = sorted(
        [(name, sys.getsizeof(mod)) for name, mod in sys.modules.items() if mod is not None],
        key=lambda x: x[1],
        reverse=True,
    )[:30]

    return {
        "rss_mb": round(mem.rss / 1024 / 1024, 1),
        "vms_mb": round(mem.vms / 1024 / 1024, 1),
        "loaded_module_count": len(sys.modules),
        "top_modules_by_size": [
            {"module": name, "size_kb": round(size / 1024, 1)}
            for name, size in top_modules
        ],
        "heavy_packages_loaded": {
            pkg: pkg in sys.modules
            for pkg in [
                "onnxruntime", "numpy", "torch", "sentence_transformers",
                "chromadb", "PIL", "fitz", "pptx", "langchain",
                "langchain_community", "langchain_core", "langgraph",
                "cryptography", "gradio",
            ]
        },
    }
