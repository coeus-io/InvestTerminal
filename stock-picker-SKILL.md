选股决策助手。当用户说"选股""帮我筛选""找股票""有没有推荐的"等时触发。基于全 93 行业的 ROE 排名 + 基本面过滤 + 技术面确认，从 2161 只候选池中筛选。

# 选股决策 Skill

## 触发条件

用户说"选股""帮我筛选""找股票""有没有推荐的""帮我看看哪些可以买""筛一下光伏""找高增长股"时触发。

## 执行流程

### Step 1: 确定筛选维度

根据用户意图，组合以下条件：

| 维度 | 对应条件 | 典型阈值 |
|------|----------|----------|
| 盈利能力 | ROE | > 15%（优秀）, > 10%（良好） |
| 估值 | PE | < 20（低估）, 20-40（合理） |
| 成长性 | 营收增长率 | > 20%（高增长）, > 10%（稳健） |
| 安全性 | 资产负债率 | < 50%（安全）, < 70%（可接受） |
| 护城河 | 毛利率 | > 30%（有定价权）, > 50%（强护城河） |
| 行业 | 限定行业 | 如"半导体""光伏" |
| 市值 | 市值范围 | > 100亿（中大盘）, < 100亿（小盘） |

### Step 2: 获取行业分析数据

```bash
cd "C:/Users/twili/Desktop/Invest"

# 读取行业分析缓存
python -c "
import json
with open('data/industry_analysis_cache.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
cache = data.get('industries', {})
'''
# 如果缓存为空，触发后台分析
python -c "
import requests
r = requests.post('http://localhost:5000/api/industry/analyse', json={})
print(r.json())
"
```

### Step 3: 执行多因子筛选

```bash
cd "C:/Users/twili/Desktop/Invest"

python -c "
from python_tools.analysis.screening import ScreeningCriteria, screen, format_results
c = ScreeningCriteria()
# 根据用户需求调整
c.roe_above(15).pe_between(0, 30).market_cap_above(100)
results = screen(c, limit=50)
print(format_results(results))
"
```

### Step 4: 热门行业精选

直接调用仪表盘筛选 API：

```bash
curl -s http://localhost:5000/api/screening | python -c "
import sys, json
d = json.load(sys.stdin)
recs = d['recommendations']
# 按行业ROE排序，取前20
recs.sort(key=lambda x: x.get('industry_roe', 0), reverse=True)
for i, r in enumerate(recs[:20], 1):
    print(f'{i}. {r[\"name\"]}({r[\"symbol\"]}) [{r[\"industry\"]}] ROE={r[\"roe\"]} 毛利率={r[\"gross_margin\"]} 价格={r.get(\"price\",\"--\")}')
"
```

### Step 5: 输出格式

```
## 🔍 选股结果

### 筛选条件
- ROE > 15%, PE < 30, 市值 > 100亿

### 结果（按评分排序）

| # | 代码 | 名称 | 行业 | PE | ROE% | 毛利率% | 评分 |
|---|------|------|------|----|------|---------|------|
| 1 | 600519 | 茅台 | 白酒 | 28 | 21.4 | 89.8 | 85 |

### 建议
- 🟢 推荐介入: 2只
- 🟡 观察: 5只
- 🔴 暂不建议: 3只
```

## 筛选预设模板

| 模板名 | 条件 |
|--------|------|
| 🏆 价值白马 | ROE > 15%, PE < 20, 市值 > 500亿 |
| 🚀 成长先锋 | 营收增长 > 30%, ROE > 10%, PE < 50 |
| 🛡️ 高股息防守 | ROE > 8%, 负债率 < 40%, 行业：银行/电力/煤炭 |
| 🔬 科技龙头 | ROE > 10%, 毛利率 > 30%, 行业：半导体/AI/光模块 |
| 💊 医药精选 | ROE > 8%, 毛利率 > 40%, 行业：化学制药/中药/医疗器械 |
