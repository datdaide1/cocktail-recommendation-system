import sqlite3
import json
import sys

def import_logs(log_file, db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                date_str = parts[0]
                uuid_str = parts[1]
                json_str = parts[2]
                
                try:
                    data = json.loads(json_str)
                    session_id = data.get("id")
                    title = data.get("title", "New Chat")
                    role = data.get("role", "guest")
                    timestamp = data.get("timestamp", "")
                    
                    # Ensure user_id is set if missing
                    user_id = data.get("user_id", "user_3EepUdkEratbETkfKQvBkxt6gbK") 
                    
                    # Check if session exists
                    cursor.execute("SELECT id FROM chat_sessions WHERE id = ?", (session_id,))
                    exists = cursor.fetchone()
                    
                    if exists:
                        cursor.execute("UPDATE chat_sessions SET role = ?, timestamp = ?, data = ? WHERE id = ?", 
                                       (role, timestamp, json_str, session_id))
                    else:
                        cursor.execute("INSERT INTO chat_sessions (id, user_id, role, timestamp, data) VALUES (?, ?, ?, ?, ?)",
                                       (session_id, user_id, role, timestamp, json_str))
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON: {json_str[:50]}")
                    
    conn.commit()
    conn.close()
    print("Database updated successfully.")

if __name__ == "__main__":
    import_logs(r"C:\Users\tranh\.gemini\antigravity\brain\18d7d738-287c-46e0-9f1f-ec69c56cdb8e\raw_chat_logs.txt", 
                r"e:\RECOMMENDATION-SYSTEM\cocktail-recommendation-system\data\chat_data.db")
