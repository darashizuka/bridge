# Bridge

Full-stack app that finds knowledge gaps in lecture notes and helps students fill them. Upload PDF, PPTX, or TXT files — the AI pipeline detects concepts that are mentioned but never explained, searches the web for explanations, and generates a study guide, dependency graph, and flashcard deck.

**Live:** [bridge-ten-pied.vercel.app](https://bridge-ten-pied.vercel.app)

## How It Works

The backend runs a six-stage LangGraph pipeline:

1. **Parse** — Extract text from uploaded files (PDF, PPTX, TXT)
2. **Detect Gaps** — LLM identifies concepts mentioned but not adequately explained
3. **Prioritize** — Rank gaps by severity (high / medium / low)
4. **Fill** — Search the web for each gap using a custom MCP server, then synthesize explanations
5. **Connect** — Build a concept dependency graph
6. **Output** — Generate a structured study guide and flashcards

Progress streams to the frontend in real time via SSE.

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, Tailwind CSS 4 |
| Auth | Clerk |
| Backend | FastAPI, LangGraph, LangChain |
| LLM | Groq |
| Search | Custom MCP server (DuckDuckGo) |
| Database | PostgreSQL (Neon), async SQLAlchemy |
| Graph Viz | React Flow, dagre auto-layout |
| Deployment | Vercel (frontend), Render (backend) |

## Local Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Fill in GROQ_API_KEY, DATABASE_URL, CLERK_JWKS_URL
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Fill in NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY, CLERK_SECRET_KEY
npm run dev
```

## Environment Variables

### Backend (Render)
- `DATABASE_URL` — PostgreSQL connection string (`postgresql+asyncpg://...?ssl=require`)
- `GROQ_API_KEY` — Groq API key
- `CLERK_JWKS_URL` — Clerk JWKS endpoint for JWT verification
- `ALLOWED_ORIGINS` — Comma-separated allowed CORS origins

### Frontend (Vercel)
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` — Clerk publishable key
- `CLERK_SECRET_KEY` — Clerk secret key
- `NEXT_PUBLIC_API_URL` — Backend API base URL
