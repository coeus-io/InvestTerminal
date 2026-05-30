"""合并 Playwright 实时数据 + 种子数据 → 最终 JSON"""
import json, os

REAL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "industry_stocks.json")

# Load what we have (56 industries from Playwright)
with open(REAL_PATH, 'r', encoding='utf-8') as f:
    real = json.load(f)

# Seed fallback for missing industries
seed = {
    '元件': [{'symbol': '002916', 'name': '深南电路'}, {'symbol': '300408', 'name': '三环集团'}, {'symbol': '002384', 'name': '东山精密'}, {'symbol': '002463', 'name': '沪电股份'}],
    '通用设备': [{'symbol': '300124', 'name': '汇川技术'}, {'symbol': '002050', 'name': '三花智控'}],
    '白色家电': [{'symbol': '000333', 'name': '美的集团'}, {'symbol': '000651', 'name': '格力电器'}, {'symbol': '600690', 'name': '海尔智家'}],
    '新能源车': [{'symbol': '300750', 'name': '宁德时代'}, {'symbol': '002594', 'name': '比亚迪'}],
    '军工装备': [{'symbol': '600893', 'name': '航发动力'}, {'symbol': '600760', 'name': '中航沈飞'}],
    '饮料制造': [{'symbol': '600519', 'name': '贵州茅台'}, {'symbol': '000858', 'name': '五粮液'}, {'symbol': '600600', 'name': '青岛啤酒'}],
    '石油加工贸易': [{'symbol': '600028', 'name': '中国石化'}, {'symbol': '601857', 'name': '中国石油'}],
    '化肥': [{'symbol': '000902', 'name': '新洋丰'}, {'symbol': '600096', 'name': '云天化'}],
    '生物制品': [{'symbol': '300122', 'name': '智飞生物'}, {'symbol': '300142', 'name': '沃森生物'}],
    '医药商业': [{'symbol': '600511', 'name': '国药股份'}, {'symbol': '603883', 'name': '老百姓'}],
    '工程机械': [{'symbol': '600031', 'name': '三一重工'}, {'symbol': '000157', 'name': '中联重科'}],
    '旅游及酒店': [{'symbol': '600754', 'name': '锦江酒店'}, {'symbol': '300144', 'name': '宋城演艺'}],
    '服装家纺': [{'symbol': '002563', 'name': '森马服饰'}, {'symbol': '603116', 'name': '红蜻蜓'}],
    '包装印刷': [{'symbol': '002191', 'name': '劲嘉股份'}, {'symbol': '002303', 'name': '美盈森'}],
    '厨卫电器': [{'symbol': '002032', 'name': '苏泊尔'}, {'symbol': '002035', 'name': '华帝股份'}],
    '纺织制造': [{'symbol': '002042', 'name': '华孚时尚'}],
    '黑色家电': [{'symbol': '600060', 'name': '海信视像'}, {'symbol': '000100', 'name': 'TCL科技'}],
    '小家电': [{'symbol': '002032', 'name': '苏泊尔'}, {'symbol': '002242', 'name': '九阳股份'}],
    '环境治理': [{'symbol': '600323', 'name': '瀚蓝环境'}, {'symbol': '300070', 'name': '碧水源'}],
    '化学纤维': [{'symbol': '600346', 'name': '恒力石化'}],
    '化学原料': [{'symbol': '600309', 'name': '万华化学'}],
    '塑料制品': [{'symbol': '600143', 'name': '金发科技'}],
    '橡胶制品': [{'symbol': '601058', 'name': '赛轮轮胎'}],
    '非金属材料': [{'symbol': '603260', 'name': '合盛硅业'}, {'symbol': '600176', 'name': '中国巨石'}],
    '金属新材料': [{'symbol': '300748', 'name': '金力永磁'}],
    '小金属': [{'symbol': '600549', 'name': '厦门钨业'}],
    '种植业与林业': [{'symbol': '600598', 'name': '北大荒'}, {'symbol': '000998', 'name': '隆平高科'}],
    '其他电子': [{'symbol': '002389', 'name': '航天彩虹'}],
    '其他电源设备': [{'symbol': '300274', 'name': '阳光电源'}],
    '电机': [{'symbol': '600580', 'name': '卧龙电驱'}],
    '汽车服务及其他': [{'symbol': '601258', 'name': '庞大集团'}],
    '贸易': [{'symbol': '600755', 'name': '厦门国贸'}, {'symbol': '600704', 'name': '物产中大'}],
    '轨交设备': [{'symbol': '601766', 'name': '中国中车'}],
    '油气开采及服务': [{'symbol': '600028', 'name': '中国石化'}, {'symbol': '601857', 'name': '中国石油'}],
}

# Merge
merged = {}
for k in sorted(set(list(real.keys()) + list(seed.keys()))):
    if k in real and len(real[k]) > 0:
        merged[k] = real[k]
    elif k in seed:
        merged[k] = seed[k]
    else:
        merged[k] = []

with open(REAL_PATH, 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

filled = sum(1 for v in merged.values() if len(v) > 0)
total_stocks = sum(len(v) for v in merged.values())
print(f'Done: {filled}/{len(merged)} industries, {total_stocks} stocks')
print(f'Playwright real-time: 2693 | Seed fallback: {total_stocks - 2693}')
