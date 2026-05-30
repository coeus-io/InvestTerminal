"""
AkShare 数据获取封装 — 统一入口 + 缓存 + 错误处理

所有函数返回 pandas DataFrame（成功）或空 DataFrame（失败）。
"""

import json
import os
import sys
from typing import Optional, Callable

import pandas as pd

from python_tools.data import cache

# ── 通用工具 ───────────────────────────────────────────────────

def _with_cache(namespace: str, fetch_fn: Callable[[], pd.DataFrame],
                *parts: str) -> pd.DataFrame:
    """
    通用缓存包装：先查缓存，未命中则调用 fetch_fn() 获取并缓存。
    fetch_fn 是无参 callable（lambda），*parts 仅用于缓存 key。
    """
    cached = cache.get(namespace, *parts)
    if cached is not None:
        try:
            return pd.DataFrame(json.loads(cached))
        except Exception:
            pass  # 缓存损坏则重新获取

    try:
        df = fetch_fn()
    except Exception as e:
        print(f"[akshare] {namespace} 获取失败: {e}", file=sys.stderr)
        return pd.DataFrame()

    if df is None or df.empty:
        return pd.DataFrame()

    try:
        cache.set(namespace, *parts, value=df.to_json(orient="records", force_ascii=False))
    except Exception:
        pass

    return df


def _safe_import(fn):
    """装饰器：AkShare 导入失败时给出友好提示"""
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ImportError:
            print("[akshare] AkShare 未安装，请运行: pip install akshare", file=sys.stderr)
            return pd.DataFrame()
    return wrapper


# ── 股票基础 ───────────────────────────────────────────────────

@_safe_import
def get_stock_list() -> pd.DataFrame:
    """获取全部 A 股列表（代码、名称、行业）"""
    import akshare as ak
    return _with_cache("stock_list",
                       lambda: _rename_cols(ak.stock_info_a_code_name(),
                                            {"code": "symbol", "name": "name"}))


def _rename_cols(df, mapping):
    if df is None or df.empty:
        return df
    existing = {k: v for k, v in mapping.items() if k in df.columns}
    return df.rename(columns=existing)


@_safe_import
def get_stock_info(symbol: str) -> dict:
    """
    获取个股基本信息。
    从同花顺 abstract 提取最新一期数据，含 EPS/BPS/ROE/毛利率/资产负债率。
    """
    cached = cache.get("stock_info", symbol)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    try:
        import akshare as ak
        df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按报告期")
        if df.empty:
            return {}

        latest = df.iloc[-1]
        info = {
            "报告期": str(latest.get("报告期", "")),
            "股票简称": _guess_name(symbol),
            "总市值": latest.get("总市值"),
            "净利润": str(latest.get("净利润", "")),
            "净利润同比增长率": str(latest.get("净利润同比增长率", "")),
            "营业总收入": str(latest.get("营业总收入", "")),
            "营业总收入同比增长率": str(latest.get("营业总收入同比增长率", "")),
            "基本每股收益": str(latest.get("基本每股收益", "")),
            "每股净资产": str(latest.get("每股净资产", "")),
            "销售毛利率": str(latest.get("销售毛利率", "")),
            "销售净利率": str(latest.get("销售净利率", "")),
            "净资产收益率": str(latest.get("净资产收益率", "")),
            "资产负债率": str(latest.get("资产负债率", "")),
        }
        cache.set("stock_info", symbol, value=json.dumps(info, ensure_ascii=False))
        return info
    except Exception as e:
        print(f"[akshare] stock_info {symbol} 获取失败: {e}", file=sys.stderr)
        return {}


# 常见股票代码→名称映射（THS 抽象接口不直接返回名称时的 fallback）
_STOCK_NAME_MAP = {
    # 白酒
    "600519": "贵州茅台", "000858": "五粮液", "000568": "泸州老窖",
    "002304": "洋河股份", "000596": "古井贡酒", "600809": "山西汾酒",
    "600559": "老白干酒", "000799": "酒鬼酒", "600702": "舍得酒业",
    "600197": "伊力特", "603369": "今世缘", "603589": "口子窖",
    "600779": "水井坊", "603919": "金徽酒", "002646": "天佑德酒",
    "600199": "金种子酒", "000995": "皇台酒业", "603198": "迎驾贡酒",
    "600381": "青海春天",
    # 半导体
    "688981": "中芯国际", "002371": "北方华创", "603986": "兆易创新",
    "688008": "澜起科技", "688012": "中微公司", "002049": "紫光国微",
    "603501": "韦尔股份", "600703": "三安光电", "688256": "寒武纪",
    "300661": "圣邦股份", "688396": "华润微", "002185": "华天科技",
    "600584": "长电科技", "002156": "通富微电", "688536": "思瑞浦",
    # 银行/保险/金融
    "601398": "工商银行", "601939": "建设银行", "601288": "农业银行",
    "601988": "中国银行", "600036": "招商银行", "601166": "兴业银行",
    "600016": "民生银行", "601328": "交通银行", "600000": "浦发银行",
    "000001": "平安银行", "601818": "光大银行", "601009": "南京银行",
    "600015": "华夏银行", "002142": "宁波银行",
    "601318": "中国平安", "601628": "中国人寿", "601601": "中国太保",
    "601336": "新华保险", "601319": "中国人保",
    "600030": "中信证券", "601211": "国泰君安", "601688": "华泰证券",
    "600837": "海通证券", "000776": "广发证券", "601066": "中信建投",
    "600999": "招商证券", "600958": "东方证券",
    # 家电/新能源
    "000333": "美的集团", "000651": "格力电器", "600690": "海尔智家",
    "002050": "三花智控",
    "300750": "宁德时代", "002594": "比亚迪", "601012": "隆基绿能",
    "300014": "亿纬锂能", "002460": "赣锋锂业", "300274": "阳光电源",
    "002466": "天齐锂业", "688599": "天合光能", "300124": "汇川技术",
    "601615": "明阳智能",
    # 电力
    "600900": "长江电力", "600025": "华能水电", "600011": "华能国际",
    "600886": "国投电力", "601985": "中国核电", "003816": "中国广核",
    "600795": "国电电力", "600023": "浙能电力",
    # 中药/医药
    "600085": "同仁堂", "000538": "云南白药", "600436": "片仔癀",
    "000999": "华润三九", "002603": "以岭药业", "600329": "达仁堂",
    "600276": "恒瑞医药", "000963": "华东医药", "002001": "新和成",
    "300347": "泰格医药", "300759": "康龙化成", "603259": "药明康德",
    # 煤炭
    "601088": "中国神华", "600188": "兖矿能源", "601225": "陕西煤业",
    "600348": "华阳股份",
}


def _guess_name(symbol: str) -> str:
    return _STOCK_NAME_MAP.get(symbol, symbol)


# ── 行情数据 ─────────────────────────────────────────────────────

# Sina 日线 API：稳定、覆盖 2 年+、不依赖 eastmoney（VPN 环境下更可靠）
_SINA_KLINE_URL = (
    "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php"
    "/CN_MarketData.getKLineData"
)


def _get_daily_price_sina(symbol: str, start_date: str = "20100101",
                          end_date: str = "20500101") -> pd.DataFrame:
    """通过 Sina API 获取日线数据，返回统一格式 DataFrame"""
    import requests

    prefix = "sh" if symbol.startswith(("6", "9")) else "sz"
    full_symbol = f"{prefix}{symbol}"

    try:
        r = requests.get(
            _SINA_KLINE_URL,
            params={"symbol": full_symbol, "scale": 240, "ma": "no", "datalen": 1023},
            timeout=15,
            proxies={"http": None, "https": None},
            headers={"Referer": "https://finance.sina.com.cn"},
        )
        if r.status_code != 200 or not r.text.strip():
            return pd.DataFrame()
        data = json.loads(r.text)
        if not data:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df = df.rename(columns={
        "day": "date", "open": "open", "high": "high",
        "low": "low", "close": "close", "volume": "volume",
    })
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["close"])
    df = df.sort_values("date")

    # 按日期过滤
    if start_date:
        df = df[df["date"] >= pd.to_datetime(start_date, errors="coerce")]
    if end_date:
        df = df[df["date"] <= pd.to_datetime(end_date, errors="coerce")]

    return df


@_safe_import
def get_daily_price(symbol: str, start_date: str = "20100101",
                    end_date: str = "20500101", adjust: str = "qfq") -> pd.DataFrame:
    """
    日线行情（前复权）
    symbol: 6 位代码如 '600519'
    优先 Sina 源（VPN 兼容），失败则回退 akshare eastmoney。
    """
    params = [symbol, str(start_date), str(end_date)]

    # 主源：Sina（VPN 环境下可靠）
    df = _with_cache("daily_price_sina",
                     lambda: _get_daily_price_sina(symbol, start_date, end_date),
                     *params)
    if not df.empty:
        return df

    # 备选：akshare eastmoney
    import akshare as ak
    return _with_cache("daily_price",
                       lambda: ak.stock_zh_a_hist(
                           symbol=symbol, period="daily",
                           start_date=start_date, end_date=end_date, adjust=adjust
                       ),
                       *params, adjust)


@_safe_import
def get_index_data(index_code: str = "000300", start_date: str = "20100101",
                   end_date: str = "20500101") -> pd.DataFrame:
    """
    指数日线（Sina API）。
    index_code: '000300'=沪深300, '000001'=上证, '399001'=深成指
    """
    import requests
    prefix = "sh" if index_code.startswith(("0", "6")) else "sz"
    params = [index_code, str(start_date), str(end_date)]

    def _fetch():
        try:
            r = requests.get(
                _SINA_KLINE_URL,
                params={"symbol": f"{prefix}{index_code}", "scale": 240,
                        "ma": "no", "datalen": 1023},
                timeout=15,
                proxies={"http": None, "https": None},
                headers={"Referer": "https://finance.sina.com.cn"},
            )
            if r.status_code != 200 or not r.text.strip():
                return pd.DataFrame()
            data = json.loads(r.text)
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data)
            df = df.rename(columns={
                "day": "date", "open": "open", "high": "high",
                "low": "low", "close": "close", "volume": "volume",
            })
            for col in ["open", "high", "low", "close", "volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["close"]).sort_values("date")
            if start_date:
                df = df[df["date"] >= pd.to_datetime(start_date, errors="coerce")]
            if end_date:
                df = df[df["date"] <= pd.to_datetime(end_date, errors="coerce")]
            return df
        except Exception:
            return pd.DataFrame()

    return _with_cache("index_data_sina", _fetch, *params)


# ── 财务数据 ─────────────────────────────────────────────────────
# 主源：同花顺（THS），VPN 兼容；eastmoney 函数在此环境不可用。

@_safe_import
def get_financial_ratios(symbol: str) -> pd.DataFrame:
    """
    关键财务指标（ROE、毛利率、净利率等）。
    使用同花顺 abstract 接口，含 25 项指标 × 全部报告期。
    """
    import akshare as ak
    return _with_cache("financial_data",
                       lambda: ak.stock_financial_abstract_ths(
                           symbol=symbol, indicator="按报告期"),
                       symbol, "ratios_ths")


@_safe_import
def get_profit_statement(symbol: str) -> pd.DataFrame:
    """利润表（同花顺源）"""
    import akshare as ak
    return _with_cache("financial_data",
                       lambda: ak.stock_financial_benefit_ths(
                           symbol=symbol, indicator="按报告期"),
                       symbol, "profit_ths")


@_safe_import
def get_balance_sheet(symbol: str) -> pd.DataFrame:
    """资产负债表（同花顺源）"""
    import akshare as ak
    return _with_cache("financial_data",
                       lambda: ak.stock_financial_debt_ths(
                           symbol=symbol, indicator="按报告期"),
                       symbol, "balance_ths")


@_safe_import
def get_cash_flow(symbol: str) -> pd.DataFrame:
    """现金流量表（同花顺源）"""
    import akshare as ak
    return _with_cache("financial_data",
                       lambda: ak.stock_financial_cash_ths(
                           symbol=symbol, indicator="按报告期"),
                       symbol, "cashflow_ths")


# ── 行业分类 ─────────────────────────────────────────────────────

@_safe_import
def get_industry_classification() -> pd.DataFrame:
    """申万行业分类（同花顺源，VPN 兼容）"""
    import akshare as ak
    return _with_cache("industry_class_ths",
                       lambda: ak.stock_board_industry_name_ths())


@_safe_import
def get_industry_stocks(industry_name: str) -> pd.DataFrame:
    """
    某行业成分股。自动刷新策略：
    1. 每次调用先尝试 eastmoney 实时 API — 成功则自动更新本地缓存
    2. 实时失败（网络受限）则用本地 JSON 兜底
    3. 1 小时内成功过的 API 不再重复请求（避免限流）
    """
    from python_tools.data.industry_cache import get_stocks
    df, _meta = get_stocks(industry_name)
    return df


def get_industry_stocks_meta(industry_name: str) -> dict:
    """
    获取成分股及其新鲜度元数据。
    返回 {"stocks": DataFrame, "source": "live"|"cache"|"none",
           "updated_at": str|None, "stale_days": int|None}
    """
    from python_tools.data.industry_cache import get_stocks
    df, meta = get_stocks(industry_name)
    return {"stocks": df, **meta}


def refresh_industry_cache() -> dict:
    """手动触发全量行业成分股刷新（需 eastmoney API 可通）"""
    from python_tools.data.industry_cache import rebuild_all
    return rebuild_all()


def industry_cache_stats() -> dict:
    """查看成分股缓存状态"""
    from python_tools.data.industry_cache import cache_stats
    return cache_stats()


# ── 资金流向 ─────────────────────────────────────────────────────

@_safe_import
def get_north_flow(start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    北向资金流向摘要。
    数据来源：东方财富（push2.eastmoney.com，VPN ON/OFF 均可通）。
    返回当日沪股通/深股通资金流向汇总。
    """
    import akshare as ak
    return _with_cache("north_flow",
                       lambda: ak.stock_hsgt_fund_flow_summary_em())
