# 📊 投资决策工具 — 操作面板

> 最后更新: 2026-05-30

---

## 一、项目架构

```
Invest/
├── STATUS.md                       ← 本文件（操作面板）
├── industry-analyst-SKILL.md       ← Claude Skill（行研框架 + 调用指引）
├── requirements.txt                ← akshare pandas matplotlib numpy
│
├── data/
│   ├── industry_stocks.json        ← 成分股缓存 (92行业/2762只)
│   ├── industry_stocks_meta.json   ← 新鲜度追踪
│   └── cache.db                    ← SQLite 请求缓存
│
├── reports_output/                 ← 生成的报告和图表
│
└── python_tools/
    ├── config.py                   ← 全局配置（路径、TTL、默认参数）
    ├── data/
    │   ├── akshare_data.py         ← 数据层封装（Sina K线 + THS 财务）
    │   ├── cache.py                ← SQLite 缓存
    │   ├── industry_cache.py       ← 成分股自动刷新 + JSON 兜底
    │   ├── build_industry_map.py   ← 全量重建工具
    │   └── merge_data.py           ← 数据合并脚本
    ├── analysis/
    │   ├── fundamental.py          ← 基本面评分
    │   ├── valuation.py            ← PE/PB/PEG 估值
    │   ├── industry.py             ← 行业分析（ROE排名 + 新鲜度标注）
    │   ├── screening.py            ← 多因子选股
    │   └── technical.py            ← MA/MACD/RSI/KDJ
    ├── portfolio/
    │   ├── tracker.py              ← 持仓管理
    │   └── performance.py          ← 收益归因 + 基准对比
    └── reports/
        └── report_builder.py       ← Markdown 报告 + matplotlib 图表
```

---

## 二、已完成配置清单

### Phase 1: 基础设施 ✅
| # | 模块 | 状态 | 说明 |
|---|------|------|------|
| 1.1 | 目录结构 | ✅ | python_tools/{data,analysis,portfolio,reports} |
| 1.2 | requirements.txt | ✅ | akshare 1.18.60, pandas, matplotlib, numpy |
| 1.3 | config.py | ✅ | 路径、缓存 TTL、DEFAULT_START_DATE="20230101" |
| 1.4 | cache.py | ✅ | SQLite，107条缓存记录 |

### Phase 2: 数据层 ✅
| # | 模块 | 来源 | 网络要求 |
|---|------|------|----------|
| 2.1 | get_daily_price() | Sina API | ✅ 始终可通 |
| 2.2 | get_index_data() | Sina API | ✅ 始终可通 |
| 2.3 | get_financial_ratios() | THS (同花顺) | ✅ 始终可通 |
| 2.4 | get_profit_statement() | THS | ✅ 始终可通 |
| 2.5 | get_balance_sheet() | THS | ✅ 始终可通 |
| 2.6 | get_cash_flow() | THS | ✅ 始终可通 |
| 2.7 | get_stock_info() | THS | ✅ 始终可通 |
| 2.8 | get_industry_classification() | THS | ✅ VPN OFF 时通 |
| 2.9 | get_north_flow() | push2.eastmoney | ✅ VPN OFF 时通 |
| 2.10 | get_industry_stocks() | push2delay + JSON 兜底 | ✅ 三层回退 |

### Phase 3: 分析层 ✅
| # | 模块 | 功能 |
|---|------|------|
| 3.1 | fundamental.py | ROE/毛利率/净利率/资产负债率 评分 (0-100) |
| 3.2 | valuation.py | PE/PB 提取 + 估值区间判断 |
| 3.3 | technical.py | MA5/10/20/60, MACD, RSI6/14/24, KDJ + 趋势判断 |
| 3.4 | industry.py | 行业ROE排名、毛利率排名、集中度 + 🟢🟡 新鲜度标注 |
| 3.5 | screening.py | 多因子筛选 (PE/PB/ROE/市值/毛利率/行业) |

### Phase 4: 组合管理 ✅
| # | 模块 | 功能 |
|---|------|------|
| 4.1 | tracker.py | 持仓增删改查 + 实时快照 + 盈亏计算 |
| 4.2 | performance.py | 年化收益 + 沪深300基准对比 + 行业暴露 |

### Phase 5: 报告层 ✅
| # | 模块 | 功能 |
|---|------|------|
| 5.1 | report_builder.py | quick_view() 速览 + stock_report() 完整报告 |
| 5.2 | report_builder.py | plot_price_trend() K线图 + plot_valuation_zone() PE区间图 |

### Phase 6: 数据覆盖 ✅
| 指标 | 数值 |
|------|------|
| 行业数 | **92/92** (100%) |
| 股票总数 | **2,762** |
| 数据来源 | 97.5% 东方财富实时 (Playwright), 2.5% 种子兜底 |
| 最大行业 | IT服务/化学制药/医疗器械 各100只 |
| 最小行业 | 化学原料/化学纤维等 仅1只 |

---

## 三、数据源可靠性矩阵

| 数据 | 来源 | 域名 | VPN ON | VPN OFF | 方法 |
|------|------|------|--------|---------|------|
| 🟢 K线 (4年) | Sina | `money.finance.sina.com.cn` | ✅ | ✅ | `requests` |
| 🟢 财务 (102期) | THS | 同花顺 akshare | ✅ | ✅ | `requests` |
| 🟢 指数 K线 | Sina | `money.finance.sina.com.cn` | ✅ | ✅ | `requests` |
| 🟢 个股信息 | THS | 同花顺 akshare | ✅ | ✅ | `requests` |
| 🟡 行业列表 | THS | 同花顺 akshare | ❌ | ✅ | `requests` |
| 🟡 北向资金 | push2.eastmoney | `push2.eastmoney.com` | ❌ | ✅ | `requests` |
| 🔴 成分股(实时) | push2delay | `push2delay.eastmoney.com` | ✅ | ✅ | **Playwright CDP** |
| 🟢 成分股(兜底) | 本地 JSON | 本地文件 | ✅ | ✅ | 文件读取 |

> **关键发现**: `push2delay.eastmoney.com` 在 Playwright 浏览器内可通，但 Python `requests` 库被网络层阻断。

---

## 四、注意要点

### 4.1 网络环境
- `17.push2.eastmoney.com` 在公司网络层被阻断（与 VPN 开关无关）
- `push2his.eastmoney.com` 同样被阻断
- **Playwright 浏览器可绕过** — 成分股刷新需通过 CDP
- VPN (`127.0.0.1:10808`) 开启时会额外阻断 `push2.eastmoney.com`

### 4.2 数据新鲜度
- `get_stock_info()` 返回**最近一个报告期**的财务数据（季度更新）
- 本地 `industry_stocks.json` 新鲜度通过 `industry_stocks_meta.json` 追踪
- 行业报告自动标注 🟢实时 / 🟡缓存(N天)

### 4.3 估值模块限制
- `valuation.py` 的 PE 历史百分位、PEG 依赖财务数据，当前 THS 源不完全覆盖
- 估值区间判断回退到绝对值法（PE<15 低估, 15-30 合理, 30-50 偏高, >50 高估）

### 4.4 多因子选股限制
- 全市场扫描慢（~30只/分钟，需逐一调用 get_stock_info）
- 建议先限定行业再筛选
- 大行业（100只）的 industry_overview 耗时 ~2-3 分钟

### 4.5 名称映射
- THS 接口不直接返回股票名称，通过 `_STOCK_NAME_MAP` fallback
- 当前映射覆盖 ~130 只常见标的，冷门股显示代码而非名称

### 4.6 日期格式
- Sina API 返回 `YYYY-MM-DD` 格式
- 统一通过 `pd.to_datetime()` 解析，兼容多种格式

### 4.7 仪表盘
- 访问: `http://localhost:5000`
- 启动: `python -m python_tools.dashboard.server`
- 自动刷新: 每 60 秒更新状态和行情
- 行业数据需手动点击加载（耗时 ~3 分钟）
- Sina API 返回 `YYYY-MM-DD` 格式
- 统一通过 `pd.to_datetime()` 解析，兼容多种格式

---

## 五、待完成

### 高优先级
- [ ] **成分股刷新自动化**: 将 Playwright CDP 方法集成到 `industry_cache.py`，替代 `requests` 方式的 `_try_fetch_live()`
- [ ] **估值模块完善**: PE 历史百分位从 Sina K线 + EPS 计算，PEG 补齐
- [ ] **名称映射扩充**: 覆盖全部 2762 只股票的名称映射

### 中优先级
- [ ] **36 个小行业数据**: 对 BK 代码不唯一的行业（通用设备/塑料制品等），在 EM 分类里找到正确的 BK 代码并拉取实时数据
- [ ] **DCF 估值模型**: `valuation.py` 中实现简化 DCF
- [ ] **股息率分析**: 新增分析维度
- [ ] **财务数据趋势图**: `report_builder.py` 增加 ROE/毛利率 历史趋势图

### 低优先级
- [ ] **回测框架**: 持仓组合历史回测
- [ ] **北向资金趋势图**: `get_north_flow()` 数据可视化
- [ ] **行业轮动分析**: 基于 `stock_board_industry_index_ths` 的行业指数走势
- [ ] **Web UI**: 从 CLI 迁移到简单的 Web 面板

---

## 六、测试计划

### 6.1 单元测试（每次改代码后）

```bash
# 数据层
python -c "
from python_tools.data.akshare_data import get_daily_price, get_financial_ratios, get_stock_info
p = get_daily_price('600519')
print(f'K线: {len(p)} rows')
r = get_financial_ratios('600519')
print(f'财务: {len(r)} rows')
i = get_stock_info('600519')
print(f'ROE={i.get(\"净资产收益率\")} 毛利率={i.get(\"销售毛利率\")}')
"

# 分析层
python -m python_tools.analysis.fundamental 600519
python -m python_tools.analysis.technical 600519

# 报告
python -m python_tools.reports.report_builder quick 600519
```

### 6.2 集成测试（每次重大改动后）

```bash
# 全链路：个股深度分析
python -m python_tools.reports.report_builder report 600519

# 行业分析（含新鲜度标注）
python -m python_tools.analysis.industry 白酒

# 持仓管理
python -m python_tools.portfolio.tracker summary
python -m python_tools.portfolio.performance summary
```

### 6.3 网络环境切换测试

| 测试场景 | 命令 | 预期 |
|----------|------|------|
| VPN ON | `get_daily_price('600519')` | ✅ (Sina) |
| VPN ON | `get_industry_classification()` | ❌ → 检查上一次缓存 |
| VPN ON | `get_north_flow()` | ❌ → 空 |
| VPN OFF | `get_industry_classification()` | ✅ (THS) |
| VPN OFF | `get_north_flow()` | ✅ (push2) |
| 任何环境 | `get_industry_stocks('白酒')` | ✅ (JSON 兜底) |

### 6.4 数据准确性交叉验证

```bash
# 与同花顺/东方财富网页版对比
python -c "
from python_tools.data.akshare_data import get_stock_info
i = get_stock_info('600519')
print(f'ROE={i.get(\"净资产收益率\")}')
print(f'毛利率={i.get(\"销售毛利率\")}')
print(f'资产负债率={i.get(\"资产负债率\")}')
# 对比 https://data.eastmoney.com/stockdata/600519.html
"
```

---

## 七、快速命令参考

| 场景 | 命令 |
|------|------|
| 个股快览 | `python -m python_tools.reports.report_builder quick 600519` |
| 个股完整报告 | `python -m python_tools.reports.report_builder report 600519` |
| K线图 | `python -m python_tools.reports.report_builder chart 600519` |
| 基本面评分 | `python -m python_tools.analysis.fundamental 600519` |
| 技术分析 | `python -m python_tools.analysis.technical 600519` |
| 估值分析 | `python -m python_tools.analysis.valuation 600519` |
| 行业分析 | `python -m python_tools.analysis.industry 白酒` |
| 多因子选股 | `python -m python_tools.analysis.screening` |
| 持仓概览 | `python -m python_tools.portfolio.tracker summary` |
| 收益归因 | `python -m python_tools.portfolio.performance summary` |
| 缓存统计 | `python -c "from python_tools.data.cache import stats; print(stats())"` |
| 成分股缓存统计 | `python -c "from python_tools.data.akshare_data import industry_cache_stats; print(industry_cache_stats())"` |
| 清缓存 | `python -c "from python_tools.data.cache import clear; clear()"` |

---

## 八、版本历史

| 日期 | 变更 |
|------|------|
| 2026-05-30 | 初始版本完成：19个Python模块 + 92行业/2762只股票数据 |
| 2026-05-30 | 数据源从 eastmoney 切换到 Sina+THS（绕过 VPN 阻断） |
| 2026-05-30 | 通过 Playwright CDP 拉取东方财富实时成分股（2693只） |
| 2026-05-30 | 成分股三层回退机制：实时API → 本地JSON → 模糊匹配 |
