# Bridge — Frontend

```bash
npm install
cp .env.example .env.local
# Fill in Clerk keys and API URL
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the app.

## What This Does

The frontend for Bridge, a lecture gap finder. Students upload lecture notes (PDF, PPTX, or TXT) and the app identifies concepts that are mentioned but never explained. Results include a study guide, an interactive concept dependency graph, and a flashcard quiz.

Key pages:
- `/` — Landing page with sign-in/sign-up
- `/dashboard` — Upload notes and view analysis history
- `/dashboard/analysis/[id]` — Results view with study guide, concept map, and flashcards

Built with Next.js 16 (App Router), React 19, Tailwind CSS 4, Clerk for auth, and React Flow for the dependency graph. Connects to a FastAPI backend that runs the LangGraph analysis pipeline.
