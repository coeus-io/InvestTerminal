"""
行业分析 — 成分股 / ROE排名 / 行业集中度

THS 数据格式适配：get_stock_info() 返回 dict（key-value），
ROE/毛利率等直接从 dict 解析百分比字符串。
"""

import pandas as pd
import numpy as np
from typing import Optional

from python_tools.data.akshare_data import (
    get_industry_classification,
    get_industry_stocks,
    get_industry_stocks_meta,
    get_stock_info,
)


def _parse_pct(val: str) -> Optional[float]:
    """解析百分比字符串 '10.57%' → 10.57"""
    if not val or not isinstance(val, str):
        return None
    try:
        return float(val.replace("%", "").replace(",", ""))
    except (ValueError, TypeError):
        return None


def _parse_num(val) -> Optional[float]:
    """解析数值字符串"""
    if val is None:
        return None
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return None


def list_industries() -> pd.DataFrame:
    """列出所有申万行业"""
    return get_industry_classification()


def get_stocks_in_industry(industry_name: str) -> pd.DataFrame:
    """获取某行业的全部成分股"""
    return get_industry_stocks(industry_name)


def industry_overview(industry_name: str, sample_limit: int = 20) -> dict:
    """
    行业概览 — ROE 排名、集中度、行业均值。
    从 get_stock_info()（THS 源）提取指标，避免依赖行-label 旧格式。
    """
    meta_result = get_industry_stocks_meta(industry_name)
    stocks = meta_result["stocks"]
    data_source = meta_result.get("source", "unknown")
    data_updated = meta_result.get("updated_at")
    data_stale = meta_result.get("stale_days")

    if stocks.empty:
        return {"error": f"未找到行业 '{industry_name}' 的成分股（API 不可达且本地文件无此行业）"}

    result = {
        "industry": industry_name,
        "stock_count": len(stocks),
        "top_stocks": [],
        "valuation": {},
        "concentration": {},
        "_meta": {
            "source": data_source,
            "updated_at": data_updated,
            "stale_days": data_stale,
        },
    }

    # 提取符号列表（兼容不同列名）
    if "symbol" in stocks.columns:
        symbols = stocks["symbol"].tolist()[:sample_limit]
    elif "代码" in stocks.columns:
        symbols = stocks["代码"].tolist()[:sample_limit]
    else:
        symbols = stocks.iloc[:, 0].tolist()[:sample_limit]

    # 逐只收集
    roe_list = []
    gross_margin_list = []
    net_margin_list = []
    market_cap_list = []
    # 从 JSON/API 构建 symbol→name 映射，用于 THS 不知道名称时的回退
    _symbol_to_name = {}
    if "symbol" in stocks.columns and "name" in stocks.columns:
        for _, r in stocks.iterrows():
            _symbol_to_name[str(r["symbol"])] = str(r["name"])

    stock_details = []

    for s in symbols:
        try:
            info = get_stock_info(s)

            # 名称：优先 THS，其次 JSON 里的名称
            name = info.get("股票简称", "") if info else ""
            if not name or name == str(s):
                name = _symbol_to_name.get(str(s), str(s))

            # ROE (THS)
            roe = _parse_pct(info.get("净资产收益率", "")) if info else None

            # 毛利率 (THS)
            gm = _parse_pct(info.get("销售毛利率", "")) if info else None

            # 净利率 (THS)
            nm = _parse_pct(info.get("销售净利率", "")) if info else None

            # 市值 (THS)
            cap = info.get("总市值") if info else None
            cap_num = _parse_num(cap) if cap else None

            if roe is not None:
                roe_list.append(roe)
            if gm is not None:
                gross_margin_list.append(gm)
            if nm is not None:
                net_margin_list.append(nm)
            if cap_num is not None:
                market_cap_list.append(cap_num)

            stock_details.append({
                "symbol": str(s),
                "name": name,
                "roe": roe,
                "gross_margin": gm,
                "net_margin": nm,
                "market_cap": cap_num,
            })

        except Exception:
            continue

    # 估值/盈利中枢
    val = {}
    if roe_list:
        val["roe_median"] = round(np.median(roe_list), 2)
        val["roe_mean"] = round(np.mean(roe_list), 2)
        val["roe_q25"] = round(np.percentile(roe_list, 25), 2)
        val["roe_q75"] = round(np.percentile(roe_list, 75), 2)
    if gross_margin_list:
        val["gross_margin_median"] = round(np.median(gross_margin_list), 2)
    if net_margin_list:
        val["net_margin_median"] = round(np.median(net_margin_list), 2)
    result["valuation"] = val

    # 集中度 CR5/CR10
    if market_cap_list:
        sorted_cap = sorted(market_cap_list, reverse=True)
        total_cap = sum(sorted_cap)
        if total_cap > 0:
            cr5 = round(sum(sorted_cap[:5]) / total_cap * 100, 1) if len(sorted_cap) >= 5 else None
            cr10 = round(sum(sorted_cap[:10]) / total_cap * 100, 1) if len(sorted_cap) >= 10 else None
            result["concentration"] = {
                "cr5": cr5,
                "cr10": cr10,
                "total_market_cap_yi": round(total_cap / 1e8, 0),
            }

    # Top 排名
    result["top_by_roe"] = sorted(
        [s for s in stock_details if s["roe"] is not None],
        key=lambda x: x["roe"], reverse=True,
    )[:10]

    result["top_by_gross_margin"] = sorted(
        [s for s in stock_details if s["gross_margin"] is not None],
        key=lambda x: x["gross_margin"], reverse=True,
    )[:10]

    return result


def rank_in_industry(symbol: str, industry_name: str) -> dict:
    """某股票在行业内的 ROE 排名"""
    overview = industry_overview(industry_name)
    if "error" in overview:
        return overview

    all_stocks = overview.get("top_by_roe", [])
    target = None
    for s in all_stocks:
        if s["symbol"] == symbol:
            target = s
            break

    if target is None:
        return {"error": f"股票 {symbol} 不在 {industry_name} ROE 数据中"}

    roe_list = [s["roe"] for s in all_stocks if s["roe"] is not None]
    rank = sum(1 for v in roe_list if v > target["roe"]) + 1

    return {
        "symbol": symbol,
        "name": target["name"],
        "industry": industry_name,
        "roe": target["roe"],
        "rank": rank,
        "total": len(roe_list),
        "percentile": round((1 - rank / len(roe_list)) * 100, 1) if roe_list else None,
    }


def industry_summary(industry_name: str) -> str:
    """行业分析报告 Markdown"""
    overview = industry_overview(industry_name)
    if "error" in overview:
        return overview["error"]

    lines = [f"## {industry_name} 行业分析\n"]

    # 数据源标注
    meta = overview.get("_meta", {})
    source = meta.get("source", "unknown")
    stale = meta.get("stale_days")
    if source == "live":
        lines.append(f"🟢 实时数据 | **成分股数量**: {overview['stock_count']}")
    elif source == "cache":
        stale_str = f"，{stale}天未更新" if stale else ""
        lines.append(f"🟡 本地缓存{stale_str} | **成分股数量**: {overview['stock_count']}")
        if stale and stale > 30:
            lines.append(f"> ⚠️ 缓存已超过 {stale} 天未更新，建议在不受限网络上运行 `refresh_industry_cache()`")
    else:
        lines.append(f"**成分股数量**: {overview['stock_count']}")

    val = overview.get("valuation", {})
    if val:
        lines.append(f"\n### 盈利指标")
        lines.append(f"- ROE 中位数: {val.get('roe_median', 'N/A')}%")
        lines.append(f"- ROE 均值: {val.get('roe_mean', 'N/A')}%")
        lines.append(f"- ROE 四分位: Q1={val.get('roe_q25', 'N/A')}%, Q3={val.get('roe_q75', 'N/A')}%")
        lines.append(f"- 毛利率中位数: {val.get('gross_margin_median', 'N/A')}%")
        lines.append(f"- 净利率中位数: {val.get('net_margin_median', 'N/A')}%")

    conc = overview.get("concentration", {})
    if conc:
        lines.append(f"\n### 集中度")
        if conc.get("cr5"):
            lines.append(f"- CR5: {conc['cr5']}%")
        if conc.get("cr10"):
            lines.append(f"- CR10: {conc['cr10']}%")
        if conc.get("total_market_cap_yi"):
            lines.append(f"- 总市值: {conc['total_market_cap_yi']} 亿元")

    top_roe = overview.get("top_by_roe", [])[:5]
    if top_roe:
        lines.append(f"\n### ROE Top 5")
        for i, s in enumerate(top_roe, 1):
            lines.append(f"{i}. {s['name']}({s['symbol']}) — ROE: {s['roe']}%")

    top_gm = overview.get("top_by_gross_margin", [])[:5]
    if top_gm:
        lines.append(f"\n### 毛利率 Top 5")
        for i, s in enumerate(top_gm, 1):
            lines.append(f"{i}. {s['name']}({s['symbol']}) — 毛利率: {s['gross_margin']}%")

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    industry = sys.argv[1] if len(sys.argv) > 1 else "白酒"
    print(industry_summary(industry))
