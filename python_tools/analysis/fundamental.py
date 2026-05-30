"""
基本面分析 — 盈利能力 / 成长性 / 财务健康 / DuPont 分解
使用同花顺（THS）财务数据源。
"""

import pandas as pd
import numpy as np
from typing import Optional

from python_tools.data.akshare_data import get_financial_ratios, get_stock_info


def analyze(symbol: str) -> dict:
    """
    基本面综合评分。
    返回 {"score": int, "details": {...}, "summary": str}
    """
    ratios = get_financial_ratios(symbol)
    info = get_stock_info(symbol)

    details = {}

    # ── 盈利能力 ──────────────────────────────────────────────
    details["profitability"] = _score_profitability(ratios)

    # ── 成长性 ─────────────────────────────────────────────────
    details["growth"] = _score_growth(ratios)

    # ── 财务健康 ──────────────────────────────────────────────
    details["health"] = _score_health(ratios)

    # ── 综合评分 ──────────────────────────────────────────────
    score = _composite_score(details)

    # ── 补充 info ──────────────────────────────────────────────
    details["info"] = info

    summary = _build_summary(symbol, score, details)
    return {"symbol": symbol, "score": score, "details": details, "summary": summary}


def _latest(df: pd.DataFrame, col: str) -> Optional[float]:
    """提取指定列的最近一期数值"""
    if df.empty or col not in df.columns:
        return None
    vals = df[col].dropna()
    if vals.empty:
        return None
    v = vals.iloc[-1]
    if isinstance(v, str):
        try:
            return float(v.replace("%", "").replace(",", ""))
        except (ValueError, TypeError):
            return None
    return float(v)


def _trend(df: pd.DataFrame, col: str, n: int = 3) -> Optional[float]:
    """提取指定列最近 n 期的平均值"""
    if df.empty or col not in df.columns:
        return None
    vals = []
    for v in df[col].dropna().iloc[-n:]:
        if isinstance(v, str):
            try:
                vals.append(float(v.replace("%", "").replace(",", "")))
            except (ValueError, TypeError):
                pass
        else:
            vals.append(float(v))
    return np.mean(vals) if vals else None


def _score_profitability(df: pd.DataFrame) -> dict:
    details = {}

    # 净资产收益率（ROE）—— 列名：净资产收益率
    roe_col = None
    for c in df.columns:
        if "净资产收益率" in c and "摊薄" not in c and "扣非" not in c:
            roe_col = c
            break
    if roe_col:
        avg_roe = _trend(df, roe_col, 4)  # 最近4个季度
        details["avg_roe"] = round(avg_roe, 2) if avg_roe else None

    # 销售毛利率
    gm_col = None
    for c in df.columns:
        if "销售毛利率" in c:
            gm_col = c
            break
    if gm_col:
        avg_gm = _trend(df, gm_col, 4)
        details["gross_margin"] = round(avg_gm, 2) if avg_gm else None

    # 销售净利率
    nm_col = None
    for c in df.columns:
        if "销售净利率" in c:
            nm_col = c
            break
    if nm_col:
        avg_nm = _trend(df, nm_col, 4)
        details["net_margin"] = round(avg_nm, 2) if avg_nm else None

    # 评分
    score = 0
    if details.get("avg_roe"):
        roe = details["avg_roe"]
        if roe >= 20:
            score += 25
        elif roe >= 15:
            score += 20
        elif roe >= 10:
            score += 12
        elif roe >= 5:
            score += 5

    if details.get("gross_margin"):
        gm = details["gross_margin"]
        if gm >= 60:
            score += 10
        elif gm >= 40:
            score += 8
        elif gm >= 25:
            score += 5

    if details.get("net_margin"):
        nm = details["net_margin"]
        if nm >= 20:
            score += 5

    details["profitability_score"] = min(score, 40)
    details["max_score"] = 40
    return details


def _score_growth(df: pd.DataFrame) -> dict:
    details = {}

    # 营收增长率
    rev_growth_cols = [c for c in df.columns if "营业总收入同比增长" in c or "营收同比增长" in c]
    if rev_growth_cols:
        g = _trend(df, rev_growth_cols[0], 4)
        details["revenue_growth"] = round(g, 2) if g else None

    # 净利润增长率
    profit_growth_cols = [c for c in df.columns if "净利润同比增长" in c and "扣非" not in c]
    if profit_growth_cols:
        g = _trend(df, profit_growth_cols[0], 4)
        details["profit_growth"] = round(g, 2) if g else None

    # 评分
    score = 0
    for key in ["revenue_growth", "profit_growth"]:
        g = details.get(key)
        if g is not None:
            if g >= 30:
                score += 15
            elif g >= 20:
                score += 12
            elif g >= 10:
                score += 8
            elif g >= 0:
                score += 4
            else:
                score -= 5

    details["growth_score"] = max(min(score, 30), -5)
    details["max_score"] = 30
    return details


def _score_health(df: pd.DataFrame) -> dict:
    details = {}

    # 资产负债率
    debt_cols = [c for c in df.columns if "资产负债率" in c]
    if debt_cols:
        d = _latest(df, debt_cols[0])
        details["debt_ratio"] = round(d, 2) if d else None

    # 评分（资产负债率低=好）
    score = 0
    if details.get("debt_ratio") is not None:
        dr = details["debt_ratio"]
        if dr < 30:
            score += 15
        elif dr < 50:
            score += 10
        elif dr < 70:
            score += 5

    # EPS
    eps_cols = [c for c in df.columns if "基本每股收益" in c]
    if eps_cols:
        eps = _latest(df, eps_cols[0])
        details["eps"] = round(eps, 2) if eps else None
    if details.get("eps") and details["eps"] > 1:
        score += 5

    # BPS
    bps_cols = [c for c in df.columns if "每股净资产" in c]
    if bps_cols:
        bps = _latest(df, bps_cols[0])
        details["bps"] = round(bps, 2) if bps else None

    details["health_score"] = min(score, 30)
    details["max_score"] = 30
    return details


def _composite_score(details: dict) -> int:
    """综合评分（满分 100）"""
    score = 0

    p = details.get("profitability", {})
    score += p.get("profitability_score", 0)

    g = details.get("growth", {})
    score += g.get("growth_score", 0)

    h = details.get("health", {})
    score += h.get("health_score", 0)

    # 基础分
    score += 10

    return min(round(score), 100)


def _build_summary(symbol: str, score: int, details: dict) -> str:
    p = details.get("profitability", {})
    g = details.get("growth", {})
    h = details.get("health", {})
    info = details.get("info", {})

    name = info.get("股票简称", symbol)

    lines = [f"## {name}（{symbol}）基本面分析\n"]
    lines.append(f"**综合评分**: {score}/100")

    if score >= 80:
        lines.append("**评价**: 优秀，基本面扎实")
    elif score >= 60:
        lines.append("**评价**: 良好，基本面健康")
    elif score >= 40:
        lines.append("**评价**: 一般，关注短板")
    else:
        lines.append("**评价**: 较弱，风险较高")

    lines.append(f"\n### 盈利能力")
    lines.append(f"- 近4季度平均 ROE: {p.get('avg_roe', 'N/A')}%")
    lines.append(f"- 近4季度平均毛利率: {p.get('gross_margin', 'N/A')}%")
    lines.append(f"- 近4季度平均净利率: {p.get('net_margin', 'N/A')}%")

    lines.append(f"\n### 成长性")
    lines.append(f"- 近4季度平均营收增长: {g.get('revenue_growth', 'N/A')}%")
    lines.append(f"- 近4季度平均利润增长: {g.get('profit_growth', 'N/A')}%")

    lines.append(f"\n### 财务健康")
    lines.append(f"- 资产负债率: {h.get('debt_ratio', 'N/A')}%")
    lines.append(f"- 基本每股收益: {h.get('eps', 'N/A')}")
    lines.append(f"- 每股净资产: {h.get('bps', 'N/A')}")

    if info:
        lines.append(f"\n### 最新报告期 ({info.get('报告期', 'N/A')})")
        lines.append(f"- 净利润: {info.get('净利润', 'N/A')}")
        lines.append(f"- 营业总收入: {info.get('营业总收入', 'N/A')}")

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "600519"
    result = analyze(symbol)
    print(result["summary"])
