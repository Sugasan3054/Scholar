import sqlite3
import os
import json
from datetime import date

from config import config

def get_connection():
    """環境変数 DATABASE_URL に基づきDBコネクションを取得する"""
    url = config.DATABASE_URL
    if url.startswith("sqlite:///"):
        # SQLite用のパス抽出
        db_path = url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        return sqlite3.connect(db_path)
    elif url.startswith("postgres"):
        # 将来の RDS / PostgreSQL用拡張ポイント
        raise NotImplementedError("PostgreSQL connection will require psycopg2 or SQLAlchemy.")
    else:
        raise ValueError(f"Unsupported DATABASE_URL scheme: {url}")

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # ユーザーテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ペーパーテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            paper_id TEXT PRIMARY KEY,
            title_jp TEXT,
            title_en TEXT,
            published_date TEXT,
            source_url TEXT,
            summary_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            chat_history TEXT DEFAULT '[]',
            user_id TEXT DEFAULT 'anonymous'
        )
    ''')
    
    # レートリミットテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rate_limits (
            user_id TEXT,
            action TEXT,
            date_str TEXT,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, action, date_str)
        )
    ''')
    
    # Simple migrations for existing DB
    try:
        cursor.execute("ALTER TABLE papers ADD COLUMN chat_history TEXT DEFAULT '[]'")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    try:
        cursor.execute("ALTER TABLE papers ADD COLUMN user_id TEXT DEFAULT 'anonymous'")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    conn.commit()
    conn.close()

def save_paper(paper_id: str, title_jp: str, title_en: str, published_date: str, source_url: str, summary_json: dict, user_id: str = "anonymous"):
    conn = get_connection()
    cursor = conn.cursor()
    
    # ユーザーが存在しない場合は登録（プロトタイプ自動登録）
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    
    # Use INSERT OR IGNORE and then UPDATE to not overwrite chat_history if paper already exists
    cursor.execute('''
        INSERT OR IGNORE INTO papers 
        (paper_id, title_jp, title_en, published_date, source_url, summary_json, chat_history, user_id)
        VALUES (?, ?, ?, ?, ?, ?, '[]', ?)
    ''', (paper_id, title_jp, title_en, published_date, source_url, json.dumps(summary_json, ensure_ascii=False), user_id))
    
    cursor.execute('''
        UPDATE papers 
        SET title_jp = ?, title_en = ?, published_date = ?, source_url = ?, summary_json = ?, user_id = ?
        WHERE paper_id = ?
    ''', (title_jp, title_en, published_date, source_url, json.dumps(summary_json, ensure_ascii=False), user_id, paper_id))
    
    conn.commit()
    conn.close()

def update_chat_history(paper_id: str, chat_history: list):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE papers 
        SET chat_history = ?
        WHERE paper_id = ?
    ''', (json.dumps(chat_history, ensure_ascii=False), paper_id))
    conn.commit()
    conn.close()

def check_rate_limit(user_id: str, action: str = "translate", limit: int = 5) -> bool:
    """
    1日の制限回数を超過していないか確認し、超過していなければカウントを増やす。
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    today_str = date.today().isoformat()
    
    # レコードが存在しなければ作成
    cursor.execute('''
        INSERT OR IGNORE INTO rate_limits (user_id, action, date_str, count)
        VALUES (?, ?, ?, 0)
    ''', (user_id, action, today_str))
    
    # 現在のカウントを取得
    cursor.execute('''
        SELECT count FROM rate_limits
        WHERE user_id = ? AND action = ? AND date_str = ?
    ''', (user_id, action, today_str))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False
        
    current_count = row[0]
    
    if current_count >= limit:
        conn.close()
        return False
        
    # カウントを増やす
    cursor.execute('''
        UPDATE rate_limits SET count = count + 1
        WHERE user_id = ? AND action = ? AND date_str = ?
    ''', (user_id, action, today_str))
    
    conn.commit()
    conn.close()
    return True


def get_paper(paper_id: str) -> dict:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM papers WHERE paper_id = ?", (paper_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_all_papers(user_id: str = None) -> list:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Fetch newest first
    if user_id:
        cursor.execute("SELECT paper_id, title_jp, title_en, published_date, source_url, summary_json, chat_history, created_at, user_id FROM papers WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    else:
        cursor.execute("SELECT paper_id, title_jp, title_en, published_date, source_url, summary_json, chat_history, created_at, user_id FROM papers ORDER BY created_at DESC")
        
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]
