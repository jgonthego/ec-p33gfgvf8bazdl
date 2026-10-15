#!/usr/bin/env python3
"""Build static site into docs/ from data/week-*.json. Usage: python3 build.py"""
import glob, json, os, html, shutil
from datetime import date, timedelta

SITE_URL = os.environ.get("BASE", "https://jgonthego.github.io/earnings-cheatsheet").rstrip("/")
SITE_NAME = "Earnings Week Cheat Sheet"
FORMSPREE = "https://formspree.io/f/YOUR_FORM_ID"  # TODO placeholder
FEEDBACK = "d.bot@mail.grokbot.com"
# Publication gate: the site owner chose to publish the Robinhood market data and accepts the terms risk
# (decision of Oct 15, 2026). True = indexable pages, robots Allow, no preview banner.
LICENSE_CLEARED = True
ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")
e = html.escape

CSS = """body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:1100px;margin:0 auto;padding:16px;color:#111;background:#fafafa}
header a{color:inherit;text-decoration:none}nav a{margin-right:12px}
table{border-collapse:collapse;width:100%;background:#fff;font-size:14px}th,td{padding:6px 8px;border-bottom:1px solid #e5e5e5;text-align:left}
th{cursor:pointer;background:#f0f0f0;position:sticky;top:0}th:hover{background:#e4e4e4}td.n{text-align:right;font-variant-numeric:tabular-nums}
.flag{color:#a15c00;font-size:12px}.disc{background:#fff4e5;border:1px solid #f0c27b;padding:10px;border-radius:6px;font-size:14px}
.sponsor{border:2px dashed #999;padding:14px;text-align:center;color:#666;margin:20px 0}
.small{font-size:12px;color:#555}form input{padding:6px}form button{padding:6px 12px}
@media(max-width:700px){.hide-sm{display:none}}"""

SORT_JS = """document.querySelectorAll('table.sortable th').forEach((th,i)=>{th.addEventListener('click',()=>{
const t=th.closest('table'),b=t.tBodies[0],rows=[...b.rows],asc=th.dataset.asc!=='1';th.dataset.asc=asc?'1':'0';
rows.sort((a,c)=>{const x=a.cells[i].dataset.v??a.cells[i].innerText,y=c.cells[i].dataset.v??c.cells[i].innerText;
const nx=parseFloat(x),ny=parseFloat(y);const r=(!isNaN(nx)&&!isNaN(ny))?nx-ny:x.localeCompare(y);return asc?r:-r});
rows.forEach(r=>b.appendChild(r))})});"""

DISCLAIMER = ("<p class='disc'><strong>Not financial advice.</strong> This page is for informational purposes only and "
  "does not recommend buying or selling any security. Data may be delayed, incomplete, or inaccurate, and earnings dates can change. "
  "Options-implied moves are a market-derived estimate, not a forecast. Verify all information independently.</p>")

def page(title, desc, path, body, depth):
    rel = "../" * depth
    url = SITE_URL + path
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
{"" if LICENSE_CLEARED else '<meta name="robots" content="noindex,nofollow">'}
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<style>{CSS}</style></head><body>
<header><h1><a href="{rel}index.html">{SITE_NAME}</a></h1>
<nav><a href="{rel}index.html">This week</a><a href="{rel}archive/index.html">Archive</a><a href="{rel}about/index.html">Method &amp; disclaimer</a></nav></header>
{"" if LICENSE_CLEARED else "<p class='disc'><strong>Internal preview — not for publication.</strong> Data-source terms do not yet permit public display.</p>"}
<main>{body}</main>
<footer>
<!-- SPONSOR SLOT: intentionally empty. Replace with a real, clearly labeled sponsor only. -->
<div class="sponsor">Sponsor slot — available</div>
<section><h3>Get the weekly cheat sheet by email</h3>
<!-- Formspree placeholder: replace YOUR_FORM_ID before launch -->
<form action="{FORMSPREE}" method="POST"><label>Email <input type="email" name="email" required></label>
<button type="submit">Subscribe</button></form></section>
<p class="small">Feedback or corrections: <a href="mailto:{FEEDBACK}?subject=Earnings%20Cheat%20Sheet%20feedback">{FEEDBACK}</a></p>
{DISCLAIMER}</footer><script>{SORT_JS}</script></body></html>"""

def nice(d): return date.fromisoformat(d).strftime("%b %-d, %Y")
def dow(d): return date.fromisoformat(d).strftime("%a %b %-d")

def week_body(w):
    rows = []
    for r in w["rows"]:
        flag = f"<div class='flag'>⚑ {e(r['note'])}</div>" if r["note"] else ""
        rows.append(f"<tr><td><strong>{r['symbol']}</strong></td><td class='hide-sm'>{e(r['name'])}</td>"
          f"<td data-v='{r['report_date']}{'0' if r['timing']=='Before open' else '1'}'>{dow(r['report_date'])}</td><td>{r['timing']}</td>"
          f"<td class='n' data-v='{r['price']}'>${r['price']:,.2f}</td>"
          f"<td class='n' data-v='{r['move_usd']}'>±${r['move_usd']:,.2f}</td><td class='n' data-v='{r['move_pct']}'>±{r['move_pct']:.2f}%</td>"
          f"<td class='hide-sm'>{r['expiration']} @ {r['strike']:g}{flag}</td><td class='small hide-sm'>{r['quote_ts']}</td></tr>")
    gaps = "".join(f"<li>{g['symbol']}: {e(g['reason'])}</li>" for g in w["gaps"]) or "<li>None among the selected tickers.</li>"
    end = (date.fromisoformat(w["week_of"]) + timedelta(days=4)).isoformat()
    return f"""<h2>Earnings week of {nice(w['week_of'])} – {nice(end)}</h2>
<p>{len(w['rows'])} notable companies scheduled to report, with the options-implied expected move. Click any column header to sort (e.g. by date or expected move %).</p>
<p class="disc"><strong>Delayed data.</strong> Prices and option quotes may be delayed and are snapshots as of the quote time in each row; they will change before the reports.</p>
<p class="small"><strong>Source: {w['source']}, retrieved {w['retrieved']}.</strong> Stock prices are last regular-session trades ({e(w['rows'][0]['price_ts'] if w['rows'] else '')}); option bid/ask times are shown per row. Selection: {e(w['selection'])}</p>
<table class="sortable"><thead><tr><th>Ticker</th><th class='hide-sm'>Company</th><th>Report date</th><th>Timing</th><th>Price</th><th>Exp. move $</th><th>Exp. move %</th><th class='hide-sm'>Expiry @ ATM strike</th><th class='hide-sm'>Quote time</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<p class="small">Method: {e(w['method'])} ⚑ = no weekly expiration was listed, so the nearest monthly was used and the figure likely overstates the earnings-only move.</p>
<h3>Data notes</h3><ul>{''.join(f'<li>{e(c)}</li>' for c in w.get('calendar_notes',[]))}{gaps}</ul>
<p class="small">Raw data: <a href="data.json">data.json</a></p>"""

def main():
    weeks = sorted((json.load(open(f)) for f in glob.glob(f"{ROOT}/data/week-*.json")), key=lambda w: w["week_of"])
    if os.path.isdir(DOCS): shutil.rmtree(DOCS)
    os.makedirs(DOCS)
    urls = ["/"]
    for w in weeks:
        d = os.path.join(DOCS, "weeks", w["week_of"]); os.makedirs(d)
        t = f"Earnings Week of {nice(w['week_of'])}: Dates, Timing & Expected Moves | {SITE_NAME}"
        desc = f"{len(w['rows'])} earnings reports for the week of {nice(w['week_of'])} with report timing and options-implied expected moves. Free, updated weekly."
        open(f"{d}/index.html","w").write(page(t, desc, f"/weeks/{w['week_of']}/", week_body(w), 2))
        json.dump(w, open(f"{d}/data.json","w"), indent=1)
        urls.append(f"/weeks/{w['week_of']}/")
    cur = weeks[-1]
    open(f"{DOCS}/index.html","w").write(page(f"{SITE_NAME} — Earnings This Week & Expected Moves",
        f"Free weekly earnings calendar: this week's notable reports, before/after market timing and options-implied expected moves.",
        "/", week_body(cur).replace('href="data.json"', f'href="weeks/{cur["week_of"]}/data.json"'), 0))
    os.makedirs(f"{DOCS}/archive")
    items = "".join(f"<li><a href='../weeks/{w['week_of']}/index.html'>Week of {nice(w['week_of'])}</a> — {len(w['rows'])} companies</li>" for w in reversed(weeks))
    open(f"{DOCS}/archive/index.html","w").write(page(f"Archive | {SITE_NAME}", "Past weekly earnings cheat sheets with expected moves.", "/archive/", f"<h2>Archive</h2><ul>{items}</ul>", 1))
    os.makedirs(f"{DOCS}/about")
    about = f"<h2>Method &amp; disclaimer</h2><p>{e(cur['method'])}</p><p>Source: Robinhood market data (earnings calendar, stock quotes, option chains and quotes). Data may be delayed; dates may change. Tickers without a usable option chain are skipped.</p>{DISCLAIMER}"
    open(f"{DOCS}/about/index.html","w").write(page(f"Method & Disclaimer | {SITE_NAME}", "How expected moves are calculated, data sources and disclaimer.", "/about/", about, 1))
    urls += ["/archive/", "/about/"]
    open(f"{DOCS}/sitemap.xml","w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{SITE_URL}{u}</loc><lastmod>{cur['week_of'] if u=='/' else ''}</lastmod></url>\n".replace("<lastmod></lastmod>","") for u in urls) + "</urlset>\n")
    open(f"{DOCS}/robots.txt","w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n" if LICENSE_CLEARED else "User-agent: *\nDisallow: /\n")
    open(f"{DOCS}/.nojekyll","w").write("")
    # newsletter draft
    os.makedirs(f"{ROOT}/newsletter", exist_ok=True)
    rows = cur["rows"]
    top = sorted(rows, key=lambda r: -r["move_pct"])[:10]
    lines = [f"# Earnings Week Cheat Sheet — Week of {nice(cur['week_of'])}", "",
      "*DRAFT — not sent. Review before sending.*", "",
      f"{len(rows)} notable companies are scheduled to report this week. Below: report timing and the options-implied expected move.", "",
      "## Largest implied moves (%)", "", "| Ticker | Report | Timing | Exp. move |", "|---|---|---|---|"]
    lines += [f"| {r['symbol']} | {dow(r['report_date'])} | {r['timing']} | ±${r['move_usd']:,.2f} (±{r['move_pct']:.2f}%){' ⚑' if r['note'] else ''} |" for r in top]
    lines += ["", "## Full schedule", ""]
    for d in sorted({r["report_date"] for r in rows}):
        lines.append(f"**{dow(d)}**")
        for t in ("Before open", "After close", "Unconfirmed"):
            s = [f"{r['symbol']} (±{r['move_pct']:.1f}%)" for r in rows if r["report_date"]==d and r["timing"]==t]
            if s: lines.append(f"- {t}: " + ", ".join(s))
        lines.append("")
    lines += ["⚑ No weekly expiration listed; nearest monthly used, so the figure likely overstates the earnings-only move.", "",
      f"Full sortable table: {SITE_URL}/weeks/{cur['week_of']}/", "",
      f"Source: {cur['source']}, retrieved {cur['retrieved']}. Data may be delayed. {cur['method']}", "",
      *([] if LICENSE_CLEARED else ["> HOLD: do not send until data-source permission is confirmed (see MAINTENANCE.md).", ""]),
      "<!-- SPONSOR SLOT: intentionally empty -->", "",
      "*Not financial advice. Informational only; data may be delayed or inaccurate and earnings dates can change.*", "",
      f"Feedback: {FEEDBACK}"]
    open(f"{ROOT}/newsletter/week-{cur['week_of']}.md","w").write("\n".join(lines)+"\n")
    print(f"Built {len(weeks)} week(s) into {DOCS}")

if __name__ == "__main__":
    main()
