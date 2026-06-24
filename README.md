# Cocktail Recommendation System

A dual-sided (B2C/B2B) AI-driven cocktail platform built with a Human-Centered AI (HCAI) design philosophy.
The system offers an intelligent "Mixologist" for casual users and a "Master Bartender" + "Cost Calculator" for F&B professionals.

## Project Architecture

- **Frontend (Server-Driven UI):** Next.js (App Router), Tailwind CSS, Shadcn UI
- **Backend Orchestrator:** FastAPI, LangGraph, Python 3.10+
- **Data & Memory:** Qdrant (Vector DB), Redis (Session Store), PostgreSQL (Relational Data)

## Repository Structure

```
cocktail-recommendation-system/
├── .env                          # Biến môi trường thực tế
├── .env.example                  # Template cho developer mới
├── .gitignore                    # Python, Node, Next.js, OS files
├── README.md                     # Hướng dẫn setup đầy đủ
├── backend/
│   ├── requirements.txt          # 12 Python packages
│   ├── verify_connections.py     # Script kiểm tra kết nối DB
│   └── app/
│       ├── main.py               # FastAPI entrypoint + CORS + health check
│       ├── core/
│       │   └── config.py         # Pydantic Settings (LLM, Qdrant, Postgres, Redis)
│       ├── db/
│       │   ├── postgres.py       # Async SQLAlchemy engine + SSL + PgBouncer fixes
│       │   ├── redis.py          # Async Redis client (Upstash)
│       │   └── qdrant.py         # Async Qdrant client (Cloud)
│       ├── api/
│       │   └── __init__.py       # APIRouter stub
│       ├── agents/               # (Empty - sẵn sàng cho LangGraph agents)
│       └── tools/                # (Empty - sẵn sàng cho Cost Calculator, Substitution Engine)
├── frontend/
│   ├── package.json              # Next.js 16.2.9, React 19, Tailwind v4, Lucide
│   ├── pnpm-lock.yaml            # Lock file đầy đủ
│   ├── tsconfig.json             # TypeScript config
│   ├── next.config.ts            # Next.js config
│   ├── postcss.config.mjs        # PostCSS + Tailwind
│   ├── eslint.config.mjs         # ESLint
│   ├── node_modules/             # Dependencies đã cài đặt
│   ├── .next/                    # Build cache (Next.js đã build thành công)
│   └── src/app/
│       ├── globals.css           # CSS tokens
│       ├── layout.tsx            # Root layout
│       ├── page.tsx              # Landing page
│       └── favicon.ico
└── data-pipeline/
    ├── requirements.txt          # pandas, qdrant-client, sentence-transformers, openai, tqdm
    └── README.md                 # Pipeline documentation
```

## Setup Instructions

### Prerequisites

- Python 3.11 or Conda (Miniconda/Anaconda)
- Node.js & pnpm (or use `cocktail-ai` conda environment)

### 1. Infrastructure (Cloud Setup)

The project is configured to run fully in the cloud to avoid local environment issues. Ensure your `.env` file is filled out with credentials from the following services:

- **Qdrant**: Sign up for a free tier cluster on [Qdrant Cloud](https://cloud.qdrant.io/). Update `QDRANT_URL` and `QDRANT_API_KEY`.
- **Redis**: Use [Upstash Redis](https://upstash.com/) for a serverless, free-tier Redis database. Update `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD`.
- **PostgreSQL**: Use [Supabase](https://supabase.com/) or [Neon](https://neon.tech/) for a free-tier Postgres DB. Update the `POSTGRES_*` variables.

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

### 3. Frontend

Install dependencies and run the Next.js dev server:

```bash
conda activate cocktail-ai
cd frontend
pnpm install
pnpm run dev
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your API keys.

---

*For more details, see the `docs/` folder.*
