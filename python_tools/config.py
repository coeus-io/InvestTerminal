"""
全局配置 — 路径、缓存策略、默认参数
"""

import os

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据缓存目录
DATA_DIR = os.path.join(ROOT_DIR, "data")
CACHE_DB = os.path.join(DATA_DIR, "cache.db")

# 持仓文件路径
PORTFOLIO_FILE = os.path.join(ROOT_DIR, "portfolio.json")

# 报告输出目录
REPORT_DIR = os.path.join(ROOT_DIR, "reports_output")

# ── 缓存 TTL（秒）─────────────────────────────────────────────
CACHE_TTL = {
    "daily_price":    24 * 3600,       # 日线 1 天
    "financial_data": 7 * 24 * 3600,   # 财报 7 天
    "industry_class": 30 * 24 * 3600,  # 行业分类 30 天
    "index_data":     24 * 3600,       # 指数 1 天
    "stock_list":     7 * 24 * 3600,   # 股票列表 7 天
}

# ── 默认参数────────────────────────────────────────────────────
# 估值百分位回看年数
DEFAULT_LOOKBACK_YEARS = 3

# 默认数据起始日期（Sina API ~2年历史；更早的需 eastmoney）
DEFAULT_START_DATE = "20230101"

# 默认基准指数
DEFAULT_BENCHMARK = "000300"  # 沪深300

# ── 确保目录存在────────────────────────────────────────────────
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
