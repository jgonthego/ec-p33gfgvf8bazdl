#!/usr/bin/env python3
"""Normalize Robinhood MCP responses into data/week-YYYY-MM-DD.json (committed; CI builds from it).

Robinhood market data is reachable only through an agent's READ-ONLY MCP tool calls
(namespace user-Robinhood-xai), not from CI. Each week an agent saves raw responses
into data/raw/ (gitignored, never committed or published):
  cal/     get_earnings_calendar (one day per call, filter=high_market_cap)
  er/      get_earnings_results  (per-ticker fallback when the calendar is truncated)
  quotes/  get_equity_quotes     (<=12 symbols per call)
  inst/<SYM>.txt get_option_instruments (ATM strike, chosen expiry; call+put)
  optq/    get_option_quotes     (<=10 ids per call)
Never call order, alert, watchlist, or exercise tools.

Rules: expiry = first expiration on/after the report date, strictly after it for
after-close/unconfirmed reports. ATM strike must be within 5% of the price, else skip.
Move = (call mid + put mid) / price. Expiry > 8 days after report => flagged.
Usage: python3 fetch.py 2026-10-19 "Oct 15, 2026, 12:20 AM ET"

Earnings-watch cards (per-ticker fundamentals + correlations). Extra raw folders:
  fin/   get_financials period=quarterly limit=1 (<=20 symbols per call)
  er/    get_earnings_results (one symbol per call; also used above for calendar gaps)
  fund/  get_equity_fundamentals (<=10 symbols per call; market cap, sector, industry)
  hist/  get_equity_historicals interval=day, ~4 months back (<=10 symbols per call) for every
         reporter and every symbol in PEERS (print the list with: python3 fetch.py --universe)
main() merges these automatically when present. To add cards to an existing week JSON without
re-deriving the expected moves:  python3 fetch.py --cards data/week-2026-10-19.json
"""
import glob, json, math, os, re, sys
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = f"{ROOT}/data/raw"
MAX_STRIKE_DIST, LONG_GAP_DAYS = 0.05, 8

# Curated notable / high-volume names (edit weekly). Name shown on page.
TICKERS = {
 "AAL":"American Airlines","ABT":"Abbott","ALLY":"Ally Financial","AMX":"América Movil","AXP":"American Express",
 "BCS":"Barclays","BE":"Bloom Energy","BX":"Blackstone","CB":"Chubb","CLF":"Cleveland-Cliffs","CMCSA":"Comcast",
 "CME":"CME Group","COF":"Capital One","CSX":"CSX","DHR":"Danaher","E":"Eni","ELV":"Elevance Health",
 "FITB":"Fifth Third","GE":"GE Aerospace","GM":"General Motors","HAL":"Halliburton","HON":"Honeywell","IBM":"IBM",
 "ISRG":"Intuitive Surgical","KEY":"KeyCorp","KMI":"Kinder Morgan","LMT":"Lockheed Martin","LRCX":"Lam Research",
 "LUV":"Southwest Airlines","LVS":"Las Vegas Sands","MCO":"Moody's","META":"Meta Platforms","MMM":"3M",
 "NDAQ":"Nasdaq Inc.","NEE":"NextEra Energy","NEM":"Newmont","NFLX":"Netflix","NOC":"Northrop Grumman",
 "NOK":"Nokia","NSC":"Norfolk Southern","PG":"Procter & Gamble","PHM":"PulteGroup","PM":"Philip Morris",
 "RTX":"RTX","SAP":"SAP","SLB":"SLB","SPOT":"Spotify","STLD":"Steel Dynamics","SYF":"Synchrony","T":"AT&T",
 "TMO":"Thermo Fisher","TSLA":"Tesla","TXN":"Texas Instruments","UAL":"United Airlines","UNP":"Union Pacific",
 "URI":"United Rentals","VLO":"Valero","WDC":"Western Digital","ZION":"Zions",
}

# Candidate peers for correlation (same-sector names + broad/sector ETFs). Edit as TICKERS change.
_BANKS = ["FITB","KEY","ZION","RF","HBAN","CFG","MTB","TFC","USB","PNC","KRE","KBE","XLF","SPY"]
_CARDS = ["COF","SYF","ALLY","AXP","V","MA","KRE","XLF","SPY"]
_DEF = ["LMT","NOC","GD","RTX","LHX","BA","ITA","XLI","SPY"]
_AIR = ["DAL","UAL","AAL","LUV","ALK","JETS","SPY"]
_RAIL = ["UNP","CSX","NSC","CP","CNI","IYT","XLI","SPY"]
_EXCH = ["CME","ICE","CBOE","NDAQ","MCO","SPGI","MSCI","XLF","SPY"]
_TOOLS = ["TMO","DHR","A","WAT","MTD","IQV","XLV","SPY"]
_MED = ["ABT","MDT","BSX","SYK","ISRG","JNJ","IHI","XLV","SPY"]
_OILSVC = ["SLB","HAL","BKR","XOM","CVX","OIH","XLE","SPY"]
_IND = ["HON","MMM","GE","EMR","ITW","ETN","XLI","SPY"]
_STEEL = ["CLF","STLD","NUE","CMC","RS","AA","FCX","XME","XLB","SPY"]
_TEL = ["T","VZ","TMUS","CMCSA","CHTR","XLC","SPY"]
_STREAM = ["NFLX","SPOT","DIS","ROKU","WBD","LYV","CMCSA","XLC","QQQ","SPY"]
PEERS = {
 "CLF":_STEEL, "STLD":_STEEL, "FITB":_BANKS, "ZION":_BANKS, "KEY":_BANKS,
 "ALLY":_CARDS, "SYF":_CARDS, "COF":_CARDS, "AXP":_CARDS,
 "GE":["RTX","HON","GEV","BA","HWM","TDG","ITA","XLI","SPY"], "GM":["F","TSLA","STLA","TM","XLY","SPY"],
 "HAL":_OILSVC, "SLB":_OILSVC, "MMM":_IND, "HON":_IND, "NOC":_DEF, "RTX":_DEF, "LMT":_DEF,
 "AMX":["TMUS","T","VZ","TEF","EWW","XLC","SPY"], "CB":["TRV","ALL","PGR","AIG","HIG","KIE","XLF","SPY"],
 "ISRG":_MED, "ABT":_MED, "NFLX":_STREAM, "SPOT":_STREAM, "UAL":_AIR, "AAL":_AIR, "LUV":_AIR,
 "CME":_EXCH, "NDAQ":_EXCH, "MCO":_EXCH, "DHR":_TOOLS, "TMO":_TOOLS,
 "ELV":["UNH","CI","HUM","CVS","CNC","MOH","XLV","SPY"], "NEE":["DUK","SO","AEP","D","XLU","SPY"],
 "PM":["MO","BTI","KO","PG","XLP","SPY"], "T":_TEL, "CMCSA":_TEL+["DIS","NFLX"],
 "CSX":_RAIL, "NSC":_RAIL, "UNP":_RAIL, "IBM":["ACN","ORCL","MSFT","HPE","CSCO","XLK","QQQ","SPY"],
 "KMI":["WMB","OKE","ET","EPD","XLE","AMLP","SPY"], "LRCX":["AMAT","KLAC","ASML","MU","SMH","QQQ","SPY"],
 "LVS":["WYNN","MGM","CZR","XLY","SPY"], "META":["GOOGL","AMZN","MSFT","SNAP","PINS","XLC","QQQ","SPY"],
 "SAP":["ORCL","CRM","MSFT","NOW","IGV","QQQ","SPY"], "TSLA":["RIVN","LCID","NVDA","GM","F","XLY","ARKK","QQQ","SPY"],
 "TXN":["ADI","MCHP","NXPI","ON","INTC","SMH","QQQ","SPY"], "URI":["CAT","DE","ETN","PWR","XLI","SPY"],
 "BCS":["HSBC","DB","UBS","ING","SAN","EUFN","XLF","SPY"], "BX":["KKR","APO","ARES","CG","BLK","XLF","SPY"],
 "NOK":["ERIC","CSCO","CIEN","XLK","QQQ","SPY"], "PG":["CL","KMB","CLX","KO","PEP","XLP","SPY"],
 "PHM":["DHI","LEN","TOL","NVR","KBH","ITB","XHB","SPY"], "VLO":["MPC","PSX","PBF","DK","XLE","SPY"],
 "BE":["PLUG","FCEL","ENPH","FSLR","GEV","TAN","ICLN","SPY"], "NEM":["AEM","KGC","WPM","FNV","GDX","GLD","SPY"],
 "WDC":["STX","MU","SNDK","NTAP","SMH","QQQ","SPY"],
}

ETFS = {"SPY","QQQ","IWM","DIA","XLF","KRE","KBE","KIE","XLI","XLE","XLV","XLK","XLY","XLP","XLU","XLB","XLC","SMH","IGV","IHI",
        "ITA","JETS","IYT","OIH","AMLP","XME","XHB","ITB","EUFN","EWW","GDX","GLD","TAN","ICLN","ARKK"}
CORR_RETURNS = 65   # daily close-to-close returns per correlation window
FEATURED = []       # e.g. ["NFLX","TSLA"]; empty = the two largest reporters by Robinhood market cap

# Cross-check notes (checked against a public calendar for missing names; only Robinhood data is published).
CROSSCHECK_NOTES = ["Also checked: FIX and ITW; Robinhood lists their next reports on Oct 30 and Oct 27, outside this week."]

def et(s):
    s = re.sub(r"(\.\d{6})\d*", r"\1", s).replace("Z", "+00:00")
    return datetime.fromisoformat(s).astimezone(ET).strftime("%Y-%m-%d %I:%M %p ET")

def read(pattern):
    for f in sorted(glob.glob(pattern)): yield open(f).read()

def main():
    week = date.fromisoformat(sys.argv[1]); retrieved = sys.argv[2]
    days = {(week + timedelta(i)).isoformat() for i in range(5)}
    cal, truncated = {}, []
    for f in sorted(glob.glob(f"{RAW}/cal/*.txt")):
        d = open(f).read()
        if "truncated" in d: truncated.append(os.path.basename(f))
        for s, dt, t in re.findall(r'"symbol":"(\w+)".*?"date":"([\d-]+)","timing":"?(\w+)', d): cal[s] = (dt, t)
    for d in read(f"{RAW}/er/*.txt"):   # per-ticker results fill calendar truncation
        for s, dt, t in re.findall(r'"symbol":"(\w+)".*?"date":"([\d-]+)","timing":"?(\w+)', d):
            if dt in days or (s not in cal): cal[s] = (dt, t)
    quotes = {}
    for d in read(f"{RAW}/quotes/*.txt"):
        for m in re.finditer(r'"symbol":"(\w+)","last_trade_price":"([\d.]+)","venue_last_trade_time":"([^"]+)"', d):
            quotes[m[1]] = (float(m[2]), et(m[3]))
    inst = {}
    for d in read(f"{RAW}/inst/*.txt"):
        for i, sym, exp, k, typ in re.findall(r'"id":"([0-9a-f-]{36})","chain_id":"[^"]*","chain_symbol":"(\w+)".*?"expiration_date":"([\d-]+)".*?"strike_price":"([\d.]+)","type":"(\w+)"', d):
            inst.setdefault(sym, {})[typ] = (i, exp, float(k))
    oq = {}
    for d in read(f"{RAW}/optq/*.txt"):
        for m in re.finditer(r'"instrument_id":"([0-9a-f-]{36})","ask_price":"([\d.]+)".*?"bid_price":"([\d.]+)".*?"updated_at":"([^"]+)"', d):
            oq[m[1]] = (float(m[3]), float(m[2]), et(m[4]))
    rows, gaps = [], []
    for sym, name in TICKERS.items():
        if sym not in cal or cal[sym][0] not in days: gaps.append((sym, "Robinhood shows no report date this week")); continue
        dt, t = cal[sym]; timing = {"am": "Before open", "pm": "After close"}.get(t, "Unconfirmed")
        if sym not in quotes: gaps.append((sym, "no Robinhood stock quote")); continue
        price, pts = quotes[sym]
        c, p = inst.get(sym, {}).get("call"), inst.get(sym, {}).get("put")
        if not c or not p: gaps.append((sym, "no usable option chain on Robinhood")); continue
        exp, k = date.fromisoformat(c[1]), c[2]; rd = date.fromisoformat(dt)
        if exp < rd or (exp == rd and timing != "Before open"):
            gaps.append((sym, f"expiry {exp} settles before the report")); continue
        if abs(k - price) / price > MAX_STRIKE_DIST:
            gaps.append((sym, f"ATM strike {k:g} more than 5% from price {price:.2f}")); continue
        qc, qp = oq.get(c[0]), oq.get(p[0])
        if not qc or not qp or min(qc[0], qc[1], qp[0], qp[1]) <= 0:
            gaps.append((sym, "missing or zero option bid/ask")); continue
        cm, pm = sum(qc[:2]) / 2, sum(qp[:2]) / 2; gap = (exp - rd).days
        rows.append(dict(symbol=sym, name=name, report_date=dt, timing=timing, price=round(price, 2), price_ts=pts,
            expiration=c[1], strike=k, call_bid=qc[0], call_ask=qc[1], put_bid=qp[0], put_ask=qp[1],
            call_mid=round(cm, 3), put_mid=round(pm, 3), move_usd=round(cm + pm, 2),
            move_pct=round(100 * (cm + pm) / price, 2), quote_ts=max(qc[2], qp[2]), long_dated=gap > LONG_GAP_DAYS,
            note=(f"Nearest expiry {c[1]} is {gap} days after report (no weekly listed); figure includes non-earnings time value." if gap > LONG_GAP_DAYS else "")))
    rows.sort(key=lambda r: (r["report_date"], r["timing"] != "Before open", r["symbol"]))
    notes = list(CROSSCHECK_NOTES)
    if truncated:
        notes.append("Robinhood's calendar responses for some days were truncated; missing names were filled with per-ticker Robinhood earnings lookups.")
    out = dict(week_of=week.isoformat(), retrieved=retrieved, source="Robinhood market data",
        method="Expected move = (ATM call mid + ATM put mid) for the first expiration on or after the report date (strictly after it for after-close or unconfirmed-time reports, since a same-day expiry settles before the release), divided by the stock's last regular-session trade price. Mid = (bid+ask)/2.",
        selection="Notable, widely held, or high-volume companies reporting this week, curated by hand.",
        rows=rows, gaps=[dict(symbol=s, reason=r) for s, r in gaps], calendar_notes=notes)
    add_cards(out)
    os.makedirs(f"{ROOT}/data", exist_ok=True)
    p = f"{ROOT}/data/week-{week}.json"; json.dump(out, open(p, "w"), indent=2)
    print(f"{len(rows)} rows, {len(gaps)} gaps -> {p}")
    for g in gaps: print("GAP", *g)

# ---------- earnings-watch cards ----------
def blobs(pattern):
    """Parse saved MCP responses (JSON object, possibly wrapped in a marker line)."""
    for t in read(pattern):
        try: yield json.loads(t[t.index("{"):t.rindex("}") + 1])
        except ValueError: print("WARN unparsable raw file in", pattern)

def num(v):
    try: return None if v is None else float(v)
    except (TypeError, ValueError): return None

def pearson(a, b):
    n = len(a); ma, mb = sum(a) / n, sum(b) / n
    sa = math.sqrt(sum((x - ma) ** 2 for x in a)); sb = math.sqrt(sum((y - mb) ** 2 for y in b))
    if not sa or not sb: return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sa * sb)

def add_cards(out):
    """Attach fundamentals / correlations / profile to each row. Missing data stays None (rendered n/a)."""
    fin, eps, prof, closes = {}, {}, {}, {}
    for j in blobs(f"{RAW}/fin/*.txt"):
        for r in (j.get("data") or {}).get("results") or []:
            if r and r.get("financials"): fin[r["symbol"]] = r["financials"][0]
    for j in blobs(f"{RAW}/er/*.txt"):
        done = [q for q in (j.get("data") or {}).get("results") or [] if q and (q.get("eps") or {}).get("actual") is not None]
        if done:
            q = max(done, key=lambda q: (q["report"]["date"] or "", q["year"], q["quarter"]))
            eps[q["symbol"]] = q
    for j in blobs(f"{RAW}/fund/*.txt"):
        for r in (j.get("data") or {}).get("results") or []:
            if r: prof[r["symbol"]] = r
    for j in blobs(f"{RAW}/hist/*.txt"):
        for r in (j.get("data") or {}).get("results") or []:
            if r: closes[r["symbol"]] = {b["begins_at"][:10]: float(b["close_price"]) for b in r.get("bars") or []
                                         if not b.get("interpolated") and b.get("close_price")}
    if not (fin or eps or prof or closes): return
    # Common session calendar: dates with a real (non-interpolated) bar for >=90% of symbols. This drops a
    # partially published latest day so every pair is measured over the same 65 returns.
    cnt = {}
    for c in closes.values():
        for d in c: cnt[d] = cnt.get(d, 0) + 1
    cal = sorted(d for d, k in cnt.items() if k >= 0.9 * len(closes))
    cov = dict(fundamentals=0, correlations=0)
    for row in out["rows"]:
        s = row["symbol"]; f = fin.get(s); q = eps.get(s); p = prof.get(s)
        row["fundamentals"] = None
        if f or q:
            row["fundamentals"] = dict(
                period=(f"FQ{f['fiscal_quarter']} {f['fiscal_year']}" if f and f.get("fiscal_quarter") else None),
                period_end=f.get("period_end_date") if f else None,
                revenue=num(f.get("revenue")) if f else None, gross_profit=num(f.get("gross_profit")) if f else None,
                net_income=num(f.get("net_income")) if f else None, net_margin=num(f.get("net_margin")) if f else None,
                eps=num(q["eps"]["actual"]) if q else None, eps_estimate=num(q["eps"].get("estimate")) if q else None,
                eps_period=f"Q{q['quarter']} {q['year']}" if q else None, eps_report_date=q["report"]["date"] if q else None)
            cov["fundamentals"] += 1
        row["profile"] = dict(market_cap=num(p.get("market_cap")), sector=p.get("sector"), industry=p.get("industry")) if p else None
        row["correlations"] = None
        tgt = closes.get(s)
        if tgt and len(cal) > CORR_RETURNS and all(d in tgt for d in cal[-(CORR_RETURNS + 1):]):
            days = cal[-(CORR_RETURNS + 1):]
            ret = lambda c: [c[days[i]] / c[days[i - 1]] - 1 for i in range(1, len(days))]
            rt = ret(tgt); res = []
            for peer in PEERS.get(s, []):
                pc = closes.get(peer)
                if peer == s or not pc or any(d not in pc for d in days): continue
                r = pearson(rt, ret(pc))
                if r is not None: res.append(dict(symbol=peer, r=round(r, 2), etf=peer in ETFS))
            res.sort(key=lambda x: -x["r"])
            if res:
                row["correlations"] = dict(n_returns=CORR_RETURNS, start=days[1], end=days[-1], base=days[0],
                    stocks=[x for x in res if not x["etf"]][:4], etfs=[x for x in res if x["etf"]][:3],
                    candidates=len(res))
                cov["correlations"] += 1
    caps = sorted((r for r in out["rows"] if (r.get("profile") or {}).get("market_cap")), key=lambda r: -r["profile"]["market_cap"])
    syms = {r["symbol"] for r in out["rows"]}
    out["featured"] = [s for s in FEATURED if s in syms][:2] or [r["symbol"] for r in caps[:2]]
    out["featured_basis"] = "hand-picked" if [s for s in FEATURED if s in syms] else "two largest reporters by Robinhood market cap"
    out["cards_method"] = (f"Latest quarter: Robinhood quarterly financials (revenue, net income, net margin) and the most recent "
        f"reported 'actual' EPS from Robinhood earnings results (may be an adjusted, non-GAAP figure). Correlated stocks: Pearson "
        f"correlation of {CORR_RETURNS} daily close-to-close returns (split-adjusted regular-session closes from Robinhood) against a "
        f"hand-picked candidate list of same-sector stocks and ETFs; top 4 stocks and top 3 ETFs shown. Correlation is not causation "
        f"and says nothing about the earnings reaction.")
    print("cards:", cov, "featured:", out["featured"])

def cards_only(path):
    out = json.load(open(path)); add_cards(out); json.dump(out, open(path, "w"), indent=2); print("updated", path)

def universe():
    w = sorted(glob.glob(f"{ROOT}/data/week-*.json"))
    rows = [r["symbol"] for r in json.load(open(w[-1]))["rows"]] if w else list(TICKERS)
    u = sorted(set(rows) | {p for s in rows for p in PEERS.get(s, [])})
    for i in range(0, len(u), 10): print(json.dumps(u[i:i + 10]))

if __name__ == "__main__":
    if sys.argv[1:2] == ["--cards"]: cards_only(sys.argv[2])
    elif sys.argv[1:2] == ["--universe"]: universe()
    else: main()
