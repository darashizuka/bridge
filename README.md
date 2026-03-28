---
title: Lecture Gap Finder
emoji: 🎓
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
---

# Lecture Gap Finder

Upload your lecture slides or paste notes — AI finds what's missing and fills the gaps.

## Pipeline
1. **Parse** — Extract text from PDF / PPTX / TXT
2. **Detect Gaps** — Find concepts mentioned but never explained
3. **Prioritize** — Rank gaps by importance (high / medium / low)
4. **Fill via MCP** — Web search each gap using a custom MCP server
5. **Map Dependencies** — Build a concept dependency graph
6. **Study Guide** — Generate structured markdown study guide + flashcards

## Stack
- **LangGraph** — Orchestrates the multi-step pipeline
- **Groq (Llama 3.3 70B)** — LLM for concept extraction, gap detection, synthesis
- **MCP + DuckDuckGo** — Custom MCP server for real-time web search
- **ChromaDB** — In-memory vector store for semantic gap detection
- **Sentence Transformers** — Embeddings for ChromaDB
- **Gradio** — UI

## Setup (local)
```bash
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY to .env
python app.py
```
