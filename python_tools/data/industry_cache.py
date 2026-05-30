"""
行业成分股缓存管理 — 实时 API 优先 + 本地 JSON 兜底 + 新鲜度追踪

设计理念：
- 每次调用 get_industry_stocks() 时先尝试实时 API
- 成功则自动更新本地缓存（JSON 文件），返回实时数据
- 失败则回退到本地缓存，标注数据来源和新鲜度
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from python_tools.config import DATA_DIR

# ── 代理绕过 ───────────────────────────────────────────────────
_PROXY_KEYS = ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy")


def _proxy_pop():
    """临时移除代理环境变量，避免 akshare 请求走代理"""
    bak = {}
    for k in _PROXY_KEYS:
        v = os.environ.pop(k, None)
        if v is not None:
            bak[k] = v
    return bak


def _proxy_restore(bak: dict):
    for k, v in bak.items():
        os.environ[k] = v

CACHE_FILE = os.path.join(DATA_DIR, "industry_stocks.json")
META_FILE = os.path.join(DATA_DIR, "industry_stocks_meta.json")


def _read_cache() -> dict:
    """读取本地成分股缓存"""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 去掉元数据 key
        return {k: v for k, v in data.items() if not k.startswith("__")}
    except Exception:
        return {}


def _write_cache(data: dict):
    """写入本地成分股缓存"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _read_meta() -> dict:
    """读取元数据文件"""
    if not os.path.exists(META_FILE):
        return {}
    try:
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_meta(meta: dict):
    """写入元数据文件"""
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def _try_fetch_live(industry_name: str) -> pd.DataFrame:
    """
    尝试从 eastmoney 实时 API 获取成分股。
    自动绕过代理，确保在 VPN/代理环境下也能直连。
    成功返回 DataFrame，失败返回空。
    """
    try:
        import akshare as ak
        bak = _proxy_pop()
        try:
            df = ak.stock_board_industry_cons_em(symbol=industry_name)
            return df if (df is not None and not df.empty) else pd.DataFrame()
        finally:
            _proxy_restore(bak)
    except Exception as e:
        print(f"  [info] {industry_name} 实时获取失败: {e}", file=sys.stderr)
        return pd.DataFrame()


def _fuzzy_match(data: dict, industry_name: str) -> Optional[list]:
    """模糊匹配行业名称"""
    # 精确匹配
    if industry_name in data:
        return data[industry_name]

    # 子串匹配
    for key, val in data.items():
        if industry_name in key or key in industry_name:
            return val

    return None


def get_stocks(industry_name: str, force_live: bool = False) -> tuple[pd.DataFrame, dict]:
    """
    获取行业成分股。

    Args:
        industry_name: 行业名称，如 '白酒'
        force_live: 跳过缓存，强制实时 API

    Returns:
        (DataFrame, meta_dict)
        meta = {"source": "live"|"cache", "updated_at": "ISO时间"|None, "stale_days": int|None}

    策略：
    1. 每次调用都尝试实时 API（网络可通时自动更新缓存）
    2. 实时失败则用本地缓存
    3. 缓存也没有则返回空
    """
    meta_info = _read_meta()

    # ── 尝试实时 API ──────────────────────────────────────────
    if not force_live:
        # 检查是否刚刷新过（1 小时内不重复请求，避免 API 限流）
        last_attempt = meta_info.get("_last_attempt", 0)
        if time.time() - last_attempt < 3600 and meta_info.get("_last_success", False):
            # 刚成功过，跳过一次实时请求
            pass
        else:
            df = _try_fetch_live(industry_name)
            meta_info["_last_attempt"] = time.time()

            if not df.empty:
                # 实时 API 成功 — 更新缓存
                stocks_data = _read_cache()
                # 适配列名
                if "代码" in df.columns and "名称" in df.columns:
                    stocks_data[industry_name] = [
                        {"symbol": str(r["代码"]), "name": str(r["名称"])}
                        for _, r in df.iterrows()
                    ]
                elif "symbol" in df.columns and "name" in df.columns:
                    stocks_data[industry_name] = [
                        {"symbol": str(r["symbol"]), "name": str(r["name"])}
                        for _, r in df.iterrows()
                    ]
                else:
                    stocks_data[industry_name] = df.to_dict(orient="records")

                _write_cache(stocks_data)
                meta_info["_last_success"] = True
                meta_info["_last_refresh"] = datetime.now().isoformat()
                _write_meta(meta_info)

                return df, {"source": "live", "updated_at": meta_info["_last_refresh"]}
            else:
                meta_info["_last_success"] = False
                _write_meta(meta_info)

    # ── 回退到本地缓存 ─────────────────────────────────────────
    cache_data = _read_cache()
    stocks = _fuzzy_match(cache_data, industry_name)

    if stocks:
        last_refresh = meta_info.get("_last_refresh")
        stale_days = None
        if last_refresh:
            try:
                last_dt = datetime.fromisoformat(last_refresh)
                stale_days = (datetime.now() - last_dt).days
            except Exception:
                pass

        df = pd.DataFrame(stocks)
        return df, {
            "source": "cache",
            "updated_at": last_refresh,
            "stale_days": stale_days,
        }

    return pd.DataFrame(), {"source": "none"}


def cache_stats() -> dict:
    """缓存统计"""
    data = _read_cache()
    meta = _read_meta()
    return {
        "industries_cached": len(data),
        "total_stocks": sum(len(v) for v in data.values()),
        "last_refresh": meta.get("_last_refresh"),
        "last_attempt": meta.get("_last_attempt"),
        "last_success": meta.get("_last_success", False),
    }


def rebuild_all() -> dict:
    """
    重建全部行业成分股缓存（需在不受限网络上运行）。
    遍历所有 THS 行业，逐个调用实时 API。
    增量更新——已有数据的行业不会被清空，只补充缺失的。
    """
    from python_tools.data.akshare_data import get_industry_classification

    industries = get_industry_classification()
    if industries.empty:
        return {"error": "无法获取行业列表"}

    existing = _read_cache()  # 保留已有数据
    total = len(industries)
    success_count = 0
    empty_count = 0

    for idx, (_, row) in enumerate(industries.iterrows(), 1):
        name = row.get("name", "")
        if not name:
            continue

        # 跳过已有数据的行业（加速）
        if name in existing and len(existing[name]) > 0:
            success_count += 1
            continue

        print(f"  [{idx}/{total}] {name} ...", end=" ", flush=True)

        df = _try_fetch_live(name)
        if df.empty:
            print("✗ 不可达")
            empty_count += 1
            # 保留已有的数据，不覆盖
            if name in existing:
                continue
            existing[name] = []
            continue

        success_count += 1
        if "代码" in df.columns and "名称" in df.columns:
            stocks = [
                {"symbol": str(r["代码"]), "name": str(r["名称"])}
                for _, r in df.iterrows()
            ]
        elif "symbol" in df.columns and "name" in df.columns:
            stocks = [
                {"symbol": str(r["symbol"]), "name": str(r["name"])}
                for _, r in df.iterrows()
            ]
        else:
            stocks = df.to_dict(orient="records")

        existing[name] = stocks
        print(f"✓ {len(stocks)} 只")
        time.sleep(0.3)

    _write_cache(existing)

    meta = _read_meta()
    meta["_last_refresh"] = datetime.now().isoformat()
    meta["_last_success"] = success_count > 0
    meta["_last_attempt"] = time.time()
    _write_meta(meta)

    return {
        "industries": len(existing),
        "successfully_fetched": success_count,
        "empty_or_failed": empty_count,
        "total_stocks": sum(len(v) for v in existing.values()),
        "saved_to": CACHE_FILE,
    }
    meta["_last_success"] = True
    meta["_last_attempt"] = time.time()
    _write_meta(meta)

    return {
        "industries": len(result),
        "successfully_fetched": success_count,
        "total_stocks": sum(len(v) for v in result.values()),
        "saved_to": CACHE_FILE,
    }
