"""
技术分析 — 均线 / MACD / RSI / KDJ / 趋势判断
"""

import pandas as pd
import numpy as np
from typing import Optional

from python_tools.data.akshare_data import get_daily_price
from python_tools.config import DEFAULT_START_DATE


def analyze(symbol: str, start_date: str = None, end_date: str = None) -> dict:
    """
    技术面综合分析。
    返回指标数据和趋势判断。
    """
    if start_date is None:
        start_date = DEFAULT_START_DATE
    if end_date is None:
        end_date = "20500101"

    df = get_daily_price(symbol, start_date=start_date, end_date=end_date)
    if df.empty:
        return {"error": f"无法获取 {symbol} 的行情数据"}

    df = df.sort_values("date")

    result = {
        "symbol": symbol,
        "latest_price": float(df["close"].iloc[-1]),
        "latest_date": str(df["date"].iloc[-1])[:10],
    }

    # ── 均线系统 ──────────────────────────────────────────────
    mas = _calc_moving_averages(df)
    result["ma"] = mas

    # ── MACD ──────────────────────────────────────────────────
    macd = _calc_macd(df)
    result["macd"] = macd

    # ── RSI ───────────────────────────────────────────────────
    rsi = _calc_rsi(df)
    result["rsi"] = rsi

    # ── KDJ ───────────────────────────────────────────────────
    kdj = _calc_kdj(df)
    result["kdj"] = kdj

    # ── 趋势判断 ──────────────────────────────────────────────
    result["trend"] = _judge_trend(result)

    # ── 总结 ──────────────────────────────────────────────────
    result["summary"] = _build_tech_summary(symbol, result)

    return result


def _calc_moving_averages(df: pd.DataFrame) -> dict:
    """均线系统"""
    close = df["close"]
    ma5 = close.rolling(5).mean().iloc[-1]
    ma10 = close.rolling(10).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1]
    ma120 = close.rolling(120).mean().iloc[-1]

    current = close.iloc[-1]

    result = {
        "ma5": round(ma5, 2) if not pd.isna(ma5) else None,
        "ma10": round(ma10, 2) if not pd.isna(ma10) else None,
        "ma20": round(ma20, 2) if not pd.isna(ma20) else None,
        "ma60": round(ma60, 2) if not pd.isna(ma60) else None,
        "ma120": round(ma120, 2) if not pd.isna(ma120) else None,
    }

    # 多/空头排列
    if ma5 and ma10 and ma20 and ma60:
        if float(ma5) > float(ma10) > float(ma20) > float(ma60):
            result["alignment"] = "多头排列"
        elif float(ma5) < float(ma10) < float(ma20) < float(ma60):
            result["alignment"] = "空头排列"
        else:
            result["alignment"] = "均线缠绕（震荡）"

    # 价格相对均线位置
    result["above_ma20"] = current > ma20 if not pd.isna(ma20) else None
    result["above_ma60"] = current > ma60 if not pd.isna(ma60) else None

    return result


def _calc_macd(df: pd.DataFrame) -> dict:
    """MACD 指标"""
    close = df["close"]

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd_bar = 2 * (dif - dea)

    last_dif = dif.iloc[-1]
    last_dea = dea.iloc[-1]
    last_bar = macd_bar.iloc[-1]
    prev_bar = macd_bar.iloc[-2] if len(macd_bar) >= 2 else 0

    # 信号判断
    signal = None
    if last_dif > last_dea:
        signal = "看涨（DIF 在 DEA 上方）"
    else:
        signal = "看跌（DIF 在 DEA 下方）"

    # 金叉/死叉
    crossover = None
    if len(dif) >= 2 and len(dea) >= 2:
        prev_dif, prev_dea = dif.iloc[-2], dea.iloc[-2]
        if prev_dif <= prev_dea and last_dif > last_dea:
            crossover = "金叉（买入信号）"
        elif prev_dif >= prev_dea and last_dif < last_dea:
            crossover = "死叉（卖出信号）"

    return {
        "dif": round(float(last_dif), 4) if not pd.isna(last_dif) else None,
        "dea": round(float(last_dea), 4) if not pd.isna(last_dea) else None,
        "macd": round(float(last_bar), 4) if not pd.isna(last_bar) else None,
        "signal": signal,
        "crossover": crossover,
        "trend": "红柱放大" if last_bar > prev_bar else "绿柱放大" if last_bar < 0 else "柱状线收缩",
    }


def _calc_rsi(df: pd.DataFrame, period: int = 14) -> dict:
    """RSI 指标"""
    close = df["close"]
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)

    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    rsi6 = _rsi_period(close, 6)
    rsi14 = _rsi_period(close, 14)
    rsi24 = _rsi_period(close, 24)

    last_rsi14 = rsi14.iloc[-1] if not pd.isna(rsi14.iloc[-1]) else None

    # 判断超买超卖
    zone = None
    if last_rsi14 is not None:
        if last_rsi14 > 80:
            zone = "严重超买"
        elif last_rsi14 > 70:
            zone = "超买"
        elif last_rsi14 < 20:
            zone = "严重超卖"
        elif last_rsi14 < 30:
            zone = "超卖"
        else:
            zone = "中性"

    return {
        "rsi6": round(float(rsi6.iloc[-1]), 2) if not pd.isna(rsi6.iloc[-1]) else None,
        "rsi14": round(float(last_rsi14), 2) if last_rsi14 else None,
        "rsi24": round(float(rsi24.iloc[-1]), 2) if not pd.isna(rsi24.iloc[-1]) else None,
        "zone": zone,
    }


def _rsi_period(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _calc_kdj(df: pd.DataFrame, n: int = 9) -> dict:
    """KDJ 指标"""
    close = df["close"]
    high = df["high"]
    low = df["low"]

    lowest_low = low.rolling(n).min()
    highest_high = high.rolling(n).max()

    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100

    k = rsv.ewm(alpha=1/3, adjust=False).mean()
    d = k.ewm(alpha=1/3, adjust=False).mean()
    j = 3 * k - 2 * d

    last_k = k.iloc[-1]
    last_d = d.iloc[-1]
    last_j = j.iloc[-1]

    # 信号
    signal = None
    if last_j is not None and not pd.isna(last_j):
        if last_j > 100:
            signal = "超买区，短线回调风险"
        elif last_j < 0:
            signal = "超卖区，短线反弹可能"
        elif last_k > last_d:
            signal = "K 线在 D 线上方，偏多"
        else:
            signal = "K 线在 D 线下方，偏空"

    return {
        "k": round(float(last_k), 2) if not pd.isna(last_k) else None,
        "d": round(float(last_d), 2) if not pd.isna(last_d) else None,
        "j": round(float(last_j), 2) if not pd.isna(last_j) else None,
        "signal": signal,
    }


def _judge_trend(result: dict) -> dict:
    """综合趋势判断"""
    bullish = 0
    bearish = 0
    reasons = []

    # 均线
    ma = result.get("ma", {})
    if ma.get("alignment") == "多头排列":
        bullish += 2
        reasons.append("均线多头排列")
    elif ma.get("alignment") == "空头排列":
        bearish += 2
        reasons.append("均线空头排列")

    if ma.get("above_ma60"):
        bullish += 1
    else:
        bearish += 1

    # MACD
    macd = result.get("macd", {})
    if macd.get("crossover") == "金叉（买入信号）":
        bullish += 1
        reasons.append("MACD 金叉")
    elif macd.get("crossover") == "死叉（卖出信号）":
        bearish += 1
        reasons.append("MACD 死叉")

    if "看涨" in str(macd.get("signal", "")):
        bullish += 1
    else:
        bearish += 1

    # RSI
    rsi = result.get("rsi", {})
    if rsi.get("zone") in ("超卖", "严重超卖"):
        bullish += 1
        reasons.append("RSI 超卖（可能反弹）")
    elif rsi.get("zone") in ("超买", "严重超买"):
        bearish += 1
        reasons.append("RSI 超买（可能回调）")

    # 结论
    total = bullish + bearish
    if total == 0:
        conclusion = "信号不明确"
    elif bullish >= bearish + 2:
        conclusion = "偏多"
    elif bearish >= bullish + 2:
        conclusion = "偏空"
    else:
        conclusion = "震荡"

    return {
        "bullish_signals": bullish,
        "bearish_signals": bearish,
        "conclusion": conclusion,
        "reasons": reasons,
    }


def _build_tech_summary(symbol: str, result: dict) -> str:
    lines = [f"## {symbol} 技术分析\n"]

    latest = result.get("latest_price")
    latest_date = result.get("latest_date")
    lines.append(f"**最新价**: {latest}（{latest_date}）")

    trend = result.get("trend", {})
    lines.append(f"\n### 趋势判断: {trend.get('conclusion', 'N/A')}")
    lines.append(f"- 多头信号: {trend.get('bullish_signals', 0)}")
    lines.append(f"- 空头信号: {trend.get('bearish_signals', 0)}")
    if trend.get("reasons"):
        lines.append(f"- 信号: {', '.join(trend['reasons'])}")

    ma = result.get("ma", {})
    lines.append(f"\n### 均线系统")
    lines.append(f"- MA5: {ma.get('ma5')} | MA10: {ma.get('ma10')} | MA20: {ma.get('ma20')}")
    lines.append(f"- MA60: {ma.get('ma60')} | MA120: {ma.get('ma120')}")
    lines.append(f"- 排列: {ma.get('alignment', 'N/A')}")

    macd = result.get("macd", {})
    lines.append(f"\n### MACD")
    lines.append(f"- DIF: {macd.get('dif')} | DEA: {macd.get('dea')} | MACD: {macd.get('macd')}")
    lines.append(f"- 信号: {macd.get('signal')}")
    if macd.get("crossover"):
        lines.append(f"- 交叉: {macd['crossover']}")

    rsi = result.get("rsi", {})
    lines.append(f"\n### RSI")
    lines.append(f"- RSI6: {rsi.get('rsi6')} | RSI14: {rsi.get('rsi14')} | RSI24: {rsi.get('rsi24')}")
    lines.append(f"- 区域: {rsi.get('zone')}")

    kdj = result.get("kdj", {})
    lines.append(f"\n### KDJ")
    lines.append(f"- K: {kdj.get('k')} | D: {kdj.get('d')} | J: {kdj.get('j')}")
    lines.append(f"- 信号: {kdj.get('signal')}")

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "600519"
    result = analyze(symbol)
    print(result.get("summary", "分析失败"))
