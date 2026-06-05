# 🍸 AI Lounge - Cocktail & Bar Assistant

An advanced, smart Cocktail Recommendation & Bar Discovery system built with a **Multi-Agent (Orchestrator-Specialist)** architecture leveraging the **Gemini API (Function Calling/Tool Use)** and **Hybrid RAG (Semantic Search + Metadata Filtering)**.

---

## 🌟 Core Features

1. **Multi-Agent Orchestration**:
   - **Guest Concierge Agent**: Acts as a host that understands user preferences and moods. Recommends cocktails based on conversations and suggests real-world cocktail bars in Hanoi/HCMC.
   - **Master Bartender Agent**: Provides precise recipes, mixology techniques, ingredient substitution suggestions, and ABV analysis.
2. **Autonomous Tool Use (Gemini Function Calling)**:
   - The agents autonomously decide when and how to call the local database tools to fetch cocktails, search bars, calculate ABV, and find substitutes.
3. **Data Enrichment Pipeline**:
   - Uses Gemini API to expand a standard cocktail dataset with rich metadata (flavor profiles, history/meanings, proper glassware, and ABV categories).
4. **Premium Dark-Theme UI**:
   - A high-end Single Page Application (SPA) web interface built with a Flask backend and modern, responsive vanilla HTML/JS/CSS frontend, styled like a luxury cocktail lounge.
   - Dual modes: Guest Concierge (for discovery/bar recommendations) and Master Bartender (for mixology, ABV calculations, and custom recipes).
   - **Menu Builder**: Compile a list of drinks and export a formatted cocktail menu.

---

## 📂 Project Directory Structure

```text
cocktail-recommendation-system/
├── data/
│   ├── raw/                       # Raw cocktail dataset (final_cocktails.csv)
│   ├── enriched_cocktails.csv     # AI-enriched cocktail database
│   └── bars_vietnam.csv           # Curated real-world Vietnamese bar database
├── scripts/
│   └── data_enricher.py           # Offline script to enrich cocktail data using Gemini
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   └── cocktail_agents.py     # Multi-Agent logic (Orchestrator, Guest, Bartender)
│   ├── tools/
│   │   ├── __init__.py            # Tool declarations and execute mapping
│   │   ├── base.py                # Shared dataset loaders
│   │   ├── calculators.py         # ABV and ingredient cost calculators
│   │   ├── db_search.py           # Cocktail and bar database search queries
│   │   ├── mixology.py            # Ingredient substitution and custom signature recipe helpers
│   │   └── semantic_search.py     # SentenceTransformers local vector search
│   ├── ui/
│   │   ├── static/                # Single Page Application (HTML/JS/CSS) frontend assets
│   │   └── app.py                 # Flask server (serves static SPA and runs REST API endpoints)
│   └── utils/
│       ├── __init__.py
│       ├── config.py              # Environment configurations & paths loader
│       └── menu_exporter.py       # Premium menu HTML generator
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Setup & Execution

### 1. Prerequisite Environments
Create a Python virtual environment and install dependencies:
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your Gemini API key:
```bash
cp .env.example .env
```
Fill in the API key in `.env`:
```env
GEMINI_API_KEY=AIzaSy... # Your Gemini API key
```

### 3. Data Enrichment (Offline)
Run the enrichment script to build the enhanced database:
```bash
python scripts/data_enricher.py
```

### 4. Launch the Web Application

To run the application locally in development mode:
```bash
python src/ui/app.py
```
The app will start at `http://localhost:5000`.

### 5. Production Deployment

To run the application in a production-grade WSGI server:

**For Linux / Docker Containers (Render, Railway, VPS):**
```bash
gunicorn --bind 0.0.0.0:5000 src.ui.app:app
```

**For Windows Servers:**
```bash
waitress-serve --listen=0.0.0.0:5000 src.ui.app:app
```
