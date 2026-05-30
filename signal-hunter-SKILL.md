买卖信号分析助手。当用户说"买卖点""什么时候买""该不该卖""买卖信号""技术面怎么看""MACD金叉""RSI超卖""回调到位""该止盈了吗"等时触发。基于 MA/MACD/RSI/KDJ/布林带/成交量 多指标共振，输出明确的买卖建议。

# 买卖信号 Skill

## 触发条件

用户提到"买卖点""信号""金叉""死叉""超买""超卖""什么时候买""该卖了吗""止损""止盈""回调""技术面"等时触发。

## 信号体系

### 🟢 买入信号（满足 3+ 项强烈建议）

| # | 信号 | 条件 | 权重 |
|---|------|------|:--:|
| 1 | RSI 超卖 | RSI14 < 30 | ⭐⭐⭐ |
| 2 | MACD 金叉 | DIF 上穿 DEA | ⭐⭐⭐ |
| 3 | KDJ 超卖反弹 | J < 0 后回升 | ⭐⭐ |
| 4 | 均线支撑 | 价格回踩 MA60 且企稳 | ⭐⭐ |
| 5 | 成交量放大 | 当日成交量 > 5日均量 × 1.5 | ⭐⭐ |
| 6 | 布林下轨 | 价格触及布林下轨反弹 | ⭐ |
| 7 | 多均线粘合 | MA5/10/20 相距 < 2% | ⭐ |
| 8 | 底背离 | 价格新低但 MACD 不新低 | ⭐⭐⭐ |

### 🔴 卖出信号（满足 2+ 项强烈建议）

| # | 信号 | 条件 | 权重 |
|---|------|------|:--:|
| 1 | RSI 超买 | RSI14 > 70 | ⭐⭐⭐ |
| 2 | MACD 死叉 | DIF 下穿 DEA | ⭐⭐⭐ |
| 3 | KDJ 超买回落 | J > 100 后跌破 | ⭐⭐ |
| 4 | 均线压制 | 价格反弹触及 MA60 后回落 | ⭐⭐ |
| 5 | 放量下跌 | 跌 > 3% 且成交量 > 5日均量 × 2 | ⭐⭐⭐ |
| 6 | 布林上轨 | 价格触及布林上轨 + 缩量 | ⭐ |
| 7 | 顶背离 | 价格新高但 MACD 不新高 | ⭐⭐⭐ |
| 8 | 破位 | 跌破关键支撑（MA120 或前低） | ⭐⭐⭐ |

## 执行命令

```bash
cd "C:/Users/twili/Desktop/Invest"

# 全面技术信号扫描
python -c "
import json
from python_tools.analysis.technical import analyze

sym = '600519'
t = analyze(sym)

print(f'=== {sym} 技术信号 ===')
print(f'价格: {t[\"latest_price\"]}')
print(f'趋势: {t[\"trend\"][\"conclusion\"]}')
print(f'多头信号: {t[\"trend\"][\"bullish_signals\"]}')
print(f'空头信号: {t[\"trend\"][\"bearish_signals\"]}')
print(f'MA排列: {t[\"ma\"][\"alignment\"]}')
print(f'RSI14: {t[\"rsi\"][\"rsi14\"]} ({t[\"rsi\"][\"zone\"]})')
print(f'MACD: DIF={t[\"macd\"][\"dif\"]} DEA={t[\"macd\"][\"dea\"]}')
print(f'KDJ: K={t[\"kdj\"][\"k\"]} D={t[\"kdj\"][\"d\"]} J={t[\"kdj\"][\"j\"]}')
"
```

## 批量扫描

```bash
cd "C:/Users/twili/Desktop/Invest"

python -c "
from python_tools.analysis.technical import analyze
import json

# 扫描自选股
with open('data/watchlist.json', 'r') as f:
    wl = json.load(f)

signals = []
for item in wl:
    sym = item['symbol']; name = item['name']
    t = analyze(sym)
    trend = t['trend']
    rsi = t['rsi']
    score = trend['bullish_signals'] - trend['bearish_signals']
    
    if score >= 2 or rsi.get('zone') in ('超卖',):
        signals.append({'sym': sym, 'name': name, 'action': '🟢 BUY', 'score': score, 'rsi': rsi.get('rsi14')})
    elif score <= -2 or rsi.get('zone') in ('超买',):
        signals.append({'sym': sym, 'name': name, 'action': '🔴 SELL', 'score': score, 'rsi': rsi.get('rsi14')})
    else:
        signals.append({'sym': sym, 'name': name, 'action': '⏸ HOLD', 'score': score, 'rsi': rsi.get('rsi14')})

signals.sort(key=lambda x: -x['score'])
print(f'{\"股票\":10s} {\"信号\":>8s} {\"评分\":>5s} {\"RSI\":>6s}')
for s in signals:
    print(f'{s[\"name\"]:8s}({s[\"sym\"]}) {s[\"action\"]:>8s} {s[\"score\"]:>+4d} {s[\"rsi\"]:>5.1f}')
"
```

## 输出格式

```
## 📡 买卖信号扫描 — [股票名称] ([代码])

### 当前状态
- 价格: XX.XX | 趋势: 偏多/偏空/震荡
- RSI14: XX.X (超卖/中性/超买)
- MACD: 金叉/死叉, DIF X.XX DEA X.XX
- KDJ: K XX D XX J XX

### 信号汇总
🟢 买入信号: 2 个 (RSI超卖, MACD金叉)
🔴 卖出信号: 0 个

### 建议: 🟢 强烈买入 / 🟡 观察等待 / 🔴 考虑卖出
- 入场区间: XX-XX
- 止损: XX (-X%)
- 目标: XX (+X%)

⚠️ 以上为技术面信号，请结合基本面/大盘环境综合判断。
```

## 信号强度分级

| 等级 | 条件 | 建议 |
|:----:|------|------|
| 🟢 强烈买入 | 买入信号 ≥ 3, 卖出信号 = 0 | 可积极介入 |
| 🟢 买入 | 买入信号 ≥ 2, 卖出信号 ≤ 1 | 分批建仓 |
| 🟡 观察 | 买卖信号持平 | 等待明朗 |
| 🔴 卖出 | 卖出信号 ≥ 2, 买入信号 ≤ 1 | 减仓或止损 |
| 🔴 强烈卖出 | 卖出信号 ≥ 3, RSI > 80 | 立即卖出 |
