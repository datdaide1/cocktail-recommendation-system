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
from src.tools.cocktail_tools import get_cocktails_df, get_bars_df
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

# Path to Chat Sessions Database
SESSIONS_FILE = Path(Config.COCKTAILS_PATH).parent / "chat_sessions.json"

import uuid
import datetime

def read_sessions():
    """Reads all chat sessions from local JSON storage"""
    if not SESSIONS_FILE.exists():
        try:
            SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
                json.dump({"sessions": {}}, f)
        except Exception as e:
            print(f"Error creating sessions file: {e}")
            return {}
        return {}
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("sessions", {})
    except Exception as e:
        print(f"Error reading sessions file: {e}")
        return {}

def write_sessions(sessions):
    """Writes all sessions back to local JSON storage"""
    try:
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump({"sessions": sessions}, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing sessions file: {e}")

@app.route('/')
def index():
    """Serves the main single page web application"""
    return app.send_static_file('index.html')

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Returns list of sessions sorted by newest timestamp"""
    sessions = read_sessions()
    role = request.args.get("role", "") # optionally filter by role
    
    sessions_list = []
    for sid, sdata in sessions.items():
        if role and sdata.get("role") != role:
            continue
        sessions_list.append({
            "id": sid,
            "title": sdata.get("title", "New Chat"),
            "role": sdata.get("role", "guest"),
            "timestamp": sdata.get("timestamp", "")
        })
        
    # Sort by timestamp descending
    sessions_list.sort(key=lambda x: x["timestamp"], reverse=True)
    return jsonify({"sessions": sessions_list})

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Returns details including messages list of a specific session"""
    sessions = read_sessions()
    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(session)

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Creates a new empty chat session"""
    data = request.json or {}
    role = data.get("role", "guest")
    
    sessions = read_sessions()
    session_id = str(uuid.uuid4())
    
    new_session = {
        "id": session_id,
        "title": "New Chat",
        "role": role,
        "timestamp": datetime.datetime.now().isoformat(),
        "chat_history": []
    }
    
    sessions[session_id] = new_session
    write_sessions(sessions)
    return jsonify(new_session)

@app.route('/api/sessions/<session_id>', methods=['PUT'])
def update_session(session_id):
    """Updates the chat history and title of a session"""
    data = request.json or {}
    history = data.get("chat_history", [])
    
    sessions = read_sessions()
    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    session["chat_history"] = history
    session["timestamp"] = datetime.datetime.now().isoformat()
    
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
                
    sessions[session_id] = session
    write_sessions(sessions)
    return jsonify(session)

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Deletes a chat session"""
    sessions = read_sessions()
    if session_id in sessions:
        del sessions[session_id]
        write_sessions(sessions)
        return jsonify({"success": True})
    return jsonify({"error": "Session not found"}), 404

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
        
    result = agent_system.run_chat(message, history, role)
    
    # Auto-log updates into the json database file if session_id exists
    if session_id:
        sessions = read_sessions()
        session = sessions.get(session_id)
        if session:
            session["chat_history"] = result["chat_history"]
            session["timestamp"] = datetime.datetime.now().isoformat()
            
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
                        
            sessions[session_id] = session
            write_sessions(sessions)
            
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
    host = os.getenv("HOST", "127.0.0.1")
    print(f"Starting Premium AI Lounge Web App at http://{host}:{port} ...")
    app.run(host=host, port=port, debug=True)
