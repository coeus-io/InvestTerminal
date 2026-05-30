Web 仪表盘一键启动助手。当用户说"打开仪表盘""看下盘面""打开面板""dashboard""启动仪表盘""看终端""看下数据"等时触发。

# 仪表盘启动 Skill

## 触发条件

"打开仪表盘""看下盘面""打开面板""dashboard""启动仪表盘""看终端""看下数据""打开投资终端"。

## 启动命令

```bash
cd "C:/Users/twili/Desktop/Invest" && python -m python_tools.dashboard.server
```

**启动后**：
- 浏览器自动打开 `http://localhost:5000`
- 四视图：总览 | 行业全景 | 推荐股 | 自选股
- 行业分析后台自动运行（2-3 分钟完成 93 行业）
- 推荐股按全行业 ROE 排序，120 只精选标的

## 已运行时的提示

如果仪表盘已在运行（检查 `http://localhost:5000` 是否可访问），直接告诉用户：
- 仪表盘已在运行中
- 访问地址: http://localhost:5000
- 无需重复启动

## API 快速参考

| 端点 | 用途 |
|------|------|
| `/api/status` | 项目状态、覆盖统计 |
| `/api/industry` | 93行业全量数据（含ROE/毛利率） |
| `/api/industry/analyse` | 触发全量行业分析 |
| `/api/screening` | 智能推荐股（按ROE排序） |
| `/api/watchlist` | 自选股CRUD |
| `/api/watchlist/search?q=茅台` | 股票模糊搜索 |
| `/api/market` | 市场指数（上证/深成/科创50/创业板） |
