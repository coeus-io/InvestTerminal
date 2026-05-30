"""
SQLite 本地缓存 — 减少重复网络请求
"""

import sqlite3
import json
import time
import os
from datetime import datetime, timedelta

from python_tools.config import CACHE_DB, CACHE_TTL


def _conn():
    """获取数据库连接（自动建表）"""
    os.makedirs(os.path.dirname(CACHE_DB), exist_ok=True)
    c = sqlite3.connect(CACHE_DB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at REAL
        )
    """)
    c.commit()
    return c


def _key(namespace: str, *parts: str) -> str:
    """构造缓存 key"""
    return f"{namespace}:{':'.join(str(p) for p in parts)}"


def get(namespace: str, *parts: str) -> str | None:
    """
    读缓存，过期返回 None。
    用法：cache.get("daily_price", "600519", "2024-01-01", "2024-12-31")
    """
    ttl = CACHE_TTL.get(namespace, 24 * 3600)
    key = _key(namespace, *parts)
    try:
        c = _conn()
        row = c.execute("SELECT value, updated_at FROM cache WHERE key = ?", (key,)).fetchone()
        c.close()
        if row is None:
            return None
        value, updated_at = row
        if time.time() - updated_at > ttl:
            return None
        return value
    except Exception:
        return None


def set(namespace: str, *parts: str, value: str) -> None:
    """
    写缓存。
    用法：cache.set("daily_price", "600519", "2024-01-01", "2024-12-31", json.dumps(df.to_dict()))
    """
    key = _key(namespace, *parts)
    try:
        c = _conn()
        c.execute(
            "INSERT OR REPLACE INTO cache (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, time.time()),
        )
        c.commit()
        c.close()
    except Exception:
        pass


def clear(namespace: str | None = None) -> int:
    """清空缓存，返回清除条数"""
    c = _conn()
    cur = c.cursor()
    if namespace:
        cur.execute("DELETE FROM cache WHERE key LIKE ?", (f"{namespace}:%",))
    else:
        cur.execute("DELETE FROM cache")
    count = cur.rowcount
    c.commit()
    c.close()
    return count


def stats() -> dict:
    """缓存统计"""
    c = _conn()
    total = c.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
    c.close()
    return {"total_entries": total, "db_path": CACHE_DB}
