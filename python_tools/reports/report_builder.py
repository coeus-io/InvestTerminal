"""
报告生成 — Markdown 结构化报告 + matplotlib 图表
"""

import os
from datetime import datetime
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # 非交互后端
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from python_tools.config import REPORT_DIR, DEFAULT_START_DATE
from python_tools.data.akshare_data import get_daily_price
from python_tools.analysis.fundamental import analyze as fundamental_analyze
from python_tools.analysis.valuation import analyze as valuation_analyze
from python_tools.analysis.technical import analyze as technical_analyze

# ── 中文字体配置 ─────────────────────────────────────────────────

def _setup_chinese_font():
    """尝试配置中文字体"""
    for font in ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei", "Noto Sans CJK SC", "Arial Unicode MS"]:
        try:
            plt.rcParams["font.sans-serif"] = [font]
            plt.rcParams["axes.unicode_minus"] = False
            return
        except Exception:
            continue
    # fallback
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


_setup_chinese_font()


# ── 图表生成 ──────────────────────────────────────────────────────

def plot_price_trend(symbol: str, days: int = 365, save_path: str = None) -> str:
    """绘制价格走势图 + 均线，返回图片路径"""
    start_date = DEFAULT_START_DATE
    df = get_daily_price(symbol, start_date=start_date)

    if df.empty:
        return ""

    df = df.sort_values("date")
    df = df.tail(days)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8),
                                     gridspec_kw={"height_ratios": [3, 1]})

    # K 线简化（收盘价线 + 均线）
    close = df["close"].values
    dates = pd.to_datetime(df["date"]).values

    ax1.plot(dates, close, color="#333", linewidth=1.2, label="收盘价")

    # 均线
    for period, color, alpha in [(5, "#ff6b6b", 0.6), (20, "#4ecdc4", 0.7), (60, "#45b7d1", 0.8)]:
        ma = df["close"].rolling(period).mean().values
        mask = ~np.isnan(ma)
        ax1.plot(dates[mask], ma[mask], color=color, alpha=alpha,
                linewidth=0.8, label=f"MA{period}")

    ax1.set_title(f"{symbol} 价格走势", fontsize=14, fontweight="bold")
    ax1.legend(loc="upper left", fontsize=8)
    ax1.set_ylabel("价格 (元)")
    ax1.grid(True, alpha=0.3)

    # 成交量
    if "volume" in df.columns:
        colors = ["#ff4444" if close[i] >= close[i-1] else "#00aa00"
                  for i in range(1, len(close))]
        ax2.bar(dates[1:], df["volume"].values[1:], color=colors,
                alpha=0.6, width=0.8)
        ax2.set_ylabel("成交量")
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path is None:
        save_path = os.path.join(REPORT_DIR, f"{symbol}_price_trend.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()

    return save_path


def plot_valuation_zone(pe_current: float, pe_median: float,
                         pe_q25: float, pe_q75: float,
                         title: str = "PE 估值区间",
                         save_path: str = None) -> str:
    """PE 估值区间图"""
    fig, ax = plt.subplots(figsize=(8, 3))

    # 绘制估值带
    ax.axvspan(0, pe_q25, alpha=0.15, color="green", label="低估区")
    ax.axvspan(pe_q25, pe_q75, alpha=0.10, color="yellow", label="合理区")
    ax.axvspan(pe_q75, pe_q75 * 2, alpha=0.12, color="red", label="高估区")

    # 中位数线
    ax.axvline(pe_median, color="orange", linewidth=1.5, linestyle="--", label=f"中位数 PE={pe_median:.1f}")

    # 当前 PE
    ax.axvline(pe_current, color="red", linewidth=2.5, label=f"当前 PE={pe_current:.1f}")
    ax.plot(pe_current, 0.5, "ro", markersize=10)

    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel("PE")
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(False)

    if save_path is None:
        save_path = os.path.join(REPORT_DIR, f"valuation_zone.png")
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()

    return save_path


# ── 报告模板 ──────────────────────────────────────────────────────

def stock_report(symbol: str, output_path: str = None) -> str:
    """
    个股完整分析报告。
    返回 Markdown 字符串，并可选保存为文件。
    """
    lines = []
    lines.append(f"# {symbol} 个股分析报告")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # ── 基本面 ─────────────────────────────────────────────────
    lines.append("---")
    try:
        fund = fundamental_analyze(symbol)
        lines.append(fund.get("summary", "基本面分析暂不可用"))
    except Exception as e:
        lines.append(f"基本面分析失败: {e}")

    # ── 估值 ───────────────────────────────────────────────────
    lines.append("")
    lines.append("---")
    try:
        val = valuation_analyze(symbol)
        lines.append(val.get("summary", "估值分析暂不可用"))
    except Exception as e:
        lines.append(f"估值分析失败: {e}")

    # ── 技术面 ─────────────────────────────────────────────────
    lines.append("")
    lines.append("---")
    try:
        tech = technical_analyze(symbol)
        lines.append(tech.get("summary", "技术分析暂不可用"))
    except Exception as e:
        lines.append(f"技术分析失败: {e}")

    # ── 免责声明 ───────────────────────────────────────────────
    lines.append("")
    lines.append("---")
    lines.append("> ⚠️ **风险提示**: 本报告由 AI 自动生成，仅供参考，不构成任何投资建议。")
    lines.append("> 投资有风险，入市需谨慎。请结合自身情况审慎决策。")

    report = "\n".join(lines)

    if output_path:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else REPORT_DIR, exist_ok=True)
        with open(output_path or os.path.join(REPORT_DIR, f"{symbol}_report.md"),
                  "w", encoding="utf-8") as f:
            f.write(report)

    return report


def quick_view(symbol: str) -> str:
    """
    快速一览 — 关键指标浓缩版
    """
    lines = [f"## {symbol} 速览\n"]

    try:
        fund = fundamental_analyze(symbol)
        lines.append(f"**基本面评分**: {fund.get('score', 'N/A')}/100")
        roe = fund.get("details", {}).get("roe", [])
        if roe:
            lines.append(f"**ROE (均值)**: {np.mean(roe[:3]):.1f}%" if len(roe) >= 3 else f"**ROE**: {roe[0]:.1f}%")
    except Exception:
        lines.append("基本面: 待获取")

    try:
        val = valuation_analyze(symbol)
        pe = val.get("pe", {})
        if pe.get("current_pe"):
            lines.append(f"**PE**: {pe['current_pe']}")
        lines.append(f"**估值区间**: {val.get('valuation_zone', 'N/A')}")
    except Exception:
        lines.append("估值: 待获取")

    try:
        tech = technical_analyze(symbol)
        trend = tech.get("trend", {})
        lines.append(f"**技术趋势**: {trend.get('conclusion', 'N/A')}")
        rsi = tech.get("rsi", {})
        if rsi.get("rsi14"):
            lines.append(f"**RSI(14)**: {rsi['rsi14']} ({rsi.get('zone', 'N/A')})")
    except Exception:
        lines.append("技术: 待获取")

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "quick"
    symbol = sys.argv[2] if len(sys.argv) > 2 else "600519"

    if cmd == "report":
        report = stock_report(symbol)
        print(report)
    elif cmd == "quick":
        print(quick_view(symbol))
    elif cmd == "chart":
        path = plot_price_trend(symbol)
        print(f"图表已保存: {path}")
    else:
        print("用法: report_builder.py [report|quick|chart] [symbol]")
