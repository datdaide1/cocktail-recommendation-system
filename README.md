# Cocktail Recommendation System

A dual-sided (B2C/B2B) AI-driven cocktail platform built with a Human-Centered AI (HCAI) design philosophy. 
The system offers an intelligent "Mixologist" for casual users and a "Master Bartender" + "Cost Calculator" for F&B professionals.

## Project Architecture

- **Frontend (Server-Driven UI):** Next.js (App Router), Tailwind CSS, Shadcn UI
- **Backend Orchestrator:** FastAPI, LangGraph, Python 3.10+
- **Data & Memory:** Qdrant (Vector DB), Redis (Session Store), PostgreSQL (Relational Data)

## Repository Structure

```
├── frontend/             # Next.js Web App
├── backend/              # FastAPI Server & LangGraph Agents
├── data-pipeline/        # Scripts for processing and vectorizing data
├── docs/                 # System Architecture & Specifications
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.10+ or Conda (Miniconda/Anaconda)
- Node.js & npm (or use `cocktail-ai` conda environment)

### 1. Infrastructure (Cloud Setup)
The project is configured to run fully in the cloud to avoid local environment issues. Ensure your `.env` file is filled out with credentials from the following services:

- **Qdrant**: Sign up for a free tier cluster on [Qdrant Cloud](https://cloud.qdrant.io/). Update `QDRANT_URL` and `QDRANT_API_KEY`.
- **Redis**: Use [Upstash Redis](https://upstash.com/) for a serverless, free-tier Redis database. Update `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD`.
- **PostgreSQL**: Use [Supabase](https://supabase.com/) or [Neon](https://neon.tech/) for a free-tier Postgres DB. Update the `POSTGRES_*` variables.

### 2. Backend
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
npm install
npm run dev
```

## Environment Variables
Copy `.env.example` to `.env` and fill in your API keys.

---
*For more details, see the `docs/` folder.*