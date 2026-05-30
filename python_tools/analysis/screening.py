"""
多因子选股 — 按条件筛选股票池
"""

import pandas as pd
import numpy as np
from typing import Optional
import time

from python_tools.data.akshare_data import (
    get_stock_list,
    get_financial_ratios,
    get_stock_info,
    get_industry_stocks,
)


class ScreeningCriteria:
    """筛选条件"""
    def __init__(self):
        self.conditions = []

    def pe_between(self, low: Optional[float] = None, high: Optional[float] = None):
        self.conditions.append(("pe", low, high))
        return self

    def pb_between(self, low: Optional[float] = None, high: Optional[float] = None):
        self.conditions.append(("pb", low, high))
        return self

    def roe_above(self, threshold: float):
        self.conditions.append(("roe_min", threshold))
        return self

    def roe_between(self, low: float, high: float):
        self.conditions.append(("roe_range", low, high))
        return self

    def market_cap_above(self, cap_yi: float):
        """市值大于 cap_yi 亿元"""
        self.conditions.append(("market_cap_min", cap_yi))
        return self

    def market_cap_between(self, low_yi: float, high_yi: float):
        self.conditions.append(("market_cap_range", low_yi, high_yi))
        return self

    def gross_margin_above(self, threshold: float):
        self.conditions.append(("gross_margin_min", threshold))
        return self

    def revenue_growth_above(self, threshold: float):
        self.conditions.append(("revenue_growth_min", threshold))
        return self

    def industry(self, name: str):
        self.conditions.append(("industry", name))
        return self


def screen(criteria: ScreeningCriteria, limit: int = 50) -> pd.DataFrame:
    """
    执行多因子筛选。
    返回符合条件的结果 DataFrame，按综合评分排序。
    """
    # 先获取候选池
    candidates = _get_candidates(criteria)

    if not candidates:
        return pd.DataFrame()

    results = []
    total = len(candidates)
    for idx, (symbol, name) in enumerate(candidates):
        if idx % 20 == 0:
            print(f"[screening] 分析进度: {idx}/{total} ({idx/total*100:.0f}%)")

        try:
            score, details = _evaluate_stock(symbol, name, criteria)
            if score is not None:
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "score": score,
                    **details,
                })
        except Exception:
            continue

        # 限速
        time.sleep(0.1)

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    df = df.sort_values("score", ascending=False).head(limit)
    return df


def _get_candidates(criteria: ScreeningCriteria) -> list:
    """获取候选股票池"""
    industry_name = None
    for cond in criteria.conditions:
        if cond[0] == "industry":
            industry_name = cond[1]
            break

    if industry_name:
        stocks_df = get_industry_stocks(industry_name)
        if not stocks_df.empty:
            if "代码" in stocks_df.columns:
                return list(zip(stocks_df["代码"], stocks_df.get("名称", stocks_df["代码"])))
            else:
                return [(s, s) for s in stocks_df.iloc[:, 0].tolist()]

    # 全市场
    stocks_df = get_stock_list()
    if not stocks_df.empty:
        if "symbol" in stocks_df.columns:
            return list(zip(stocks_df["symbol"], stocks_df.get("name", stocks_df["symbol"])))
        else:
            # 尝试前两列
            return [(row[0], row[1] if len(row) > 1 else row[0])
                    for _, row in stocks_df.head(500).iterrows()]

    return []


def _evaluate_stock(symbol: str, name: str, criteria: ScreeningCriteria) -> tuple:
    """评估单只股票，返回 (score, details) 或 (None, None)"""
    try:
        info = get_stock_info(symbol)
        ratios = get_financial_ratios(symbol)
    except Exception:
        return None, None

    details = {}
    score = 0

    # 提取指标
    pe_val = _extract_first(ratios, "市盈率")
    pb_val = _extract_first(ratios, "市净率")
    roe_val = _extract_first(ratios, "净资产收益率")
    gross_margin = _extract_first(ratios, "销售毛利率")
    total_cap = info.get("总市值")

    # 检查每个条件
    passed = True
    for cond in criteria.conditions:
        cond_type = cond[0]

        if cond_type == "pe":
            _, low, high = cond
            if pe_val is None:
                passed = False
                break
            if low is not None and pe_val < low:
                passed = False
                break
            if high is not None and pe_val > high:
                passed = False
                break

        elif cond_type == "pb":
            _, low, high = cond
            if pb_val is None:
                passed = False
                break
            if low is not None and pb_val < low:
                passed = False
                break
            if high is not None and pb_val > high:
                passed = False
                break

        elif cond_type == "roe_min":
            threshold = cond[1]
            if roe_val is None or roe_val < threshold:
                passed = False
                break

        elif cond_type == "roe_range":
            _, low, high = cond
            if roe_val is None or roe_val < low or roe_val > high:
                passed = False
                break

        elif cond_type == "market_cap_min":
            threshold = cond[1] * 1e8  # 亿元转元
            if total_cap is None:
                passed = False
                break
            try:
                if float(total_cap) < threshold:
                    passed = False
                    break
            except (ValueError, TypeError):
                passed = False
                break

        elif cond_type == "gross_margin_min":
            threshold = cond[1]
            if gross_margin is None or gross_margin < threshold:
                passed = False
                break

    if not passed:
        return None, None

    # 综合评分
    details["pe"] = pe_val
    details["pb"] = pb_val
    details["roe"] = roe_val
    details["gross_margin"] = gross_margin
    details["market_cap"] = total_cap

    # ROE 越高越好（满分 30）
    if roe_val is not None:
        score += min(roe_val / 20 * 30, 30)

    # PE 越低越好（满分 20）
    if pe_val is not None and pe_val > 0:
        score += max(0, min((50 - pe_val) / 50 * 20, 20))

    # 毛利率越高越好（满分 20）
    if gross_margin is not None:
        score += min(gross_margin / 40 * 20, 20)

    # 基本面综合（满分 30）
    # 简化评分
    if roe_val and roe_val >= 15:
        score += 15
    if gross_margin and gross_margin >= 30:
        score += 15

    return round(min(score, 100), 1), details


def _extract_first(df: pd.DataFrame, keyword: str) -> Optional[float]:
    """从财务指标 DataFrame 提取第一个匹配值"""
    if df.empty:
        return None
    for _, r in df.iterrows():
        if keyword in str(r.iloc[0]):
            try:
                return float(r.iloc[1])
            except (ValueError, TypeError):
                return None
    return None


def format_results(df: pd.DataFrame) -> str:
    """格式化筛选结果为 Markdown 表格"""
    if df.empty:
        return "无符合条件的结果"

    lines = [f"## 多因子选股结果（共 {len(df)} 只）\n"]
    lines.append("| 排名 | 代码 | 名称 | 评分 | PE | PB | ROE(%) | 毛利率(%) |")
    lines.append("|------|------|------|------|----|----|--------|-----------|")

    for i, (_, row) in enumerate(df.iterrows(), 1):
        lines.append(
            f"| {i} | {row['symbol']} | {row['name']} | "
            f"{row['score']} | {row.get('pe', 'N/A')} | {row.get('pb', 'N/A')} | "
            f"{row.get('roe', 'N/A')} | {row.get('gross_margin', 'N/A')} |"
        )

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # 示例：ROE > 15%, PE < 30, 毛利率 > 30%
    criteria = ScreeningCriteria()
    criteria.roe_above(15).pe_between(0, 30).gross_margin_above(30)

    print("筛选条件: ROE>15%, PE<30, 毛利率>30%")
    results = screen(criteria, limit=20)
    print(format_results(results))
