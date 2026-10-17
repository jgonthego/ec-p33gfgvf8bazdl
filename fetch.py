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
"""
import glob, json, os, re, sys
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
    os.makedirs(f"{ROOT}/data", exist_ok=True)
    p = f"{ROOT}/data/week-{week}.json"; json.dump(out, open(p, "w"), indent=2)
    print(f"{len(rows)} rows, {len(gaps)} gaps -> {p}")
    for g in gaps: print("GAP", *g)

if __name__ == "__main__":
    main()
