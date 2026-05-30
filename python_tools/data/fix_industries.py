"""修复被 BK 代码共享污染的行业数据"""
import json, os

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "industry_stocks.json")

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

# ── 污染行业 → 手工整理种子数据 ───────────────────────────────

fixes = {
    '农产品加工': [
        {'symbol':'000930','name':'中粮科技'},{'symbol':'300999','name':'金龙鱼'},
        {'symbol':'600737','name':'中粮糖业'},{'symbol':'002286','name':'保龄宝'},
        {'symbol':'002507','name':'涪陵榨菜'},{'symbol':'000895','name':'双汇发展'},
        {'symbol':'603288','name':'海天味业'},{'symbol':'002557','name':'洽洽食品'},
        {'symbol':'600887','name':'伊利股份'},
    ],
    '种植业与林业': [
        {'symbol':'600598','name':'北大荒'},{'symbol':'600313','name':'农发种业'},
        {'symbol':'002041','name':'登海种业'},{'symbol':'600371','name':'万向德农'},
        {'symbol':'000998','name':'隆平高科'},{'symbol':'300087','name':'荃银高科'},
    ],
    '造纸': [
        {'symbol':'000488','name':'晨鸣纸业'},{'symbol':'600966','name':'博汇纸业'},
        {'symbol':'002078','name':'太阳纸业'},{'symbol':'600103','name':'青山纸业'},
        {'symbol':'600308','name':'华泰股份'},
    ],
    '专用设备': [
        {'symbol':'300450','name':'先导智能'},{'symbol':'002371','name':'北方华创'},
        {'symbol':'688012','name':'中微公司'},{'symbol':'300751','name':'迈为股份'},
        {'symbol':'300316','name':'晶盛机电'},{'symbol':'300604','name':'长川科技'},
        {'symbol':'603283','name':'赛腾股份'},{'symbol':'688001','name':'华兴源创'},
    ],
    '轨交设备': [
        {'symbol':'601766','name':'中国中车'},{'symbol':'688009','name':'中国通号'},
        {'symbol':'603500','name':'祥和实业'},{'symbol':'300011','name':'鼎汉技术'},
        {'symbol':'002296','name':'辉煌科技'},
    ],
    '元件': [
        {'symbol':'002916','name':'深南电路'},{'symbol':'300408','name':'三环集团'},
        {'symbol':'002384','name':'东山精密'},{'symbol':'002463','name':'沪电股份'},
        {'symbol':'600183','name':'生益科技'},{'symbol':'300476','name':'胜宏科技'},
        {'symbol':'002436','name':'兴森科技'},{'symbol':'002138','name':'顺络电子'},
    ],
    '通用设备': [
        {'symbol':'300124','name':'汇川技术'},{'symbol':'002050','name':'三花智控'},
        {'symbol':'002158','name':'汉钟精机'},{'symbol':'300607','name':'拓斯达'},
        {'symbol':'688017','name':'绿的谐波'},{'symbol':'002520','name':'日发精机'},
    ],
    '塑料制品': [
        {'symbol':'600143','name':'金发科技'},{'symbol':'002324','name':'普利特'},
        {'symbol':'300180','name':'华峰超纤'},{'symbol':'300221','name':'银禧科技'},
        {'symbol':'002838','name':'道恩股份'},
    ],
    '橡胶制品': [
        {'symbol':'601058','name':'赛轮轮胎'},{'symbol':'600469','name':'风神股份'},
        {'symbol':'000589','name':'贵州轮胎'},{'symbol':'601163','name':'三角轮胎'},
        {'symbol':'002381','name':'双箭股份'},
    ],
    '非金属材料': [
        {'symbol':'603260','name':'合盛硅业'},{'symbol':'600176','name':'中国巨石'},
        {'symbol':'600586','name':'金晶科技'},{'symbol':'002080','name':'中材科技'},
    ],
    '电机': [
        {'symbol':'600580','name':'卧龙电驱'},{'symbol':'002176','name':'江特电机'},
        {'symbol':'300626','name':'华瑞股份'},{'symbol':'603728','name':'鸣志电器'},
    ],
    '其他电源设备': [
        {'symbol':'300274','name':'阳光电源'},{'symbol':'300693','name':'盛弘股份'},
        {'symbol':'002518','name':'科士达'},{'symbol':'688390','name':'固德威'},
    ],
    '其他电子': [
        {'symbol':'002389','name':'航天彩虹'},{'symbol':'002414','name':'高德红外'},
        {'symbol':'300516','name':'久之洋'},{'symbol':'002935','name':'天奥电子'},
        {'symbol':'300456','name':'赛微电子'},
    ],
    '化学纤维': [
        {'symbol':'600346','name':'恒力石化'},{'symbol':'000301','name':'东方盛虹'},
        {'symbol':'601233','name':'桐昆股份'},{'symbol':'002064','name':'华峰化学'},
    ],
    '化学原料': [
        {'symbol':'600309','name':'万华化学'},{'symbol':'002092','name':'中泰化学'},
        {'symbol':'000422','name':'湖北宜化'},{'symbol':'000683','name':'远兴能源'},
    ],
    '小金属': [
        {'symbol':'600549','name':'厦门钨业'},{'symbol':'002428','name':'云南锗业'},
        {'symbol':'000960','name':'锡业股份'},{'symbol':'000657','name':'中钨高新'},
        {'symbol':'600259','name':'广晟有色'},
    ],
    '包装印刷': [
        {'symbol':'002191','name':'劲嘉股份'},{'symbol':'002303','name':'美盈森'},
        {'symbol':'600210','name':'紫江企业'},{'symbol':'002014','name':'永新股份'},
        {'symbol':'002799','name':'环球印务'},
    ],
    '纺织制造': [
        {'symbol':'002042','name':'华孚时尚'},{'symbol':'002563','name':'森马服饰'},
        {'symbol':'603116','name':'红蜻蜓'},{'symbol':'002327','name':'富安娜'},
        {'symbol':'603558','name':'健盛集团'},
    ],
    '厨卫电器': [
        {'symbol':'002032','name':'苏泊尔'},{'symbol':'002035','name':'华帝股份'},
        {'symbol':'603486','name':'科沃斯'},{'symbol':'002614','name':'奥佳华'},
        {'symbol':'002508','name':'老板电器'},
    ],
    '黑色家电': [
        {'symbol':'600060','name':'海信视像'},{'symbol':'000100','name':'TCL科技'},
        {'symbol':'000016','name':'深康佳A'},{'symbol':'002429','name':'兆驰股份'},
        {'symbol':'600839','name':'四川长虹'},
    ],
    '小家电': [
        {'symbol':'002032','name':'苏泊尔'},{'symbol':'002242','name':'九阳股份'},
        {'symbol':'603868','name':'飞科电器'},{'symbol':'002959','name':'小熊电器'},
        {'symbol':'603355','name':'莱克电气'},
    ],
    '汽车服务及其他': [
        {'symbol':'601258','name':'庞大集团'},{'symbol':'600297','name':'广汇汽车'},
        {'symbol':'603377','name':'东方时尚'},{'symbol':'000996','name':'中国中期'},
    ],
    '贸易': [
        {'symbol':'600755','name':'厦门国贸'},{'symbol':'600704','name':'物产中大'},
        {'symbol':'000829','name':'天音控股'},{'symbol':'600278','name':'东方创业'},
        {'symbol':'002091','name':'江苏国泰'},
    ],
    '燃气': [
        {'symbol':'600917','name':'重庆燃气'},{'symbol':'601139','name':'深圳燃气'},
        {'symbol':'600681','name':'百川能源'},{'symbol':'600333','name':'长春燃气'},
        {'symbol':'000593','name':'大通燃气'},
    ],
    '油气开采及服务': [
        {'symbol':'600028','name':'中国石化'},{'symbol':'601857','name':'中国石油'},
        {'symbol':'600938','name':'中国海油'},{'symbol':'601808','name':'中海油服'},
        {'symbol':'600871','name':'石化油服'},
    ],
    '影视院线': [
        {'symbol':'002739','name':'万达电影'},{'symbol':'300133','name':'华策影视'},
        {'symbol':'300251','name':'光线传媒'},{'symbol':'600977','name':'中国电影'},
        {'symbol':'600715','name':'文投控股'},
    ],
    '综合': [
        {'symbol':'600805','name':'悦达投资'},{'symbol':'600620','name':'天宸股份'},
        {'symbol':'000009','name':'中国宝安'},{'symbol':'600653','name':'申华控股'},
        {'symbol':'600212','name':'绿能慧充'},
    ],
    '化学制品': [
        {'symbol':'600309','name':'万华化学'},{'symbol':'002601','name':'龙佰集团'},
        {'symbol':'002648','name':'卫星化学'},{'symbol':'600346','name':'恒力石化'},
        {'symbol':'000301','name':'东方盛虹'},{'symbol':'600352','name':'浙江龙盛'},
        {'symbol':'002092','name':'中泰化学'},{'symbol':'603260','name':'合盛硅业'},
    ],
    '文化传媒': [
        {'symbol':'300413','name':'芒果超媒'},{'symbol':'603721','name':'中广天择'},
        {'symbol':'300251','name':'光线传媒'},{'symbol':'300133','name':'华策影视'},
        {'symbol':'002739','name':'万达电影'},{'symbol':'600977','name':'中国电影'},
        {'symbol':'600633','name':'浙数文化'},{'symbol':'300031','name':'宝通科技'},
    ],
    '电力': [
        {'symbol':'600900','name':'长江电力'},{'symbol':'600025','name':'华能水电'},
        {'symbol':'600011','name':'华能国际'},{'symbol':'600886','name':'国投电力'},
        {'symbol':'601985','name':'中国核电'},{'symbol':'003816','name':'中国广核'},
        {'symbol':'600795','name':'国电电力'},{'symbol':'600023','name':'浙能电力'},
        {'symbol':'600905','name':'三峡能源'},{'symbol':'601991','name':'大唐发电'},
        {'symbol':'600027','name':'华电国际'},{'symbol':'001289','name':'龙源电力'},
    ],
    '汽车零部件': [
        {'symbol':'601689','name':'拓普集团'},{'symbol':'002920','name':'德赛西威'},
        {'symbol':'601799','name':'星宇股份'},{'symbol':'603596','name':'伯特利'},
        {'symbol':'002048','name':'宁波华翔'},{'symbol':'600741','name':'华域汽车'},
        {'symbol':'002126','name':'银轮股份'},{'symbol':'601058','name':'赛轮轮胎'},
    ],
    '多元金融': [
        {'symbol':'600816','name':'建元信托'},{'symbol':'000617','name':'中油资本'},
        {'symbol':'600390','name':'五矿资本'},{'symbol':'002423','name':'中粮资本'},
        {'symbol':'600318','name':'新力金融'},{'symbol':'600901','name':'江苏金租'},
    ],
    '工业金属': [
        {'symbol':'601899','name':'紫金矿业'},{'symbol':'603993','name':'洛阳钼业'},
        {'symbol':'000630','name':'铜陵有色'},{'symbol':'000807','name':'云铝股份'},
        {'symbol':'600362','name':'江西铜业'},{'symbol':'601600','name':'中国铝业'},
        {'symbol':'002203','name':'海亮股份'},{'symbol':'600219','name':'南山铝业'},
        {'symbol':'000933','name':'神火股份'},
    ],
    '金属新材料': [
        {'symbol':'300748','name':'金力永磁'},{'symbol':'600980','name':'北矿科技'},
        {'symbol':'300811','name':'铂科新材'},{'symbol':'300224','name':'正海磁材'},
    ],
}

# Apply fixes
for name, stocks in fixes.items():
    data[name] = stocks

# Save
with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

total = sum(len(v) for v in data.values())
filled = sum(1 for v in data.values() if len(v) > 0)
empty = sum(1 for v in data.values() if len(v) == 0)
print(f'Total: {len(data)} industries, {total} stocks')
print(f'Filled: {filled}/{len(data)}, Empty: {empty}')
if empty:
    print(f'Empty industries: {[k for k,v in data.items() if len(v)==0]}')
