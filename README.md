# Cocktail Recommendation System

A dual-sided (B2C/B2B) AI-driven cocktail platform built with a Human-Centered AI (HCAI) design philosophy.
The system offers an intelligent "Mixologist" for casual users and a "Master Bartender" + "Cost Calculator" for F&B professionals.

## Project Architecture

- **Frontend (Server-Driven UI):** Next.js 16 (App Router), Tailwind CSS v4, Server-Sent Events (SSE) Client
- **Backend Orchestrator:** FastAPI, LangGraph, Python 3.11+
- **Data & Memory:** Qdrant (Vector DB), Redis (Session Store), PostgreSQL (Relational Data)
- **Deployment:** Vercel (CI/CD via GitHub Actions)

## Repository Structure

```
cocktail-recommendation-system/
├── .env                          # Biến môi trường thực tế
├── .env.example                  # Template cho developer mới
├── README.md                     # Hướng dẫn setup đầy đủ
├── .github/
│   └── workflows/                # CI/CD pipelines (test, evals, Vercel deploy)
├── backend/
│   ├── requirements.txt          # Python packages
│   ├── tests/                    # PyTest suite (endpoints, agents, mocking)
│   └── app/
│       ├── main.py               # FastAPI entrypoint + CORS + SSE
│       ├── core/                 # Pydantic Settings
│       ├── db/                   # Clients: Postgres (Supabase), Redis, Qdrant
│       ├── api/                  # REST API Endpoints (session, chat, tools)
│       ├── agents/               # LangGraph state & nodes (Router, B2C Mixologist, B2B Bartender)
│       └── tools/                # Cost & ABV Calculator, Qdrant Retrievers
├── frontend/
│   ├── package.json              # Next.js 16, React 19, Tailwind v4, Playwright
│   ├── tests/                    # Playwright E2E tests
│   └── src/
│       ├── app/                  # Next.js App Router (page.tsx, globals.css, layout.tsx)
│       ├── components/sdui/      # Server-Driven UI Components (Card, Carousel, RationaleBlock)
│       └── lib/                  # SSE Logic & Client Helpers
└── data-pipeline/
    ├── requirements.txt          # pandas, qdrant-client, openai
    └── README.md                 # Pipeline documentation
```

## Setup Instructions

### Prerequisites

- Python 3.11 or Conda (Miniconda/Anaconda)
- Node.js 22 & pnpm (or use `cocktail-ai` conda environment)

### 1. Infrastructure (Cloud Setup)

The project is configured to run fully in the cloud to avoid local environment issues. Ensure your `.env` file is filled out with credentials from the following services:

- **Qdrant**: Sign up for a free tier cluster on [Qdrant Cloud](https://cloud.qdrant.io/). Update `QDRANT_URL` and `QDRANT_API_KEY`.
- **Redis**: Use [Upstash Redis](https://upstash.com/) for a serverless, free-tier Redis database. Update `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD`.
- **PostgreSQL**: Use [Supabase](https://supabase.com/) or [Neon](https://neon.tech/) for a free-tier Postgres DB. Update the `POSTGRES_*` variables.
- **LLM APIs**: Add your API keys for OpenRouter or Gemini (`OPENROUTER_API_KEY`, `GEMINI_API_KEY`).

### 2. Backend

Create the conda environment `cocktail-ai`:

```bash
conda create -n cocktail-ai python=3.11 -y
```

Activate the conda environment and install dependencies:

```bash
conda activate cocktail-ai
cd backend
pip install -r requirements.txt
```

Run the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Run Backend Tests:

```bash
export PYTHONPATH="."
pytest tests/
```

### 3. Frontend

Install dependencies and run the Next.js dev server:

```bash
cd frontend
pnpm install
pnpm run dev
```

Run Frontend E2E Tests:

```bash
pnpm exec playwright test
```

## Deployment

The project is configured for continuous deployment on **Vercel** via GitHub Actions.
Pushes to `dev` and `test` branches will trigger a Preview deployment.
Pushes to `main` will trigger a Production deployment.

Ensure the following GitHub Secrets are configured for the Vercel deployment:
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

---

*For more details, see the `docs/` folder.*
