import os
import sys
import json
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

# Append project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.utils.config import Config
from src.agents.cocktail_agents import CocktailAgentSystem
from src.tools.base import get_cocktails_df, get_bars_df
from src.utils.menu_exporter import MenuExporter

# Initialize Flask App
# We configure it to serve static files from the 'static' directory next to app.py
static_dir = Path(__file__).resolve().parent / "static"
app = Flask(__name__, static_folder=str(static_dir), static_url_path="")

# Initialize Agent System
try:
    agent_system = CocktailAgentSystem()
except Exception as e:
    print(f"Error initializing Agent System: {e}")
    agent_system = None

import uuid
import datetime
import sqlite3

# Path to Chat Sessions Database
DB_PATH = Config.DATABASE_PATH

def get_db_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            role TEXT,
            timestamp TEXT,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    """Serves the main single page web application"""
    return app.send_static_file('index.html')

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Returns list of sessions sorted by newest timestamp"""
    role = request.args.get("role", "")
    user_id = request.args.get("user_id", "")
    
    conn = get_db_connection()
    query = "SELECT data FROM chat_sessions WHERE 1=1"
    params = []
    
    if role:
        query += " AND role = ?"
        params.append(role)
    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)
        
    query += " ORDER BY timestamp DESC"
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    sessions_list = []
    for row in rows:
        session_data = json.loads(row["data"])
        sessions_list.append({
            "id": session_data.get("id"),
            "title": session_data.get("title", "New Chat"),
            "role": session_data.get("role", "guest"),
            "timestamp": session_data.get("timestamp", "")
        })
        
    return jsonify({"sessions": sessions_list})

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Returns details including messages list of a specific session"""
    conn = get_db_connection()
    row = conn.execute("SELECT data FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    
    if not row:
        return jsonify({"error": "Session not found"}), 404
        
    session = json.loads(row["data"])
    return jsonify(session)

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Creates a new empty chat session"""
    data = request.json or {}
    role = data.get("role", "guest")
    user_id = data.get("user_id", "")
    
    session_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    new_session = {
        "id": session_id,
        "title": "New Chat",
        "role": role,
        "timestamp": timestamp,
        "chat_history": []
    }
    
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO chat_sessions (id, user_id, role, timestamp, data) VALUES (?, ?, ?, ?, ?)",
        (session_id, user_id, role, timestamp, json.dumps(new_session))
    )
    conn.commit()
    conn.close()
    
    return jsonify(new_session)

@app.route('/api/sessions/<session_id>', methods=['PUT'])
def update_session(session_id):
    """Updates the chat history and title of a session"""
    data = request.json or {}
    history = data.get("chat_history", [])
    
    conn = get_db_connection()
    row = conn.execute("SELECT data FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
    
    if not row:
        conn.close()
        return jsonify({"error": "Session not found"}), 404
        
    session = json.loads(row["data"])
    session["chat_history"] = history
    timestamp = datetime.datetime.now().isoformat()
    session["timestamp"] = timestamp
    
    # Auto titling if the session title is still default
    if session["title"] == "New Chat" and len(history) > 0:
        first_user_msg = next((msg for msg in history if msg["role"] == "user"), None)
        if first_user_msg and first_user_msg.get("parts"):
            text = first_user_msg["parts"][0]
            clean_text = text.replace("\n", " ").strip()
            if len(clean_text) > 35:
                session["title"] = clean_text[:35] + "..."
            else:
                session["title"] = clean_text
                
    conn.execute(
        "UPDATE chat_sessions SET timestamp = ?, data = ? WHERE id = ?",
        (timestamp, json.dumps(session), session_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify(session)

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Deletes a chat session"""
    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    
    if deleted:
        return jsonify({"success": True})
    return jsonify({"error": "Session not found"}), 404

@app.route('/api/export_sessions', methods=['GET'])
def export_sessions():
    """Exports all sessions as a JSON file attachment"""
    conn = get_db_connection()
    rows = conn.execute("SELECT id, data FROM chat_sessions").fetchall()
    conn.close()
    
    sessions = {}
    for row in rows:
        sessions[row["id"]] = json.loads(row["data"])
        
    return jsonify(sessions)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handles conversational agent requests with automatic tool use and session logs logging"""
    if not agent_system:
        return jsonify({"message": "Gemini API key is not configured on the backend.", "chat_history": []}), 500
        
    data = request.json or {}
    message = data.get("message", "")
    history = data.get("chat_history", [])
    role = data.get("role", "guest") # 'guest' or 'bartender'
    session_id = data.get("session_id", "")
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
        
    try:
        result = agent_system.run_chat(message, history, role)
    except Exception as e:
        print(f"Error executing run_chat: {e}")
        return jsonify({"error": f"Agent error: {str(e)}"}), 500
    
    # Auto-log updates into the sqlite database if session_id exists
    if session_id:
        conn = get_db_connection()
        row = conn.execute("SELECT data FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
        
        if row:
            session = json.loads(row["data"])
            session["chat_history"] = result["chat_history"]
            timestamp = datetime.datetime.now().isoformat()
            session["timestamp"] = timestamp
            
            # Auto titling if the session title is still default
            if session["title"] == "New Chat" and len(result["chat_history"]) > 0:
                first_user_msg = next((msg for msg in result["chat_history"] if msg["role"] == "user"), None)
                if first_user_msg and first_user_msg.get("parts"):
                    text = first_user_msg["parts"][0]
                    clean_text = text.replace("\n", " ").strip()
                    if len(clean_text) > 35:
                        session["title"] = clean_text[:35] + "..."
                    else:
                        session["title"] = clean_text
                        
            conn.execute(
                "UPDATE chat_sessions SET timestamp = ?, data = ? WHERE id = ?",
                (timestamp, json.dumps(session), session_id)
            )
            conn.commit()
            
            # Fire-and-forget logging to Google Sheets via Google Forms
            import threading
            import requests
            def submit_to_gform(sid, cdata):
                try:
                    form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdirWt5H9HQ1AbR7Qc_2N-dF98enVeWCIviZXYpEsSvOLQSrw/formResponse"
                    payload = {
                        "entry.1227120136": sid,
                        "entry.39545789": json.dumps(cdata, ensure_ascii=False)
                    }
                    requests.post(form_url, data=payload, timeout=5)
                except Exception as e:
                    print("Error logging to GForm:", e)
                    
            threading.Thread(target=submit_to_gform, args=(session_id, session), daemon=True).start()
            
        conn.close()
            
    return jsonify(result)

@app.route('/api/bars', methods=['GET'])
def get_bars():
    """Returns matching bar records from bars_vietnam.csv"""
    city = request.args.get("city", "")
    district = request.args.get("district", "")
    style = request.args.get("style", "")
    price_range = request.args.get("price_range", "")
    
    df = get_bars_df()
    if df.empty:
        return jsonify({"bars": []})
        
    results = df.copy()
    
    if city and city != "Any":
        results = results[results['city'].str.lower() == city.lower()]
    if district:
        results = results[results['district'].str.lower().str.contains(district.lower())]
    if style and style != "Any":
        results = results[results['style'].str.lower().str.contains(style.lower())]
    if price_range and price_range != "Any":
        results = results[results['price_range'] == price_range]
        
    output = []
    for _, row in results.iterrows():
        output.append({
            "name": row.get("name"),
            "city": row.get("city"),
            "district": row.get("district"),
            "address": row.get("address"),
            "style": row.get("style"),
            "price_range": row.get("price_range"),
            "signature_cocktail": row.get("signature_cocktail"),
            "vibe_description": row.get("vibe_description")
        })
        
    return jsonify({"bars": output})

@app.route('/api/cocktails', methods=['GET'])
def get_cocktails():
    """Returns filtered cocktail recipes from the database"""
    search = request.args.get("search", "")
    
    df = get_cocktails_df()
    if df.empty:
        return jsonify({"cocktails": []})
        
    results = df.copy()
    if search:
        results = results[
            results['name'].str.lower().str.contains(search.lower()) |
            results['ingredients'].str.lower().str.contains(search.lower())
        ]
        
    output = []
    for _, row in results.head(50).iterrows():
        # Parse ingredients string representation of list to nice list
        ingredients_raw = row.get("ingredients", "")
        try:
            ingredients_list = eval(ingredients_raw)
            if not isinstance(ingredients_list, list):
                ingredients_list = [ingredients_raw]
        except:
            ingredients_list = [ingredients_raw] if ingredients_raw else []
            
        output.append({
            "name": row.get("name"),
            "category": row.get("category"),
            "glassware_recommendation": row.get("glassware_recommendation", row.get("glassType")),
            "abv_category": row.get("abv_category"),
            "ingredients": ingredients_list,
            "instructions": row.get("instructions"),
            "meaning_and_history": row.get("meaning_and_history"),
            "drinkThumbnail": row.get("drinkThumbnail")
        })
        
    return jsonify({"cocktails": output})

@app.route('/api/abv', methods=['POST'])
def calculate_abv_endpoint():
    """Performs local ABV math calculations on client-defined formulas"""
    data = request.json or {}
    ingredients = data.get("ingredients", [])
    
    total_volume = 0.0
    total_alcohol = 0.0
    
    for ing in ingredients:
        vol = float(ing.get("volume_ml", 0.0))
        abv = float(ing.get("abv", 0.0))
        total_volume += vol
        total_alcohol += (vol * abv / 100.0)
        
    if total_volume == 0:
        return jsonify({"error": "Total volume must be greater than 0ml."}), 400
        
    final_abv = (total_alcohol / total_volume) * 100.0
    
    if final_abv == 0:
        abv_category = "Mocktail (Non-alcoholic)"
        color = "#4CAF50"
    elif final_abv < 10:
        abv_category = "Low ABV"
        color = "#2196F3"
    elif final_abv < 20:
        abv_category = "Medium ABV"
        color = "#FF9800"
    else:
        abv_category = "Strong ABV"
        color = "#F44336"
        
    return jsonify({
        "total_volume_ml": round(total_volume, 1),
        "estimated_abv": round(final_abv, 1),
        "abv_category": abv_category,
        "color_code": color,
        "description": f"Overall drink volume: {round(total_volume, 1)}ml with an estimated strength of {round(final_abv, 1)}% ABV."
    })

@app.route('/api/export-menu', methods=['POST'])
def export_menu():
    """Generates and returns customized premium HTML menu string"""
    data = request.json or {}
    title = data.get("title", "THE ARTISAN LOUNGE")
    selected_cocktails = data.get("cocktails", [])
    
    exporter = MenuExporter(menu_title=title)
    html_menu = exporter.generate_html_menu(selected_cocktails)
    
    return jsonify({"html": html_menu})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting Premium AI Lounge Web App at http://{host}:{port} ...")
    app.run(host=host, port=port, debug=True)
