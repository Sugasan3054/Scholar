import sqlite3
import os
import json

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

DB_PATH = os.path.join(DB_DIR, "papers.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            paper_id TEXT PRIMARY KEY,
            title_jp TEXT,
            title_en TEXT,
            published_date TEXT,
            source_url TEXT,
            summary_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            chat_history TEXT DEFAULT '[]'
        )
    ''')
    
    # Simple migration for existing DB
    try:
        cursor.execute("ALTER TABLE papers ADD COLUMN chat_history TEXT DEFAULT '[]'")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    conn.commit()
    conn.close()

def save_paper(paper_id: str, title_jp: str, title_en: str, published_date: str, source_url: str, summary_json: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Use INSERT OR IGNORE and then UPDATE to not overwrite chat_history if paper already exists
    cursor.execute('''
        INSERT OR IGNORE INTO papers 
        (paper_id, title_jp, title_en, published_date, source_url, summary_json, chat_history)
        VALUES (?, ?, ?, ?, ?, ?, '[]')
    ''', (paper_id, title_jp, title_en, published_date, source_url, json.dumps(summary_json, ensure_ascii=False)))
    
    cursor.execute('''
        UPDATE papers 
        SET title_jp = ?, title_en = ?, published_date = ?, source_url = ?, summary_json = ?
        WHERE paper_id = ?
    ''', (title_jp, title_en, published_date, source_url, json.dumps(summary_json, ensure_ascii=False), paper_id))
    
    conn.commit()
    conn.close()

def update_chat_history(paper_id: str, chat_history: list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE papers 
        SET chat_history = ?
        WHERE paper_id = ?
    ''', (json.dumps(chat_history, ensure_ascii=False), paper_id))
    conn.commit()
    conn.close()

def get_paper(paper_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM papers WHERE paper_id = ?", (paper_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_all_papers() -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Fetch newest first
    cursor.execute("SELECT paper_id, title_jp, title_en, published_date, source_url, summary_json, chat_history, created_at FROM papers ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]
