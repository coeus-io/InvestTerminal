"""完全重建 industry_stocks.json — 核心行业用Playwright数据 + 其余用精选种子"""
import json, os

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "industry_stocks.json")

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    old = json.load(f)

# ── Step 1: 25 个 BK 代码 100% 映射正确的核心行业 — 保留 Playwright 数据 ──
TRUSTED_PLAYWRIGHT = {
    "白酒": "BK1575", "半导体": "BK1036", "消费电子": "BK1037",
    "光学光电子": "BK1038", "电子化学品": "BK1332",
    "银行": "BK1283", "保险": "BK1358", "证券": "BK1366",
    "房地产": "BK0451", "电池": "BK1033", "光伏设备": "BK1031",
    "风电设备": "BK1032", "能源金属": "BK1434",
    "煤炭开采加工": "BK1250", "贵金属": "BK1381",
    "化学制药": "BK0465", "中药": "BK1608",
    "医疗服务": "BK1063", "医疗器械": "BK1041",
    "IT服务": "BK1444", "计算机设备": "BK1043", "军工电子": "BK1386",
    "建筑材料": "BK0457", "美容护理": "BK1431",
    "教育": "BK1387", "游戏": "BK1301",
}

# ── Step 2: 所有行业的精选种子数据 ──
SEED = {
    "白酒": old.get("白酒", []),
    "饮料制造": [
        {"symbol":"600519","name":"贵州茅台"},{"symbol":"000858","name":"五粮液"},
        {"symbol":"000568","name":"泸州老窖"},{"symbol":"600887","name":"伊利股份"},
        {"symbol":"600600","name":"青岛啤酒"},{"symbol":"000729","name":"燕京啤酒"},
        {"symbol":"600132","name":"重庆啤酒"},{"symbol":"002568","name":"百润股份"},
    ],
    "食品加工制造": [
        {"symbol":"600887","name":"伊利股份"},{"symbol":"002557","name":"洽洽食品"},
        {"symbol":"603288","name":"海天味业"},{"symbol":"600305","name":"恒顺醋业"},
        {"symbol":"002847","name":"盐津铺子"},{"symbol":"603345","name":"安井食品"},
        {"symbol":"600882","name":"妙可蓝多"},{"symbol":"000895","name":"双汇发展"},
        {"symbol":"600873","name":"梅花生物"},{"symbol":"002582","name":"好想你"},
    ],
    "半导体": old.get("半导体", []),
    "元件": [
        {"symbol":"002916","name":"深南电路"},{"symbol":"300408","name":"三环集团"},
        {"symbol":"002384","name":"东山精密"},{"symbol":"002463","name":"沪电股份"},
        {"symbol":"600183","name":"生益科技"},{"symbol":"300476","name":"胜宏科技"},
        {"symbol":"002436","name":"兴森科技"},{"symbol":"002138","name":"顺络电子"},
    ],
    "消费电子": old.get("消费电子", []),
    "光学光电子": old.get("光学光电子", []),
    "电子化学品": old.get("电子化学品", []),
    "银行": old.get("银行", []),
    "保险": old.get("保险", []),
    "证券": old.get("证券", []),
    "多元金融": [
        {"symbol":"600816","name":"建元信托"},{"symbol":"000617","name":"中油资本"},
        {"symbol":"600390","name":"五矿资本"},{"symbol":"002423","name":"中粮资本"},
        {"symbol":"600901","name":"江苏金租"},{"symbol":"600318","name":"新力金融"},
    ],
    "房地产": old.get("房地产", []),
    "汽车整车": old.get("汽车整车", []),
    "汽车零部件": [
        {"symbol":"601689","name":"拓普集团"},{"symbol":"002920","name":"德赛西威"},
        {"symbol":"601799","name":"星宇股份"},{"symbol":"603596","name":"伯特利"},
        {"symbol":"002048","name":"宁波华翔"},{"symbol":"600741","name":"华域汽车"},
        {"symbol":"002126","name":"银轮股份"},{"symbol":"601058","name":"赛轮轮胎"},
        {"symbol":"601966","name":"玲珑轮胎"},{"symbol":"600660","name":"福耀玻璃"},
    ],
    "汽车服务及其他": [
        {"symbol":"601258","name":"庞大集团"},{"symbol":"600297","name":"广汇汽车"},
        {"symbol":"603377","name":"东方时尚"},{"symbol":"000996","name":"中国中期"},
    ],
    "电池": old.get("电池", []),
    "光伏设备": old.get("光伏设备", []),
    "风电设备": old.get("风电设备", []),
    "新能源车": [
        {"symbol":"300750","name":"宁德时代"},{"symbol":"002594","name":"比亚迪"},
        {"symbol":"300014","name":"亿纬锂能"},{"symbol":"300124","name":"汇川技术"},
        {"symbol":"601012","name":"隆基绿能"},{"symbol":"300274","name":"阳光电源"},
        {"symbol":"002460","name":"赣锋锂业"},{"symbol":"002466","name":"天齐锂业"},
    ],
    "能源金属": old.get("能源金属", []),
    "电力": [
        {"symbol":"600900","name":"长江电力"},{"symbol":"600025","name":"华能水电"},
        {"symbol":"600011","name":"华能国际"},{"symbol":"600886","name":"国投电力"},
        {"symbol":"601985","name":"中国核电"},{"symbol":"003816","name":"中国广核"},
        {"symbol":"600795","name":"国电电力"},{"symbol":"600023","name":"浙能电力"},
        {"symbol":"600905","name":"三峡能源"},{"symbol":"601991","name":"大唐发电"},
        {"symbol":"600027","name":"华电国际"},{"symbol":"001289","name":"龙源电力"},
    ],
    "电网设备": old.get("电网设备", []),
    "煤炭开采加工": old.get("煤炭开采加工", []),
    "石油加工贸易": [
        {"symbol":"600028","name":"中国石化"},{"symbol":"601857","name":"中国石油"},
        {"symbol":"600938","name":"中国海油"},{"symbol":"600688","name":"上海石化"},
        {"symbol":"000059","name":"华锦股份"},
    ],
    "贵金属": old.get("贵金属", []),
    "工业金属": [
        {"symbol":"601899","name":"紫金矿业"},{"symbol":"603993","name":"洛阳钼业"},
        {"symbol":"000630","name":"铜陵有色"},{"symbol":"000807","name":"云铝股份"},
        {"symbol":"600362","name":"江西铜业"},{"symbol":"601600","name":"中国铝业"},
        {"symbol":"002203","name":"海亮股份"},{"symbol":"600219","name":"南山铝业"},
        {"symbol":"000933","name":"神火股份"},
    ],
    "钢铁": old.get("钢铁", []),
    "化学制药": old.get("化学制药", []),
    "中药": old.get("中药", []),
    "生物制品": [
        {"symbol":"300122","name":"智飞生物"},{"symbol":"300142","name":"沃森生物"},
        {"symbol":"300601","name":"康泰生物"},{"symbol":"002007","name":"华兰生物"},
        {"symbol":"600161","name":"天坛生物"},
    ],
    "医疗服务": old.get("医疗服务", []),
    "医疗器械": old.get("医疗器械", []),
    "医药商业": [
        {"symbol":"600511","name":"国药股份"},{"symbol":"000028","name":"国药一致"},
        {"symbol":"603883","name":"老百姓"},{"symbol":"002727","name":"一心堂"},
        {"symbol":"603939","name":"益丰药房"},{"symbol":"300937","name":"药易购"},
    ],
    "白色家电": [
        {"symbol":"000333","name":"美的集团"},{"symbol":"000651","name":"格力电器"},
        {"symbol":"600690","name":"海尔智家"},{"symbol":"002050","name":"三花智控"},
        {"symbol":"000921","name":"海信家电"},{"symbol":"002032","name":"苏泊尔"},
    ],
    "厨卫电器": [
        {"symbol":"002032","name":"苏泊尔"},{"symbol":"002035","name":"华帝股份"},
        {"symbol":"603486","name":"科沃斯"},{"symbol":"002614","name":"奥佳华"},
        {"symbol":"002508","name":"老板电器"},
    ],
    "黑色家电": [
        {"symbol":"600060","name":"海信视像"},{"symbol":"000100","name":"TCL科技"},
        {"symbol":"000016","name":"深康佳A"},{"symbol":"002429","name":"兆驰股份"},
        {"symbol":"600839","name":"四川长虹"},
    ],
    "小家电": [
        {"symbol":"002032","name":"苏泊尔"},{"symbol":"002242","name":"九阳股份"},
        {"symbol":"603868","name":"飞科电器"},{"symbol":"002959","name":"小熊电器"},
        {"symbol":"603355","name":"莱克电气"},
    ],
    "IT服务": old.get("IT服务", []),
    "软件开发": old.get("软件开发", []),
    "计算机设备": old.get("计算机设备", []),
    "通信设备": old.get("通信设备", []),
    "军工装备": [
        {"symbol":"600893","name":"航发动力"},{"symbol":"600760","name":"中航沈飞"},
        {"symbol":"600862","name":"中航高科"},{"symbol":"000768","name":"中航西飞"},
        {"symbol":"600038","name":"中直股份"},{"symbol":"600879","name":"航天电子"},
        {"symbol":"600118","name":"中国卫星"},
    ],
    "军工电子": old.get("军工电子", []),
    "建筑装饰": old.get("建筑装饰", []),
    "建筑材料": old.get("建筑材料", []),
    "工程机械": [
        {"symbol":"600031","name":"三一重工"},{"symbol":"000157","name":"中联重科"},
        {"symbol":"000425","name":"徐工机械"},{"symbol":"603338","name":"浙江鼎力"},
        {"symbol":"600984","name":"建设机械"},{"symbol":"002097","name":"山河智能"},
    ],
    "港口航运": old.get("港口航运", []),
    "机场航运": old.get("机场航运", []),
    "公路铁路运输": old.get("公路铁路运输", []),
    "物流": old.get("物流", []),
    "养殖业": old.get("养殖业", []),
    "零售": old.get("零售", []),
    "教育": old.get("教育", []),
    "游戏": old.get("游戏", []),
    "文化传媒": old.get("文化传媒", []),
    "旅游及酒店": [
        {"symbol":"600754","name":"锦江酒店"},{"symbol":"600258","name":"首旅酒店"},
        {"symbol":"000888","name":"峨眉山A"},{"symbol":"000430","name":"张家界"},
        {"symbol":"603099","name":"长白山"},{"symbol":"600138","name":"中青旅"},
        {"symbol":"300144","name":"宋城演艺"},
    ],
    "美容护理": old.get("美容护理", []),
    "服装家纺": [
        {"symbol":"603116","name":"红蜻蜓"},{"symbol":"603555","name":"贵人鸟"},
        {"symbol":"002563","name":"森马服饰"},{"symbol":"002291","name":"星期六"},
    ],
    "自动化设备": [
        {"symbol":"300124","name":"汇川技术"},{"symbol":"300450","name":"先导智能"},
        {"symbol":"002747","name":"埃斯顿"},{"symbol":"300024","name":"机器人"},
        {"symbol":"002698","name":"博实股份"},
    ],
    "通用设备": [
        {"symbol":"300124","name":"汇川技术"},{"symbol":"002050","name":"三花智控"},
        {"symbol":"002158","name":"汉钟精机"},{"symbol":"300607","name":"拓斯达"},
        {"symbol":"688017","name":"绿的谐波"},{"symbol":"002520","name":"日发精机"},
    ],
    "专用设备": [
        {"symbol":"300450","name":"先导智能"},{"symbol":"002371","name":"北方华创"},
        {"symbol":"688012","name":"中微公司"},{"symbol":"300751","name":"迈为股份"},
        {"symbol":"300316","name":"晶盛机电"},{"symbol":"300604","name":"长川科技"},
        {"symbol":"603283","name":"赛腾股份"},{"symbol":"688001","name":"华兴源创"},
    ],
    "轨交设备": [
        {"symbol":"601766","name":"中国中车"},{"symbol":"688009","name":"中国通号"},
        {"symbol":"603500","name":"祥和实业"},{"symbol":"300011","name":"鼎汉技术"},
        {"symbol":"002296","name":"辉煌科技"},
    ],
    "环保设备": old.get("环保设备", []),
    "环境治理": [
        {"symbol":"600323","name":"瀚蓝环境"},{"symbol":"300070","name":"碧水源"},
        {"symbol":"600008","name":"首创环保"},{"symbol":"300388","name":"节能国祯"},
        {"symbol":"002672","name":"东江环保"},{"symbol":"000826","name":"启迪环境"},
    ],
    "互联网电商": old.get("互联网电商", []),
    "通信服务": old.get("通信服务", []),
    "化学制品": [
        {"symbol":"600309","name":"万华化学"},{"symbol":"002601","name":"龙佰集团"},
        {"symbol":"002648","name":"卫星化学"},{"symbol":"600346","name":"恒力石化"},
        {"symbol":"000301","name":"东方盛虹"},{"symbol":"600352","name":"浙江龙盛"},
        {"symbol":"002092","name":"中泰化学"},{"symbol":"603260","name":"合盛硅业"},
    ],
    "化肥": [
        {"symbol":"000902","name":"新洋丰"},{"symbol":"002539","name":"云图控股"},
        {"symbol":"002470","name":"金正大"},{"symbol":"600096","name":"云天化"},
        {"symbol":"000731","name":"四川美丰"},
    ],
    "化学纤维": [
        {"symbol":"600346","name":"恒力石化"},{"symbol":"000301","name":"东方盛虹"},
        {"symbol":"601233","name":"桐昆股份"},{"symbol":"002064","name":"华峰化学"},
    ],
    "化学原料": [
        {"symbol":"600309","name":"万华化学"},{"symbol":"002092","name":"中泰化学"},
        {"symbol":"000422","name":"湖北宜化"},{"symbol":"000683","name":"远兴能源"},
    ],
    "农化制品": old.get("农化制品", []),
    "塑料制品": [
        {"symbol":"600143","name":"金发科技"},{"symbol":"002324","name":"普利特"},
        {"symbol":"300180","name":"华峰超纤"},{"symbol":"300221","name":"银禧科技"},
        {"symbol":"002838","name":"道恩股份"},
    ],
    "橡胶制品": [
        {"symbol":"601058","name":"赛轮轮胎"},{"symbol":"600469","name":"风神股份"},
        {"symbol":"000589","name":"贵州轮胎"},{"symbol":"601163","name":"三角轮胎"},
        {"symbol":"002381","name":"双箭股份"},
    ],
    "非金属材料": [
        {"symbol":"603260","name":"合盛硅业"},{"symbol":"600176","name":"中国巨石"},
        {"symbol":"600586","name":"金晶科技"},{"symbol":"002080","name":"中材科技"},
    ],
    "金属新材料": [
        {"symbol":"300748","name":"金力永磁"},{"symbol":"600980","name":"北矿科技"},
        {"symbol":"300811","name":"铂科新材"},{"symbol":"300224","name":"正海磁材"},
    ],
    "农产品加工": [
        {"symbol":"000930","name":"中粮科技"},{"symbol":"300999","name":"金龙鱼"},
        {"symbol":"600737","name":"中粮糖业"},{"symbol":"002286","name":"保龄宝"},
        {"symbol":"002507","name":"涪陵榨菜"},{"symbol":"000895","name":"双汇发展"},
        {"symbol":"603288","name":"海天味业"},{"symbol":"002557","name":"洽洽食品"},
        {"symbol":"600887","name":"伊利股份"},
    ],
    "种植业与林业": [
        {"symbol":"600598","name":"北大荒"},{"symbol":"600313","name":"农发种业"},
        {"symbol":"002041","name":"登海种业"},{"symbol":"600371","name":"万向德农"},
        {"symbol":"000998","name":"隆平高科"},{"symbol":"300087","name":"荃银高科"},
    ],
    "小金属": [
        {"symbol":"600549","name":"厦门钨业"},{"symbol":"002428","name":"云南锗业"},
        {"symbol":"000960","name":"锡业股份"},{"symbol":"000657","name":"中钨高新"},
        {"symbol":"600259","name":"广晟有色"},
    ],
    "其他电子": [
        {"symbol":"002389","name":"航天彩虹"},{"symbol":"002414","name":"高德红外"},
        {"symbol":"300516","name":"久之洋"},{"symbol":"002935","name":"天奥电子"},
        {"symbol":"300456","name":"赛微电子"},
    ],
    "其他电源设备": [
        {"symbol":"300274","name":"阳光电源"},{"symbol":"300693","name":"盛弘股份"},
        {"symbol":"002518","name":"科士达"},{"symbol":"688390","name":"固德威"},
    ],
    "其他社会服务": [
        {"symbol":"300012","name":"华测检测"},{"symbol":"300662","name":"科锐国际"},
        {"symbol":"300572","name":"安车检测"},{"symbol":"300416","name":"苏试试验"},
        {"symbol":"300887","name":"谱尼测试"},
    ],
    "包装印刷": [
        {"symbol":"002191","name":"劲嘉股份"},{"symbol":"002303","name":"美盈森"},
        {"symbol":"600210","name":"紫江企业"},{"symbol":"002014","name":"永新股份"},
        {"symbol":"002799","name":"环球印务"},
    ],
    "纺织制造": [
        {"symbol":"002042","name":"华孚时尚"},{"symbol":"002563","name":"森马服饰"},
        {"symbol":"603116","name":"红蜻蜓"},{"symbol":"002327","name":"富安娜"},
        {"symbol":"603558","name":"健盛集团"},
    ],
    "电机": [
        {"symbol":"600580","name":"卧龙电驱"},{"symbol":"002176","name":"江特电机"},
        {"symbol":"300626","name":"华瑞股份"},{"symbol":"603728","name":"鸣志电器"},
    ],
    "家居用品": old.get("家居用品", []),
    "贸易": [
        {"symbol":"600755","name":"厦门国贸"},{"symbol":"600704","name":"物产中大"},
        {"symbol":"000829","name":"天音控股"},{"symbol":"600278","name":"东方创业"},
        {"symbol":"002091","name":"江苏国泰"},
    ],
    "燃气": [
        {"symbol":"600917","name":"重庆燃气"},{"symbol":"601139","name":"深圳燃气"},
        {"symbol":"600681","name":"百川能源"},{"symbol":"600333","name":"长春燃气"},
        {"symbol":"000593","name":"大通燃气"},
    ],
    "影视院线": [
        {"symbol":"002739","name":"万达电影"},{"symbol":"300133","name":"华策影视"},
        {"symbol":"300251","name":"光线传媒"},{"symbol":"600977","name":"中国电影"},
        {"symbol":"600715","name":"文投控股"},
    ],
    "油气开采及服务": [
        {"symbol":"600028","name":"中国石化"},{"symbol":"601857","name":"中国石油"},
        {"symbol":"600938","name":"中国海油"},{"symbol":"601808","name":"中海油服"},
        {"symbol":"600871","name":"石化油服"},
    ],
    "造纸": [
        {"symbol":"000488","name":"晨鸣纸业"},{"symbol":"600966","name":"博汇纸业"},
        {"symbol":"002078","name":"太阳纸业"},{"symbol":"600103","name":"青山纸业"},
        {"symbol":"600308","name":"华泰股份"},
    ],
    "综合": [
        {"symbol":"600805","name":"悦达投资"},{"symbol":"600620","name":"天宸股份"},
        {"symbol":"000009","name":"中国宝安"},{"symbol":"600653","name":"申华控股"},
        {"symbol":"600212","name":"绿能慧充"},
    ],
    "光模块": [
        {"symbol":"300308","name":"中际旭创"},{"symbol":"300502","name":"新易盛"},
        {"symbol":"300394","name":"天孚通信"},{"symbol":"002281","name":"光迅科技"},
        {"symbol":"688048","name":"长光华芯"},{"symbol":"300570","name":"太辰光"},
        {"symbol":"300913","name":"兆龙互连"},{"symbol":"300565","name":"科信技术"},
        {"symbol":"688313","name":"仕佳光子"},{"symbol":"600105","name":"永鼎股份"},
        {"symbol":"300620","name":"光库科技"},{"symbol":"603083","name":"剑桥科技"},
        {"symbol":"688205","name":"德科立"},{"symbol":"300548","name":"博创科技"},
        {"symbol":"688498","name":"源杰科技"},
    ],
}

# ── Build final ──
result = {}
for k in sorted(SEED.keys()):
    result[k] = SEED[k]

with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

total = sum(len(v) for v in result.values())
filled = sum(1 for v in result.values() if len(v)>0)
print(f'Done: {filled}/{len(result)} industries, {total} stocks')
print(f'Playwright data: ~{sum(len(v) for k,v in result.items() if k in TRUSTED_PLAYWRIGHT)} stocks in 27 trusted industries')
print(f'Seed curated: ~{total - sum(len(v) for k,v in result.items() if k in TRUSTED_PLAYWRIGHT)} stocks in remaining industries')
