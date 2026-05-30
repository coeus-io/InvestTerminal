"""
投资决策仪表盘 v4 — 自选股 50+ / 智能推荐 / adata 实时行情
"""

import json, os, sys, time, threading, statistics, random
from datetime import datetime
from flask import Flask, jsonify, send_from_directory, request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from python_tools.config import DEFAULT_START_DATE, DATA_DIR, REPORT_DIR
from python_tools.data.cache import stats as cache_stats
from python_tools.data.industry_cache import cache_stats as industry_stats
from python_tools.data.akshare_data import get_daily_price, get_stock_info

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
WATCHLIST_FILE = os.path.join(DATA_DIR, "watchlist.json")
INDUSTRY_CACHE_FILE = os.path.join(DATA_DIR, "industry_analysis_cache.json")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
os.makedirs(DATA_DIR, exist_ok=True)

_ANALYSIS_IN_PROGRESS = False
_ANALYSIS_PROGRESS = ""

# ── 行业全量分析 ──────────────────────────────────────────────
def _analyse_one_industry(name, stocks):
    """全维度行业分析 — ROE/毛利率/净利率/负债率/EPS/营收增长/总市值"""
    roes, gms, nms, drs, epss, revs, caps = [], [], [], [], [], [], []
    detail = []
    for s in stocks:
        sym = s.get("symbol", ""); nm = s.get("name", "")
        try:
            info = get_stock_info(sym)
            if not info: continue
            row = {"symbol": sym, "name": nm}

            def p(v):
                try:
                    f = float(str(v).replace("%","").replace(",",""))
                    return f if abs(f) < 200 else 0
                except: return 0

            roe = p(info.get("净资产收益率", "0"))
            if roe: roes.append(roe); row["roe"] = roe

            gm = p(info.get("销售毛利率", "0"))
            if gm and abs(gm) < 100: gms.append(gm); row["gross_margin"] = gm

            nm = p(info.get("销售净利率", "0"))
            if nm and abs(nm) < 100: nms.append(nm); row["net_margin"] = nm

            dr = p(info.get("资产负债率", "0"))
            if dr and abs(dr) < 100: drs.append(dr); row["debt_ratio"] = dr

            eps = p(info.get("基本每股收益", "0"))
            if eps: epss.append(eps); row["eps"] = eps

            rev_g = info.get("营业总收入同比增长率","")
            rv = p(rev_g)
            if rv: revs.append(rv); row["revenue_growth"] = rv

            cap_str = info.get("总市值","")
            if cap_str:
                try:
                    cv = float(str(cap_str).replace(",",""))
                    if cv > 0: caps.append(cv); row["market_cap"] = round(cv/1e8, 1)
                except: pass

            detail.append(row)
        except: continue

    result = {"stock_count": len(stocks)}
    if roes: roes.sort(); result["roe_median"] = round(statistics.median(roes), 2); result["roe_mean"] = round(sum(roes)/len(roes), 2)
    if gms: gms.sort(); result["gross_margin_median"] = round(statistics.median(gms), 2)
    if nms: nms.sort(); result["net_margin_median"] = round(statistics.median(nms), 2)
    if drs: drs.sort(); result["debt_ratio_median"] = round(statistics.median(drs), 2)
    if epss: epss.sort(); result["eps_median"] = round(statistics.median(epss), 2)
    if revs: revs.sort(); result["revenue_growth_median"] = round(statistics.median(revs), 2)
    if caps: caps.sort(); result["market_cap_median"] = round(statistics.median(caps)/1e8, 1)

    result["top_roe"] = sorted([d for d in detail if d.get("roe")], key=lambda x: x["roe"], reverse=True)[:5]
    result["top_gm"] = sorted([d for d in detail if d.get("gross_margin")], key=lambda x: x["gross_margin"], reverse=True)[:5]
    result["all_stocks"] = sorted(detail, key=lambda x: x.get("roe", 0), reverse=True)[:30]
    result["source"] = "live"
    return result

def _threaded_analyse_all():
    global _ANALYSIS_IN_PROGRESS, _ANALYSIS_PROGRESS
    _ANALYSIS_IN_PROGRESS = True; _ANALYSIS_PROGRESS = "启动中"
    try:
        with open(os.path.join(DATA_DIR, "industry_stocks.json"), "r", encoding="utf-8") as f:
            ind_data = json.load(f)
        names = sorted(ind_data.keys()); results = {}
        for i, name in enumerate(names, 1):
            _ANALYSIS_PROGRESS = f"{i}/{len(names)} {name}"
            stocks = ind_data.get(name, [])
            if stocks: results[name] = _analyse_one_industry(name, stocks)
            if i % 5 == 0:
                with open(INDUSTRY_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump({"cached_at": datetime.now().isoformat(), "industries": results, "progress": f"{i}/{len(names)}"}, f, ensure_ascii=False, indent=2)
        with open(INDUSTRY_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"cached_at": datetime.now().isoformat(), "industries": results, "progress": "done"}, f, ensure_ascii=False, indent=2)
    finally:
        _ANALYSIS_IN_PROGRESS = False; _ANALYSIS_PROGRESS = ""

# ── 自选股 ──────────────────────────────────────────────────
def _load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return [{"symbol":"600519","name":"贵州茅台"},{"symbol":"000858","name":"五粮液"},{"symbol":"300750","name":"宁德时代"},{"symbol":"000333","name":"美的集团"},{"symbol":"600036","name":"招商银行"},{"symbol":"601318","name":"中国平安"},{"symbol":"600276","name":"恒瑞医药"},{"symbol":"002594","name":"比亚迪"},{"symbol":"600406","name":"国电南瑞"},{"symbol":"000400","name":"许继电气"},{"symbol":"300001","name":"特锐德"},{"symbol":"000682","name":"东方电子"},{"symbol":"300308","name":"中际旭创"},{"symbol":"300502","name":"新易盛"},{"symbol":"300394","name":"天孚通信"},{"symbol":"002281","name":"光迅科技"},{"symbol":"688048","name":"长光华芯"},{"symbol":"300570","name":"太辰光"},{"symbol":"300913","name":"兆龙互连"},{"symbol":"688313","name":"仕佳光子"}]
def _save_watchlist(wl):
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(wl, f, ensure_ascii=False, indent=2)

# ── Routes ──────────────────────────────────────────────────
@app.route("/")

def index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(STATIC_DIR, "favicon.svg")

@app.route("/api/status")
def api_status():
    try:
        with open(os.path.join(DATA_DIR, "industry_stocks.json"), "r", encoding="utf-8") as f:
            ind_data = json.load(f)
        total = len(ind_data); filled = sum(1 for v in ind_data.values() if len(v)>0); ts = sum(len(v) for v in ind_data.values())
        ac = {}
        if os.path.exists(INDUSTRY_CACHE_FILE):
            with open(INDUSTRY_CACHE_FILE, "r", encoding="utf-8") as f: ac = json.load(f)
        cached = ac.get("industries", {}); analysed = sum(1 for v in cached.values() if v.get("roe_median"))
        cs = cache_stats(); reports = [f for f in os.listdir(REPORT_DIR) if f.endswith((".png",".md"))] if os.path.exists(REPORT_DIR) else []
        import requests; src_ok=0
        for u in ["https://money.finance.sina.com.cn","https://push2.eastmoney.com","https://data.eastmoney.com"]:
            try: r=requests.get(u,timeout=3,proxies={"http":None,"https":None}); src_ok+=1 if r.status_code<500 else 0
            except: pass
        # 持仓盈亏
        portfolio = {"total_cost":0,"total_market":0,"total_pnl":0,"total_pnl_pct":0,"holding_count":0}
        try:
            from python_tools.portfolio.tracker import load as load_holdings
            holdings = load_holdings()
            if holdings:
                import adata
                codes = [h["symbol"] for h in holdings]
                df = adata.stock.market.list_market_current(code_list=codes)
                if not df.empty:
                    pm = dict(zip(df["stock_code"], df["price"]))
                    for h in holdings:
                        cost = h.get("cost_price",0) * h.get("shares",0)
                        px = float(pm.get(h["symbol"],0))
                        mv = px * h.get("shares",0) if px else 0
                        portfolio["total_cost"] += cost
                        portfolio["total_market"] += mv
                        portfolio["holding_count"] += 1
                    if portfolio["total_cost"] > 0:
                        portfolio["total_pnl"] = portfolio["total_market"] - portfolio["total_cost"]
                        portfolio["total_pnl_pct"] = round(portfolio["total_pnl"] / portfolio["total_cost"] * 100, 2)
        except Exception as e:
            print(f"[portfolio] calc failed: {e}", file=__import__('sys').stderr)

        return jsonify({"health":{"sources_ok":src_ok,"sources_total":3,"all_green":src_ok==3,"cache_entries":cs.get("total_entries",0),"reports_count":len(reports),"analysis_progress":ac.get("progress","")},"coverage":{"industries_filled":filled,"industries_total":total,"total_stocks":ts,"fill_pct":round(filled/total*100,0) if total else 0,"analysed_count":analysed},"freshness":{"analysis_cached_at":ac.get("cached_at")},"portfolio":{"total_cost":round(portfolio["total_cost"],2),"total_market":round(portfolio["total_market"],2),"total_pnl":round(portfolio["total_pnl"],2),"total_pnl_pct":portfolio["total_pnl_pct"],"holding_count":portfolio["holding_count"]}})
    except Exception as e: return jsonify({"error":str(e)})

@app.route("/api/industry")
def api_industry():
    try:
        ac = {}
        if os.path.exists(INDUSTRY_CACHE_FILE):
            with open(INDUSTRY_CACHE_FILE,"r",encoding="utf-8") as f: ac=json.load(f)
        cached=ac.get("industries",{})
        with open(os.path.join(DATA_DIR,"industry_stocks.json"),"r",encoding="utf-8") as f: ind_data=json.load(f)
        result=[]
        for name,stocks in sorted(ind_data.items()):
            e={"name":name,"stock_count":len(stocks),
               "roe_median":None,"gross_margin_median":None,"net_margin_median":None,
               "debt_ratio_median":None,"eps_median":None,"revenue_growth_median":None,
               "market_cap_median":None,"top_roe":[],"all_stocks":[],"source":"pending"}
            if name in cached and cached[name].get("roe_median"):
                c=cached[name]
                for field in ["roe_median","roe_mean","gross_margin_median","net_margin_median",
                              "debt_ratio_median","eps_median","revenue_growth_median",
                              "market_cap_median","top_roe","all_stocks"]:
                    e[field] = c.get(field)
                e["source"] = "cache"
            result.append(e)
        pending=sum(1 for r in result if r["roe_median"] is None)
        if not _ANALYSIS_IN_PROGRESS and pending>10:
            threading.Thread(target=_threaded_analyse_all,daemon=True).start()
        return jsonify({"industries":result,"total":len(result),"analysed":sum(1 for r in result if r["roe_median"]),"pending":pending,"analysis_running":_ANALYSIS_IN_PROGRESS,"progress":_ANALYSIS_PROGRESS})
    except Exception as e: return jsonify({"error":str(e)})

@app.route("/api/industry/<name>")
def api_industry_single(name):
    try:
        with open(os.path.join(DATA_DIR,"industry_stocks.json"),"r",encoding="utf-8") as f: ind_data=json.load(f)
        stocks=ind_data.get(name,[])
        if not stocks: return jsonify({"error":f"未找到行业 {name}"})
        return jsonify(_analyse_one_industry(name,stocks))
    except Exception as e: return jsonify({"error":str(e)})

@app.route("/api/industry/analyse", methods=["POST"])
def api_industry_analyse():
    if _ANALYSIS_IN_PROGRESS: return jsonify({"status":"already_running"})
    threading.Thread(target=_threaded_analyse_all,daemon=True).start()
    return jsonify({"status":"started"})

@app.route("/api/watchlist/search")
def api_watchlist_search():
    q = request.args.get("q","").strip()
    if len(q)<1: return jsonify({"candidates":[]})
    seen=set(); result=[]
    for industry_name,stocks in json.load(open(os.path.join(DATA_DIR,"industry_stocks.json"),"r",encoding="utf-8")).items():
        for s in stocks:
            sym=s.get("symbol",""); nm=s.get("name","")
            if (q in sym or q in nm) and sym not in seen:
                seen.add(sym); result.append({"symbol":sym,"name":nm,"industry":industry_name})
    return jsonify({"candidates":result[:50]})

@app.route("/api/watchlist", methods=["GET","POST","DELETE"])
def api_watchlist():
    if request.method=="GET":
        wl=_load_watchlist()
        enriched=[]
        try:
            import adata
            codes = [w["symbol"] for w in wl]
            df = adata.stock.market.list_market_current(code_list=codes)
            if not df.empty:
                price_map = dict(zip(df["stock_code"], df["price"]))
                chg_map = dict(zip(df["stock_code"], df["change_pct"]))
                for item in wl:
                    s=item["symbol"]
                    p=float(price_map[s]) if s in price_map else None
                    c=float(chg_map[s]) if s in chg_map else None
                    enriched.append({"symbol":s,"name":item.get("name",s),"price":p,"change_pct":c})
                return jsonify({"watchlist":enriched})
        except: pass
        # fallback
        for item in wl:
            sym=item["symbol"]
            try:
                p=get_daily_price(sym,start_date=DEFAULT_START_DATE)
                price=round(p["close"].iloc[0],2) if not p.empty and len(p)>=2 else None
                chg=round((p["close"].iloc[0]-p["close"].iloc[1])/p["close"].iloc[1]*100,2) if not p.empty and len(p)>=2 else None
            except: price=None;chg=None
            enriched.append({"symbol":sym,"name":item.get("name",sym),"price":price,"change_pct":chg})
        return jsonify({"watchlist":enriched})
    elif request.method=="POST":
        data=request.json; sym=data.get("symbol","").strip(); nm=data.get("name","").strip()
        if not sym: return jsonify({"error":"symbol required"}),400
        wl=_load_watchlist()
        if any(w["symbol"]==sym for w in wl): return jsonify({"error":"already exists"}),409
        if not nm:
            try: info=get_stock_info(sym); nm=info.get("股票简称",sym)
            except: nm=sym
        wl.append({"symbol":sym,"name":nm}); _save_watchlist(wl)
        return jsonify({"status":"added","symbol":sym,"name":nm})
    elif request.method=="DELETE":
        data=request.json; sym=data.get("symbol","").strip()
        wl=_load_watchlist(); wl=[w for w in wl if w["symbol"]!=sym]; _save_watchlist(wl)
        return jsonify({"status":"deleted"})

@app.route("/api/screening")
def api_screening():
    """
    智能推荐股 — 使用行业分析缓存 + adata 实时行情
    不需要逐个调 get_stock_info（太慢）
    """
    try:
        with open(os.path.join(DATA_DIR, "industry_stocks.json"), "r", encoding="utf-8") as f: ind_data = json.load(f)
        ac = {}
        if os.path.exists(INDUSTRY_CACHE_FILE):
            with open(INDUSTRY_CACHE_FILE, "r", encoding="utf-8") as f: ac = json.load(f)
        cached = ac.get("industries", {})

        # Phase 1: 从全部行业缓存收集标的（按ROE排序）
        ind_list = []
        for ind_name, ci in cached.items():
            if not ci.get("roe_median"): continue
            stocks = ind_data.get(ind_name, [])
            if not stocks: continue
            ind_list.append((ind_name, ci["roe_median"], ci.get("gross_margin_median"), ci.get("net_margin_median")))

        # 按ROE中位数降序排
        ind_list.sort(key=lambda x: x[1], reverse=True)

        result = []; seen = set()
        for ind_name, roe_m, gm_m, nm_m in ind_list:
            ci = cached.get(ind_name, {})
            top_stocks = ci.get("top_roe", [])
            if not top_stocks:
                stocks = ind_data.get(ind_name, [])
                top_stocks = [{"symbol":s["symbol"],"name":s["name"],"roe":0} for s in stocks[:2]]

            for s in top_stocks[:3]:
                if s["symbol"] in seen: continue
                seen.add(s["symbol"])
                result.append({
                    "symbol": s["symbol"], "name": s.get("name",""), "industry": ind_name,
                    "roe": str(s.get("roe","")) if s.get("roe") else str(roe_m)+"% (行业)",
                    "gross_margin": str(gm_m) if gm_m else "--",
                    "industry_roe": roe_m,  # for sorting
                })
                if s["symbol"] in seen: continue
                seen.add(s["symbol"])
                ci = cached.get(ind_name, {})
                result.append({
                    "symbol": s["symbol"], "name": s.get("name",""), "industry": ind_name,
                    "roe": str(s.get("roe","")) if s.get("roe") else \
                           (str(ci.get("roe_median",""))+"% (行业)" if ci.get("roe_median") else "--"),
                    "gross_margin": ci.get("gross_margin_median","--") if ci.get("gross_margin_median") else "--",
                })

        # Phase 2: 一次性拿实时行情（adata，极快）
        try:
            import adata
            codes = [r["symbol"] for r in result]
            df = adata.stock.market.list_market_current(code_list=codes)
            if not df.empty:
                pm = dict(zip(df["stock_code"], df["price"]))
                cm = dict(zip(df["stock_code"], df["change_pct"]))
                for r in result:
                    r["price"] = round(float(pm[r["symbol"]]), 2) if r["symbol"] in pm else None
                    r["change_pct"] = round(float(cm[r["symbol"]]), 2) if r["symbol"] in cm else None
        except: pass

        result.sort(key=lambda x: x.get("industry_roe", 0), reverse=True)
        return jsonify({"recommendations": result[:120], "total": len(result)})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/market")
def api_market():
    indices=[]
    import requests
    sina_map={"000001":"sh000001","399001":"sz399001","000688":"sh000688","399006":"sz399006"}
    name_map={"000001":"上证指数","399001":"深证成指","000688":"科创50","399006":"创业板指"}
    for code,sym in sina_map.items():
        nm=name_map.get(code,code)
        try:
            r=requests.get(f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sym}&scale=240&ma=no&datalen=3",timeout=8,proxies={"http":None,"https":None},headers={"Referer":"https://finance.sina.com.cn"})
            if r.status_code==200 and r.text.strip():
                data=r.json()
                if len(data)>=2:
                    c0=float(data[0]["close"]); c1=float(data[1]["close"])
                    indices.append({"name":nm,"value":round(c0,2),"change":round((c0-c1)/c1*100,2)})
        except: pass
    return jsonify({"indices":indices})

if __name__ == "__main__":
    import webbrowser, threading
    print("📊 投资决策仪表盘 v4 启动中...")
    print("   访问: http://localhost:5000")
    print("   菜单: 总览 | 行业全景 | 推荐股 | 自选股")
    threading.Timer(1.0, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
