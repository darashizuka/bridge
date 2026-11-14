import sys
import psutil
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import engine, Base
from app.routers import analyses, flashcards, health


def _log_memory(label: str):
    mem = psutil.Process().memory_info()
    mods = len(sys.modules)
    heavy = {p: p in sys.modules for p in [
        "onnxruntime", "numpy", "torch", "PIL", "fitz",
        "langchain_community", "langchain", "cryptography",
    ]}
    loaded = [k for k, v in heavy.items() if v]
    print(f"[MEMORY] {label}: RSS={mem.rss // 1024 // 1024}MB | "
          f"modules={mods} | heavy={loaded}", flush=True)


_log_memory("after imports")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _log_memory("lifespan start")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    _log_memory("lifespan ready")
    yield
    await engine.dispose()


app = FastAPI(title="Bridge API", version="1.0.0", lifespan=lifespan)

settings = get_settings()
origins = [o.strip() for o in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(analyses.router, prefix="/api/v1", tags=["analyses"])
app.include_router(flashcards.router, prefix="/api/v1", tags=["flashcards"])
