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
   - A high-end Streamlit web interface styled like a luxury lounge with two distinct modes (Guest & Bartender).
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
│   │   ├── __init__.py
│   │   └── cocktail_tools.py      # Python tools for Gemini (DB Search, ABV, Substitutes)
│   ├── ui/
│   │   └── app.py                 # Streamlit UI (Guest / Bartender tabs)
│   └── utils/
│       ├── __init__.py
│       ├── config.py              # Environment configuration & path loader
│       └── menu_exporter.py       # Exporter utility for menu generation
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
```bash
streamlit run src/ui/app.py
```
The app will automatically launch in your browser at `http://localhost:8501`.
