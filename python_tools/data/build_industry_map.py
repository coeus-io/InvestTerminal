"""
行业成分股映射生成器 — 在不受限网络上运行一次即可。
生成 data/industry_stocks.json，后续离线使用。
"""

import json
import sys
import os
import time

import pandas as pd

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from python_tools.data.akshare_data import get_industry_classification
from python_tools.config import DATA_DIR


def build(output_path: str = None) -> dict:
    """
    遍历所有同花顺行业，获取每个行业的成分股。
    每请求之间 sleep 0.5s 避免被限流。
    返回 {行业名: [{"symbol": "...", "name": "..."}, ...]}
    """
    industries = get_industry_classification()
    if industries.empty:
        print("无法获取行业列表，请检查网络", file=sys.stderr)
        return {}

    result = {}
    total = len(industries)

    for idx, (_, row) in enumerate(industries.iterrows(), 1):
        name = row.get("name", "")
        code = row.get("code", "")
        if not name:
            continue

        print(f"[{idx}/{total}] 获取 {name} ...", end=" ")

        try:
            import akshare as ak
            df = ak.stock_board_industry_cons_em(symbol=name)

            if df.empty:
                print("空")
                result[name] = []
                continue

            stocks = []
            for _, sr in df.iterrows():
                sym = sr.get("代码", sr.iloc[0]) if "代码" in df.columns else sr.iloc[0]
                nm = sr.get("名称", str(sym)) if "名称" in df.columns else str(sym)
                stocks.append({"symbol": str(sym), "name": str(nm)})

            result[name] = stocks
            print(f"{len(stocks)} 只")

        except Exception as e:
            print(f"失败: {e}")
            result[name] = []

        time.sleep(0.5)

    # 写入文件
    if output_path is None:
        output_path = os.path.join(DATA_DIR, "industry_stocks.json")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n已保存到 {output_path}")
    print(f"共 {len(result)} 个行业，{sum(len(v) for v in result.values())} 只股票")

    return result


if __name__ == "__main__":
    build()
