# memory/persistent_memory.py
import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from langgraph.checkpoint.memory import MemorySaver

# 使用D盘路径（遵循Conda-Disk-Manager）
DATA_DIR = os.environ.get("DATA_ROOT", "D:/generated_outputs/research_assistant")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "memory.db")

class PersistentMemory:
    """会话记忆管理器"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                session_id TEXT PRIMARY KEY,
                messages TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                key TEXT,
                value TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES conversations(session_id)
            )
        ''')
        conn.commit()
        conn.close()
    
    def save_conversation(self, session_id: str, messages: List[Dict[str, str]]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now()
        cursor.execute('''
            INSERT OR REPLACE INTO conversations (session_id, messages, created_at, updated_at)
            VALUES (?, ?, COALESCE((SELECT created_at FROM conversations WHERE session_id=?), ?), ?)
        ''', (session_id, json.dumps(messages, ensure_ascii=False), session_id, now, now))
        conn.commit()
        conn.close()
    
    def load_conversation(self, session_id: str) -> List[Dict[str, str]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT messages FROM conversations WHERE session_id=?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return []
    
    def save_memory(self, session_id: str, key: str, value: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now()
        cursor.execute('''
            INSERT OR REPLACE INTO user_memories (session_id, key, value, created_at)
            VALUES (?, ?, ?, ?)
        ''', (session_id, key, value, now))
        conn.commit()
        conn.close()
    
    def load_memory(self, session_id: str, key: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM user_memories WHERE session_id=? AND key=?", (session_id, key))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

# LangGraph的MemorySaver用于checkpoint持久化（内存级，重启丢失）
_saver_instance = None

def get_memory_saver():
    global _saver_instance
    if _saver_instance is None:
        _saver_instance = MemorySaver()
    return _saver_instance

# 全局单例
_memory_instance = None
def get_memory():
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = PersistentMemory()
    return _memory_instance