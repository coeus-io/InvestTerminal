"""
收益归因 — 总收益 / 年化收益 / 基准对比 / 行业暴露
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional

from python_tools.portfolio.tracker import load, snapshot
from python_tools.data.akshare_data import get_daily_price, get_index_data
from python_tools.config import DEFAULT_BENCHMARK, DEFAULT_START_DATE


def total_return() -> dict:
    """
    计算持仓总收益。
    返回 {"total_pnl": float, "total_pnl_pct": float, "total_cost": float, "total_market_value": float}
    """
    df = snapshot()
    if df.empty:
        return {"error": "暂无持仓"}

    total_cost = df["cost_total"].sum()
    if df["market_value"].isna().all():
        return {"error": "无法获取当前价格"}

    total_market = df["market_value"].sum()
    total_pnl = total_market - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

    return {
        "total_cost": round(total_cost, 2),
        "total_market_value": round(total_market, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl_pct, 2),
    }


def annualized_return() -> dict:
    """
    年化收益率计算。
    对每笔持仓用 XIRR 简化（持有期收益年化）。
    """
    holdings = load()
    if not holdings:
        return {"error": "暂无持仓"}

    results = []
    now = datetime.now()

    for h in holdings:
        symbol = h["symbol"]
        buy_date = h.get("buy_date", DEFAULT_START_DATE[:4] + "-" + DEFAULT_START_DATE[4:6] + "-" + DEFAULT_START_DATE[6:])
        start = max(buy_date.replace("-", ""), DEFAULT_START_DATE)
        df = get_daily_price(symbol, start_date=start, end_date="20500101")

        if df.empty or "close" not in df.columns:
            results.append({"symbol": symbol, "annualized_return": None, "error": "无数据"})
            continue

        buy_price = h["cost_price"]
        current_price = df["close"].iloc[0]

        # 持有天数
        buy_date = datetime.strptime(h.get("buy_date", DEFAULT_START_DATE[:4] + "-" + DEFAULT_START_DATE[4:6] + "-" + DEFAULT_START_DATE[6:]), "%Y-%m-%d")
        days_held = max((now - buy_date).days, 1)

        # 年化: (current/buy)^(365/days) - 1
        if buy_price > 0:
            ann_return = ((current_price / buy_price) ** (365 / days_held) - 1) * 100
        else:
            ann_return = None

        results.append({
            "symbol": symbol,
            "name": h["name"],
            "buy_date": h.get("buy_date"),
            "days_held": days_held,
            "buy_price": buy_price,
            "current_price": current_price,
            "simple_return": round((current_price - buy_price) / buy_price * 100, 2),
            "annualized_return": round(ann_return, 2) if ann_return else None,
        })

    # 组合年化（按市值加权）
    total_cost = sum(h["cost_price"] * h["shares"] for h in holdings)
    total_current = 0
    for h, r in zip(holdings, results):
        df = get_daily_price(h["symbol"], start_date=DEFAULT_START_DATE, end_date="20500101")
        if not df.empty and "close" in df.columns:
            total_current += df["close"].iloc[0] * h["shares"]

    portfolio_ann = None
    if total_cost > 0 and total_current > 0:
        # 用最早的买入日期
        earliest = min(h.get("buy_date", DEFAULT_START_DATE[:4] + "-" + DEFAULT_START_DATE[4:6] + "-" + DEFAULT_START_DATE[6:]) for h in holdings)
        earliest_dt = datetime.strptime(earliest, "%Y-%m-%d")
        days = max((now - earliest_dt).days, 1)
        portfolio_ann = ((total_current / total_cost) ** (365 / days) - 1) * 100

    return {
        "holdings": results,
        "portfolio_annualized": round(portfolio_ann, 2) if portfolio_ann else None,
    }


def benchmark_comparison() -> dict:
    """
    与基准（沪深300）对比。
    """
    holdings = load()
    if not holdings:
        return {"error": "暂无持仓"}

    # 获取最早的买入日期
    earliest_date = min(h.get("buy_date", DEFAULT_START_DATE[:4] + "-" + DEFAULT_START_DATE[4:6] + "-" + DEFAULT_START_DATE[6:]) for h in holdings).replace("-", "")
    latest_date = datetime.now().strftime("%Y%m%d")

    # 获取基准收益
    benchmark_df = get_index_data(DEFAULT_BENCHMARK, start_date=earliest_date, end_date=latest_date)
    portfolio_ret = total_return()

    if benchmark_df.empty:
        return {
            "portfolio_return": portfolio_ret.get("total_pnl_pct"),
            "benchmark_return": None,
            "note": "无法获取基准数据",
        }

    close = benchmark_df["close"] if "close" in benchmark_df.columns else None
    if close is None or len(close) < 2:
        return {"error": "基准数据不足"}

    bench_start = close.iloc[-1]  # 最早
    bench_end = close.iloc[0]     # 最新
    bench_return = (bench_end - bench_start) / bench_start * 100 if bench_start > 0 else 0

    alpha = (portfolio_ret.get("total_pnl_pct", 0) or 0) - bench_return

    result = {
        "portfolio_return": portfolio_ret.get("total_pnl_pct"),
        "benchmark_return": round(bench_return, 2),
        "benchmark": "沪深300",
        "alpha": round(alpha, 2) if alpha else None,
    }

    if alpha is not None:
        if alpha > 0:
            result["verdict"] = f"跑赢基准 {alpha:.2f}%"
        else:
            result["verdict"] = f"跑输基准 {alpha:.2f}%"

    return result


def industry_exposure() -> dict:
    """行业暴露分析"""
    holdings = load()
    if not holdings:
        return {"error": "暂无持仓"}

    from python_tools.data.akshare_data import get_stock_info

    exposure = {}
    for h in holdings:
        try:
            info = get_stock_info(h["symbol"])
            industry = info.get("行业", info.get("所属行业", "未知"))
        except Exception:
            industry = "未知"

        value = h["cost_price"] * h["shares"]
        exposure[industry] = exposure.get(industry, 0) + value

    total = sum(exposure.values())
    result = {
        "exposure": {k: {"value": v, "weight": round(v/total*100, 1)} for k, v in exposure.items()},
        "total_value": round(total, 2),
        "industry_count": len(exposure),
    }

    return result


def performance_summary() -> str:
    """收益归因摘要 Markdown"""
    lines = ["## 收益归因分析\n"]

    # 总收益
    tr = total_return()
    if "error" not in tr:
        lines.append("### 总收益")
        lines.append(f"- 总成本: {tr['total_cost']:,.2f}")
        lines.append(f"- 总市值: {tr['total_market_value']:,.2f}")
        lines.append(f"- 总盈亏: {tr['total_pnl']:+,.2f}")
        lines.append(f"- 总收益率: {tr['total_pnl_pct']:+.2f}%")
        lines.append("")

    # 年化收益
    ann = annualized_return()
    if "portfolio_annualized" in ann and ann["portfolio_annualized"] is not None:
        lines.append(f"### 年化收益")
        lines.append(f"- 组合年化收益率: {ann['portfolio_annualized']:+.2f}%")

        for h in ann.get("holdings", []):
            lines.append(f"  - {h['name']}({h['symbol']}): "
                        f"{h['annualized_return']:+.2f}% (持有 {h['days_held']} 天)")
        lines.append("")

    # 基准对比
    bench = benchmark_comparison()
    if bench.get("benchmark_return") is not None:
        lines.append("### 基准对比")
        lines.append(f"- 组合收益: {bench['portfolio_return']:+.2f}%")
        lines.append(f"- {bench['benchmark']}收益: {bench['benchmark_return']:+.2f}%")
        lines.append(f"- Alpha: {bench['alpha']:+.2f}%")
        if "verdict" in bench:
            lines.append(f"- 结论: {bench['verdict']}")

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"

    if cmd == "total":
        print(total_return())
    elif cmd == "annualized":
        print(annualized_return())
    elif cmd == "benchmark":
        print(benchmark_comparison())
    elif cmd == "exposure":
        print(industry_exposure())
    elif cmd == "summary":
        print(performance_summary())
    else:
        print("用法: performance.py [total|annualized|benchmark|exposure|summary]")
