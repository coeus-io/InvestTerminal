"""
持仓管理 — 记录股票持仓 / 盈亏计算 / 实时市值
"""

import json
import os
from datetime import datetime
from typing import Optional

import pandas as pd

from python_tools.config import PORTFOLIO_FILE, DEFAULT_START_DATE
from python_tools.data.akshare_data import get_daily_price


def load() -> list[dict]:
    """加载持仓列表"""
    if not os.path.exists(PORTFOLIO_FILE):
        return []
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(holdings: list[dict]) -> None:
    """保存持仓列表"""
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(holdings, f, ensure_ascii=False, indent=2)


def add(symbol: str, name: str, cost_price: float, shares: int,
        buy_date: str = None, notes: str = "") -> dict:
    """
    新增持仓。
    buy_date: "2024-01-15" 格式，默认今天
    """
    holdings = load()

    if buy_date is None:
        buy_date = datetime.now().strftime("%Y-%m-%d")

    # 检查重复（同一代码可加仓）
    holding = {
        "symbol": symbol,
        "name": name,
        "cost_price": cost_price,
        "shares": shares,
        "buy_date": buy_date,
        "notes": notes,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    holdings.append(holding)
    save(holdings)

    return holding


def remove(symbol: str, index: int = None) -> dict | None:
    """删除持仓。指定 index 删除特定一笔，否则全部删除。"""
    holdings = load()
    new_holdings = []

    if index is not None:
        removed = None
        count = 0
        for h in holdings:
            if h["symbol"] == symbol:
                if count == index:
                    removed = h
                    count += 1
                    continue
                count += 1
            new_holdings.append(h)
    else:
        removed = [h for h in holdings if h["symbol"] == symbol]
        new_holdings = [h for h in holdings if h["symbol"] != symbol]
        removed = removed[0] if removed else None

    save(new_holdings)
    return removed


def list_holdings() -> list[dict]:
    """列出所有持仓"""
    return load()


def snapshot() -> pd.DataFrame:
    """
    持仓快照 — 实时盈亏。
    返回 DataFrame，包含每笔的市值、盈亏、收益率。
    """
    holdings = load()
    if not holdings:
        return pd.DataFrame()

    rows = []
    for h in holdings:
        symbol = h["symbol"]
        df = get_daily_price(symbol, start_date=DEFAULT_START_DATE, end_date="20500101")

        if df.empty:
            current_price = None
        else:
            current_price = df["close"].iloc[0]

        cost_total = h["cost_price"] * h["shares"]
        if current_price:
            market_value = current_price * h["shares"]
            pnl = market_value - cost_total
            pnl_pct = (current_price - h["cost_price"]) / h["cost_price"] * 100
        else:
            market_value = None
            pnl = None
            pnl_pct = None

        rows.append({
            "symbol": symbol,
            "name": h["name"],
            "shares": h["shares"],
            "cost_price": h["cost_price"],
            "cost_total": round(cost_total, 2),
            "current_price": current_price,
            "market_value": round(market_value, 2) if market_value else None,
            "pnl": round(pnl, 2) if pnl is not None else None,
            "pnl_pct": round(pnl_pct, 2) if pnl_pct is not None else None,
            "buy_date": h.get("buy_date", ""),
        })

    return pd.DataFrame(rows)


def summary() -> str:
    """持仓摘要 Markdown"""
    df = snapshot()
    if df.empty:
        return "暂无持仓记录。使用 `add` 添加持仓。"

    total_cost = df["cost_total"].sum()
    total_market = df["market_value"].sum() if df["market_value"].notna().all() else None
    total_pnl = total_market - total_cost if total_market is not None else None
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 and total_pnl is not None else None

    lines = ["## 持仓概览\n"]
    lines.append(f"**总成本**: {total_cost:,.2f}")
    lines.append(f"**总市值**: {total_market:,.2f}" if total_market else "**总市值**: N/A")
    lines.append(f"**总盈亏**: {total_pnl:+,.2f}" if total_pnl is not None else "**总盈亏**: N/A")
    lines.append(f"**总收益率**: {total_pnl_pct:+.2f}%" if total_pnl_pct is not None else "**总收益率**: N/A")
    lines.append("")

    lines.append("| 代码 | 名称 | 持仓 | 成本价 | 现价 | 成本 | 市值 | 盈亏 | 收益率 |")
    lines.append("|------|------|------|--------|------|------|------|------|--------|")

    for _, row in df.iterrows():
        lines.append(
            f"| {row['symbol']} | {row['name']} | {row['shares']} | "
            f"{row['cost_price']} | {row['current_price'] or 'N/A'} | "
            f"{row['cost_total']} | {row['market_value'] or 'N/A'} | "
            f"{row['pnl'] or 'N/A'} | {row['pnl_pct'] or 'N/A'} |"
        )

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"

    if cmd == "add" and len(sys.argv) >= 5:
        r = add(sys.argv[2], sys.argv[3], float(sys.argv[4]), int(sys.argv[5]))
        print(f"已添加: {r}")
    elif cmd == "list":
        print(json.dumps(list_holdings(), ensure_ascii=False, indent=2))
    elif cmd == "summary":
        print(summary())
    elif cmd == "snapshot":
        print(snapshot().to_string())
    elif cmd == "remove" and len(sys.argv) >= 3:
        remove(sys.argv[2])
        print("已删除")
    else:
        print("用法: tracker.py [add|list|summary|snapshot|remove]")
