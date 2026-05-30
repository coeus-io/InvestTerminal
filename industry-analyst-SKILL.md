系统性 A 股投资决策助手。提供行业分析、个股深度研究、多因子选股、持仓管理、市场仪表盘五大能力，覆盖 Python 数据工具包和 Web 可视化面板。

触发词："分析XX行业""帮我做行研""这个赛道怎么样""这个行业值不值得投""帮我分析XX股票""XX怎么样可以买吗""选股""筛选""持仓""打开了仪表盘""看下盘面""市场怎么样""打开仪表盘"等。

# A 股投资决策终端（InvestTerminal）

## 五大应用场景

### 场景 1：行业研究 🔬

**触发**："分析半导体行业""白酒板块怎么样""光伏有没有机会""帮我做个 AI 行业报告"

**执行流程**：
1. 先通过 Playwright 获取行业成分股（调用 `push2delay.eastmoney.com` API）
2. 逐只拉取基本面（ROE/毛利率/净利率/营收增长/资产负债率）→ THS 源
3. 技术面分析（MA/MACD/RSI/趋势判断）→ Sina K 线
4. 生成结构化报告

**命令**：
```bash
cd "C:/Users/twili/Desktop/Invest"
# 单行业速览
python -c "from python_tools.analysis.industry import industry_summary; print(industry_summary('半导体'))"

# 行业深度（含 ROE 排名、集中度 CR5）
python -c "from python_tools.analysis.industry import industry_overview; import json; print(json.dumps(industry_overview('白酒', sample_limit=10), ensure_ascii=False, indent=2))"
```

### 场景 2：个股深度研究 📈

**触发**："帮我分析一下贵州茅台""宁德时代怎么样""润泽科技能不能买""看看中际旭创"

**执行流程**：
1. 基本面评分（`fundamental.analyze()`） — ROE/毛利率/成长性/财务健康 → 0-100 分
2. 估值分析（`valuation.analyze()`） — PE/PB/PEG + 行业对比
3. 技术面（`technical.analyze()`） — MA/MACD/RSI/KDJ + 趋势信号
4. 行业排名（`industry.rank_in_industry()`） — 该股在行业内的 ROE 排名
5. 综合结论 + 操作建议

**命令**：
```bash
cd "C:/Users/twili/Desktop/Invest"

# 快速一览
python -m python_tools.reports.report_builder quick 600519

# 完整报告（基本面+估值+技术面）
python -m python_tools.reports.report_builder report 600519

# 单独模块
python -m python_tools.analysis.fundamental 600519
python -m python_tools.analysis.valuation 600519
python -m python_tools.analysis.technical 600519
```

### 场景 3：多因子选股 🔍

**触发**："帮我筛选 ROE>15%, PE<30, 毛利率>30% 的股票""找一下高增长低估值的光伏股""选股"

**支持的筛选条件**：
- `pe_between(low, high)` — PE 区间
- `pb_between(low, high)` — PB 区间
- `roe_above(threshold)` — ROE 最低值
- `roe_between(low, high)` — ROE 区间
- `market_cap_above(yi)` — 市值下限（亿元）
- `market_cap_between(low, high)` — 市值区间
- `gross_margin_above(threshold)` — 毛利率最低值
- `revenue_growth_above(threshold)` — 营收增长最低值
- `industry(name)` — 限定行业

**命令**：
```bash
cd "C:/Users/twili/Desktop/Invest"

# 组合条件筛选
python -c "
from python_tools.analysis.screening import ScreeningCriteria, screen, format_results
c = ScreeningCriteria()
c.roe_above(15).pe_between(0, 30).market_cap_above(100)
results = screen(c, limit=30)
print(format_results(results))
"

# 行业内筛选
python -c "
from python_tools.analysis.screening import ScreeningCriteria, screen, format_results
c = ScreeningCriteria()
c.industry('半导体').roe_above(5).gross_margin_above(30)
results = screen(c, limit=20)
print(format_results(results))
"
```

### 场景 4：持仓组合管理 💼

**触发**："帮我看看持仓""添加茅台到持仓""持仓收益怎么样"

**命令**：
```bash
cd "C:/Users/twili/Desktop/Invest"

# 持仓概览
python -m python_tools.portfolio.tracker summary

# 添加持仓
python -m python_tools.portfolio.tracker add 600519 贵州茅台 1800 100 2025-06-01

# 删除持仓
python -m python_tools.portfolio.tracker remove 600519

# 收益归因 + 基准对比（沪深300）
python -m python_tools.portfolio.performance summary
```

### 场景 5：市场仪表盘 🖥️

**触发**："打开仪表盘""看下盘面""市场怎么样"

**启动**：
```bash
cd "C:/Users/twili/Desktop/Invest"
python -m python_tools.dashboard.server
# 浏览器自动打开 → http://localhost:5000
```

**四视图**：

| 视图 | 内容 | 刷新 |
|------|------|:--:|
| 总览 | KPI（数据源/覆盖/股票池）、市场指数（上证/深成/科创/创业）、持仓组合 | 30s |
| 行业全景 | 93 行业表（ROE中位/毛利率中位/净利率中位/Top1 股票）| 手动+后台分析 |
| 推荐股 | 全行业按 ROE 排序的 120 只精选标的（含实时行情） | 手动 |
| 自选股 | 无数量限制的关注列表（搜索添加/批量删除）| 手动 |

**API 端点**：`/api/status` `/api/industry` `/api/industry/analyse` `/api/screening` `/api/watchlist` `/api/watchlist/search` `/api/market`

---

## 数据源可靠性矩阵

| 数据 | 源 | 函数 | 可通性 |
|------|-----|------|:--:|
| 🟢 K 线（4年） | Sina | `get_daily_price()` | ✅ 始终 |
| 🟢 财务数据（102期） | 同花顺 THS | `get_stock_info()` | ✅ 始终 |
| 🟢 指数 K 线 | Sina | `get_index_data()` | ✅ 始终 |
| 🟢 实时行情（批量） | adata | `list_market_current()` | ✅ 始终 |
| 🟡 行业列表 | THS | `get_industry_classification()` | VPN OFF |
| 🟡 北向资金 | push2.eastmoney | `get_north_flow()` | VPN OFF |
| 🔴 成分股（实时） | push2delay.eastmoney | `get_industry_stocks()` | **Playwright** |
| 🟢 成分股（兜底） | 本地 JSON | 自动回退 | ✅ 始终 |

---

## 关键注意点

### 网络限制
- `17.push2.eastmoney.com` 和 `push2his.eastmoney.com` 在公司网络层被阻断（与 VPN 无关）
- **成分股实时获取必须通过 Playwright 浏览器**（`push2delay.eastmoney.com`）
- `adata.stock.market.list_market_current()` 是批量实时行情最优方案

### 数据新鲜度
- 行业分析缓存 → `data/industry_analysis_cache.json`（后台线程自动跑，5s 保存一次进度）
- 成分股映射 → `data/industry_stocks.json`（93行业/2778只，Playwright 拉取）
- 自选股 → `data/watchlist.json`（持久化，支持 50+ 只）

### 行业分析机制
- 启动后自动后台分析 93 行业（逐个调 THS API）
- 进度实时可见（`/api/industry` 返回 `progress: "15/93 白酒"`）
- 推荐股按全行业 ROE 中位数排序，取各行业 Top 3

---

## 使用流程示例

### 用户："帮我分析一下光模块，看看哪些可以买"

```
1. Python 获取光模块行业 16 只标的的 ROE/毛利率/营收增长 → 基本面对比表
2. Sina K 线 → 20 日涨幅/RSI/趋势 → 行情对比表
3. 综合评分 → 第一梯队/第二梯队/第三梯队分级
4. 买入建议 → 入场区间/目标价/止损
5. 问用户："要不要加到自选股？" → 调用 `/api/watchlist POST`
```

### 用户："打开仪表盘"

```
cd "C:/Users/twili/Desktop/Invest"
python -m python_tools.dashboard.server
→ 浏览器自动打开 http://localhost:5000
→ 四视图可切换
→ 行业后台自动分析（2-3 分钟完成 93 行业）
→ 推荐股按 ROE 排序展示 120 只精选
```
