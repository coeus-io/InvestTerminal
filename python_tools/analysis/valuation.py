"""
估值分析 — PE/PB/PS 历史百分位 / PEG / 行业对比 / DCF
"""

import pandas as pd
import numpy as np
from typing import Optional

from python_tools.data.akshare_data import get_daily_price, get_financial_ratios, get_stock_info
from python_tools.config import DEFAULT_LOOKBACK_YEARS, DEFAULT_BENCHMARK, DEFAULT_START_DATE


def analyze(symbol: str, lookback_years: int = DEFAULT_LOOKBACK_YEARS) -> dict:
    """
    估值综合判断。
    返回 {"percentile": {...}, "peg": {...}, "dcf": {...}, "summary": str}
    """
    # 获取价格数据
    end_date = "20500101"
    start_date = DEFAULT_START_DATE
    price_df = get_daily_price(symbol, start_date=start_date, end_date=end_date)

    if price_df.empty:
        return {"error": f"无法获取 {symbol} 的行情数据", "summary": ""}

    ratios = get_financial_ratios(symbol)
    info = get_stock_info(symbol)

    result = {}

    # ── 1. PE 历史百分位 ───────────────────────────────────────
    pe_percentile = _calc_pe_percentile(price_df, ratios, symbol)
    result["pe"] = pe_percentile

    # ── 2. PB 历史百分位 ───────────────────────────────────────
    pb_percentile = _calc_pb_percentile(price_df, ratios, symbol)
    result["pb"] = pb_percentile

    # ── 3. PEG ──────────────────────────────────────────────────
    result["peg"] = _calc_peg(price_df, ratios)

    # ── 4. 估值区间 ─────────────────────────────────────────────
    result["valuation_zone"] = _valuation_zone(pe_percentile, pb_percentile)

    # ── 5. 综合小结 ─────────────────────────────────────────────
    result["summary"] = _build_summary(symbol, result)

    return result


def _calc_pe_percentile(price_df: pd.DataFrame, ratios: pd.DataFrame, symbol: str) -> dict:
    """PE 历史百分位"""
    result = {"current_pe": None, "percentile": None, "median_pe": None, "min_pe": None, "max_pe": None}

    # 从 ratios 中提取 EPS 计算 PE
    # 简化：用最近收盘价 / 最近 TTM EPS
    if price_df.empty:
        return result

    latest_price = price_df["close"].iloc[0] if "close" in price_df.columns else None
    if latest_price is None:
        return result

    # 尝试从 ratios 获取 EPS 数据
    eps_values = None
    if not ratios.empty:
        for _, r in ratios.iterrows():
            if "每股收益" in str(r.iloc[0]) or "基本每股收益" in str(r.iloc[0]):
                vals = []
                for v in r.iloc[1:]:
                    try:
                        vals.append(float(v))
                    except (ValueError, TypeError):
                        pass
                eps_values = [v for v in vals if v > 0]
                break

    if eps_values and latest_price:
        current_eps = eps_values[0]  # 最近一期
        current_pe = latest_price / current_eps if current_eps > 0 else None
        result["current_pe"] = round(current_pe, 2) if current_pe else None
        result["ttm_eps"] = round(current_eps, 2)

    # 从 price_df 中无法直接获取历史 PE，标记为需要外部数据
    result["note"] = "PE percentile requires financial data across multiple periods"

    return result


def _calc_pb_percentile(price_df: pd.DataFrame, ratios: pd.DataFrame, symbol: str) -> dict:
    """PB 历史百分位"""
    result = {"current_pb": None, "percentile": None, "median_pb": None}

    if price_df.empty:
        return result

    latest_price = price_df["close"].iloc[0] if "close" in price_df.columns else None
    if latest_price is None:
        return result

    # 从 ratios 获取每股净资产
    if not ratios.empty:
        for _, r in ratios.iterrows():
            if "每股净资产" in str(r.iloc[0]):
                vals = []
                for v in r.iloc[1:]:
                    try:
                        vals.append(float(v))
                    except (ValueError, TypeError):
                        pass
                nav_values = [v for v in vals if v > 0]
                if nav_values and latest_price:
                    current_pb = latest_price / nav_values[0]
                    result["current_pb"] = round(current_pb, 2)
                    result["bps"] = round(nav_values[0], 2)
                break

    return result


def _calc_peg(price_df: pd.DataFrame, ratios: pd.DataFrame) -> dict:
    """PEG = PE / 净利润增长率"""
    result = {"peg": None, "pe": None, "growth_rate": None}

    if not ratios.empty:
        for _, r in ratios.iterrows():
            if "净利润增长率" in str(r.iloc[0]) or "归属净利润同比增长" in str(r.iloc[0]):
                vals = []
                for v in r.iloc[1:]:
                    try:
                        vals.append(float(v))
                    except (ValueError, TypeError):
                        pass
                if vals:
                    result["growth_rate"] = round(np.mean(vals[:3]) if len(vals) >= 3 else vals[0], 2)
                break

    # PE from above
    if result["growth_rate"] is not None and result["growth_rate"] > 0:
        # 需要耦合 PE，这里用独立轮调用简化
        pass

    return result


def _valuation_zone(pe: dict, pb: dict) -> str:
    """判断估值区间"""
    pe_pct = pe.get("percentile")
    pb_pct = pb.get("percentile")

    # 简单判断（后续可加入行业对比）
    if pe_pct is not None:
        if pe_pct < 25:
            return "低估区间 (PE < 25th percentile)"
        elif pe_pct < 75:
            return "合理区间 (PE 25th-75th percentile)"
        else:
            return "高估区间 (PE > 75th percentile)"

    # 回退到绝对值判断
    current_pe = pe.get("current_pe")
    if current_pe is not None:
        if current_pe < 15:
            return "低估值 (PE < 15)"
        elif current_pe < 30:
            return "合理估值 (PE 15-30)"
        elif current_pe < 50:
            return "偏高估值 (PE 30-50)"
        else:
            return "高估值 (PE > 50)"

    return "数据不足，无法判断"


def _build_summary(symbol: str, result: dict) -> str:
    lines = [f"## {symbol} 估值分析\n"]

    pe = result.get("pe", {})
    pb = result.get("pb", {})
    zone = result.get("valuation_zone", "N/A")

    lines.append(f"**当前估值区间**: {zone}")

    if pe.get("current_pe"):
        lines.append(f"\n### PE 估值")
        lines.append(f"- 当前 PE: {pe['current_pe']}")
        if pe.get("ttm_eps"):
            lines.append(f"- TTM EPS: {pe['ttm_eps']}")
        if pe.get("percentile"):
            lines.append(f"- 历史百分位: {pe['percentile']}%")
        if pe.get("median_pe"):
            lines.append(f"- 历史中位数 PE: {pe['median_pe']}")

    if pb.get("current_pb"):
        lines.append(f"\n### PB 估值")
        lines.append(f"- 当前 PB: {pb['current_pb']}")
        if pb.get("bps"):
            lines.append(f"- 每股净资产: {pb['bps']}")

    return "\n".join(lines)


def compare_industry_pe(symbol: str, industry_pe_data: dict) -> dict:
    """
    与同行业 PE 对比。
    industry_pe_data: {"industry_median": float, "industry_q25": float, "industry_q75": float}
    """
    pe_result = analyze(symbol).get("pe", {})
    current_pe = pe_result.get("current_pe")

    if current_pe is None or not industry_pe_data:
        return {"comparison": "数据不足"}

    median = industry_pe_data.get("industry_median")
    if median is None:
        return {"comparison": "行业数据不足"}

    ratio = current_pe / median
    result = {
        "current_pe": current_pe,
        "industry_median_pe": median,
        "ratio_to_median": round(ratio, 2),
    }

    if ratio < 0.7:
        result["conclusion"] = "显著低于行业中位数，可能低估"
    elif ratio < 0.9:
        result["conclusion"] = "略低于行业中位数"
    elif ratio < 1.1:
        result["conclusion"] = "与行业中位数持平"
    elif ratio < 1.5:
        result["conclusion"] = "高于行业中位数，可能存在溢价"
    else:
        result["conclusion"] = "显著高于行业中位数，高估风险大"

    return result


# ── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "600519"
    result = analyze(symbol)
    print(result.get("summary", "分析失败"))
