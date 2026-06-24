# Cocktail Recommendation System

A dual-mode (B2C & B2B) intelligent recommendation system powered by Multi-Agent AI and LangGraph.

## Features
- **B2C Mode**: An interactive "Nightlife Concierge" that helps users discover cocktail bars, hidden speakeasies, and drink recommendations based on their mood and preferences.
- **B2B Mode**: A "Master Bartender" mode tailored for mixologists, which includes automated cost and ABV calculators, and an ingredient substitution engine.

## Tech Stack
- **Backend**: FastAPI, LangGraph, Qdrant (Vector DB), SQLite
- **AI Models**: OpenAI (via OpenRouter)
- **Frontend**: Vanilla HTML/JS/CSS served directly via FastAPI static files.

## Setup Instructions
1. Install Anaconda or Miniconda.
2. Create and activate the conda environment:
   ```bash
   conda create -n cocktail-ai python=3.11
   conda activate cocktail-ai
   ```
3. Install the dependencies from the `backend/requirements.txt`:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Create a `.env` file in the root directory and add your keys:
   ```env
   OPENROUTER_API_KEY=your_key_here
   OPENAI_API_BASE=https://openrouter.ai/api/v1
   ```
5. Run the server:
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
6. Navigate to `http://localhost:8000/b2c_03_chat_assistant.html` to use the system.
