import pytest
import sqlite3
import json
import os
from src.ui.app import get_db_connection

def test_db_connection():
    conn = get_db_connection()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()

def test_db_tables():
    conn = get_db_connection()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_sessions'")
    assert cursor.fetchone() is not None
    conn.close()

def test_insert_and_retrieve_session():
    conn = get_db_connection()
    test_id = "test_session_123"
    test_data = {"id": test_id, "title": "Test", "chat_history": []}
    
    # Clean up first
    conn.execute("DELETE FROM chat_sessions WHERE id = ?", (test_id,))
    
    # Insert
    conn.execute("INSERT INTO chat_sessions (id, timestamp, data) VALUES (?, ?, ?)", 
                 (test_id, "2026-06-09T00:00:00", json.dumps(test_data)))
    conn.commit()
    
    # Retrieve
    row = conn.execute("SELECT data FROM chat_sessions WHERE id = ?", (test_id,)).fetchone()
    assert row is not None
    retrieved_data = json.loads(row["data"])
    assert retrieved_data["id"] == test_id
    
    # Cleanup
    conn.execute("DELETE FROM chat_sessions WHERE id = ?", (test_id,))
    conn.commit()
    conn.close()
