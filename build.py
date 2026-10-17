#!/usr/bin/env python3
"""Build static site into docs/ from data/week-*.json. Usage: python3 build.py"""
import glob, json, os, html, shutil
from datetime import date, timedelta

SITE_URL = os.environ.get("BASE", "https://jgonthego.github.io/ec-p33gfgvf8bazdl").rstrip("/")
SITE_NAME = "Earnings Week Cheat Sheet"
FORM_ID = os.environ.get("FORM_ID", "").strip()  # newsletter flag: signup hidden until a real Formspree ID is set
FORMSPREE = f"https://formspree.io/f/{FORM_ID}"
SHOW_FORM = bool(FORM_ID) and FORM_ID != "YOUR_FORM_ID"
FEEDBACK = "d.bot@mail.grokbot.com"
# Publication gate: the site owner chose to publish the Robinhood market data and accepts the terms risk
# (decision of Oct 15, 2026). True = indexable pages, robots Allow, no preview banner.
LICENSE_CLEARED = True
# Hidden site (owner decision, Oct 17, 2026): noindex/nofollow/noarchive on every page, robots.txt Disallow, no sitemap, no canonical.
HIDDEN = True
ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")
e = html.escape

CSS = """:root{--bg:#f6f7fb;--fg:#0f172a;--muted:#5b6475;--card:#fff;--line:#e4e7ef;--acc:#4f46e5;--acc2:#06b6d4;--bmo:#f59e0b;--amc:#6366f1;--warn-bg:#fff7e6;--warn-line:#f3c98b;--flag:#b45309;--shadow:0 1px 2px rgba(15,23,42,.06),0 4px 16px rgba(15,23,42,.06)}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0b1020;--fg:#e6e9f2;--muted:#9aa3b8;--card:#131a2e;--line:#232c45;--acc:#818cf8;--acc2:#22d3ee;--warn-bg:#2a2110;--warn-line:#6b4f1d;--flag:#fbbf24;--shadow:0 1px 2px rgba(0,0,0,.4)}}
:root[data-theme=dark]{--bg:#0b1020;--fg:#e6e9f2;--muted:#9aa3b8;--card:#131a2e;--line:#232c45;--acc:#818cf8;--acc2:#22d3ee;--warn-bg:#2a2110;--warn-line:#6b4f1d;--flag:#fbbf24;--shadow:0 1px 2px rgba(0,0,0,.4)}
*{box-sizing:border-box}body{font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:var(--fg);background:var(--bg);line-height:1.5}
.wrap{max-width:1140px;margin:0 auto;padding:0 18px}a{color:var(--acc)}
.top{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 85%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.top .wrap{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding-top:10px;padding-bottom:10px}
.brand{font-weight:800;font-size:18px;color:var(--fg);text-decoration:none;display:flex;align-items:center;gap:8px}
.logo{width:26px;height:26px;border-radius:7px;background:linear-gradient(135deg,var(--acc),var(--acc2));display:inline-block}
nav{display:flex;gap:4px;margin-left:auto;flex-wrap:wrap}nav a{color:var(--muted);text-decoration:none;padding:6px 10px;border-radius:8px;font-size:14px}nav a:hover{background:var(--card);color:var(--fg)}
#theme{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:8px;padding:5px 9px;cursor:pointer}
.hero{margin:22px 0 18px;padding:26px;border-radius:18px;color:#fff;background:linear-gradient(135deg,#4f46e5,#0891b2);box-shadow:var(--shadow)}
.hero h2,.hero h1{margin:0 0 6px;font-size:clamp(22px,4vw,32px)}.hero .small{color:#eef2ff;margin-top:6px}.hero p{margin:0;opacity:.9}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:18px}
.stat{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);border-radius:12px;padding:12px}.stat b{display:block;font-size:22px}.stat span{font-size:12px;opacity:.85}
.grid2{display:grid;grid-template-columns:3fr 2fr;gap:16px}@media(max-width:860px){.grid2{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:var(--shadow);margin-bottom:16px}
.card h3{margin:0 0 10px;font-size:16px}svg{display:block;width:100%;height:auto}svg text{fill:var(--fg);font-family:inherit}svg .mut{fill:var(--muted)}
.legend{font-size:12px;color:var(--muted);display:flex;gap:14px;flex-wrap:wrap;margin-top:6px}.sw{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.days{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}@media(max-width:900px){.days{grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}}
.day{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px;box-shadow:var(--shadow)}.day h4{margin:0 0 8px;display:flex;justify-content:space-between}.day h4 span{font-size:12px;color:var(--muted);font-weight:500}
.slot{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:8px 0 4px}
.chips{display:flex;flex-wrap:wrap;gap:5px}.chip{font-size:12px;padding:3px 7px;border-radius:999px;border:1px solid var(--line);background:var(--bg);white-space:nowrap}.chip i{font-style:normal;color:var(--muted);margin-left:3px}
.tw{overflow-x:auto;border-radius:14px;border:1px solid var(--line);box-shadow:var(--shadow)}
table{border-collapse:collapse;width:100%;background:var(--card);font-size:14px}th,td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left}
th{cursor:pointer;background:var(--card);position:sticky;top:0;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);white-space:nowrap}th:hover{color:var(--fg)}th::after{content:" ↕";opacity:.4}
tbody tr:hover{background:color-mix(in srgb,var(--acc) 6%,transparent)}td.n{text-align:right;font-variant-numeric:tabular-nums}
.bar{display:flex;align-items:center;gap:8px;justify-content:flex-end}.bar .t{height:6px;width:70px;background:var(--line);border-radius:3px;overflow:hidden}.bar .t i{display:block;height:100%;background:linear-gradient(90deg,var(--acc2),var(--acc))}
.pill{font-size:11px;padding:2px 8px;border-radius:999px;font-weight:600;white-space:nowrap}.bmo{background:color-mix(in srgb,var(--bmo) 20%,transparent);color:var(--flag)}.amc{background:color-mix(in srgb,var(--amc) 20%,transparent);color:var(--acc)}
.flag{color:var(--flag);font-size:12px}.disc{background:var(--warn-bg);border:1px solid var(--warn-line);padding:12px;border-radius:10px;font-size:14px}
.small{font-size:12px;color:var(--muted)}h2.sec{font-size:20px;margin:26px 0 12px}
footer{margin-top:30px;padding:20px 0 40px;border-top:1px solid var(--line)}
form{display:flex;gap:8px;flex-wrap:wrap}form input{padding:9px 12px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);min-width:240px}form button{padding:9px 16px;border:0;border-radius:8px;background:var(--acc);color:#fff;font-weight:600;cursor:pointer}
.ew{--c:#4f8dff;position:relative;color:#eef2ff;background:radial-gradient(120% 60% at 50% 0%,color-mix(in srgb,var(--c) 22%,#0a0d1c) 0%,#080b17 70%);border:1px solid color-mix(in srgb,var(--c) 70%,transparent);border-radius:18px;padding:18px;box-shadow:0 0 0 1px color-mix(in srgb,var(--c) 25%,transparent),0 0 28px color-mix(in srgb,var(--c) 35%,transparent),inset 0 0 30px color-mix(in srgb,var(--c) 10%,transparent);margin-bottom:16px}
.ew a{color:inherit}.ew-h{display:flex;gap:12px;align-items:center}.ew-n{margin:0;font-size:clamp(22px,4.4vw,32px);line-height:1.1;font-weight:900;letter-spacing:.01em;text-transform:uppercase;color:var(--c);text-shadow:0 0 14px color-mix(in srgb,var(--c) 70%,transparent)}
.ew-n small{font-size:.6em;color:#e6ebff;text-shadow:none}.ew-s{margin:2px 0 0;font-size:12px;color:#aab3cf}
.tk{--c:#4f8dff;flex:none;display:inline-grid;place-items:center;min-width:52px;height:52px;padding:0 6px;border-radius:13px;font-weight:900;font-size:15px;letter-spacing:.02em;color:#fff;background:linear-gradient(140deg,var(--c),color-mix(in srgb,var(--c) 45%,#000));box-shadow:0 0 14px color-mix(in srgb,var(--c) 55%,transparent);text-shadow:0 1px 2px rgba(0,0,0,.5)}
.tk.sm{min-width:40px;height:40px;font-size:12px;border-radius:10px}.tk.xs{min-width:0;width:100%;height:24px;font-size:9px;padding:0 2px;border-radius:6px;box-shadow:none}
.ew-when{text-align:center;margin:12px 0;font-size:15px;color:#d5dbf0}.ew-when b{color:#fff;letter-spacing:.03em}
.ew-box{background:rgba(255,255,255,.035);border:1px solid color-mix(in srgb,var(--c) 40%,rgba(255,255,255,.08));border-radius:14px;padding:12px 14px;margin-top:12px}
.ew-box h3{margin:0 0 6px;font-size:13px;text-transform:uppercase;letter-spacing:.08em;text-align:center;color:#e8ecff}
.ew-move{text-align:center}.ew-move .big{font-size:clamp(46px,11vw,72px);font-weight:900;line-height:1;color:var(--c);text-shadow:0 0 22px color-mix(in srgb,var(--c) 80%,transparent)}
.ew-move .usd{font-size:clamp(22px,5vw,30px);font-weight:800;margin:4px 0 6px}.ew-move p{margin:2px 0}.ew-move .ref span{color:#9aa4c4;font-size:12px}
.ew-note{font-size:11px;color:#9aa4c4;margin:8px 0 0;text-align:center}.ew-flag{font-size:12px;color:#fbbf24;margin:6px 0 0}.ew-na{color:#9aa4c4;text-align:center;margin:4px 0}
.q4{display:grid;grid-template-columns:repeat(4,1fr);gap:0}.q4 div{text-align:center;padding:4px 6px;border-left:1px solid rgba(255,255,255,.1)}.q4 div:first-child{border-left:0}
.q4 span{display:block;font-size:11px;color:#aab3cf}.q4 b{font-size:clamp(15px,3.6vw,19px)}.q4 b.na{color:#7f89a8;font-weight:600}
.ew-sub{margin:-2px 0 8px;text-align:center;font-size:12px;color:#aab3cf}.corr{list-style:none;margin:0;padding:0}
.corr li{display:grid;grid-template-columns:48px 58px 1fr 48px;align-items:center;gap:8px;padding:5px 0}.corr b{font-size:14px}.corr em{font-style:normal;font-weight:800;text-align:right;font-variant-numeric:tabular-nums}
.cb{height:12px;border-radius:6px;background:rgba(255,255,255,.07);overflow:hidden}.cb i{display:block;height:100%;border-radius:6px;background:linear-gradient(90deg,color-mix(in srgb,var(--c) 55%,#fff0),var(--c));box-shadow:0 0 10px var(--c)}
.etfp{margin:8px 0 0;text-align:center;font-size:12px;color:#d5dbf0;border:1px solid color-mix(in srgb,var(--c) 45%,transparent);border-radius:10px;padding:5px 8px}
.ew-f{margin-top:12px;font-size:11px;color:#9aa4c4;text-align:center}
.vs-t{text-align:center;font-weight:900;font-size:clamp(22px,4.5vw,40px);letter-spacing:.02em;margin:4px 0 12px}.vs-t i{font-style:normal;font-size:.55em;color:var(--muted)}.vs-t span{text-shadow:0 0 18px currentColor}
.vs-t small{display:block;font-size:12px;font-weight:600;color:var(--muted);letter-spacing:.08em;text-transform:uppercase}
.vs{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}@media(max-width:860px){.vs{grid-template-columns:1fr}}
.ew-one{max-width:620px;margin:0 auto}
.ewg{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px;margin-bottom:16px}
.ewc{--c:#4f8dff;display:block;text-decoration:none;color:#e9edff;background:linear-gradient(160deg,color-mix(in srgb,var(--c) 16%,#0a0d1c),#080b17 75%);border:1px solid color-mix(in srgb,var(--c) 55%,transparent);border-radius:14px;padding:12px;box-shadow:0 0 14px color-mix(in srgb,var(--c) 22%,transparent);transition:transform .12s,box-shadow .12s}
a.ewc:hover{transform:translateY(-2px);box-shadow:0 0 22px color-mix(in srgb,var(--c) 45%,transparent)}
.ewc-h{display:flex;gap:10px;align-items:center}.ewc-h b{display:block;font-size:14px;line-height:1.2}.ewc-h span{font-size:12px;color:#aab3cf}
.ewc-m{font-size:30px;font-weight:900;color:var(--c);text-shadow:0 0 12px color-mix(in srgb,var(--c) 70%,transparent);margin:8px 0 2px}.ewc-m small{font-size:14px;color:#e9edff;margin-left:8px;text-shadow:none;font-weight:700}
.ewc-l{font-size:12px;color:#c3cae2}
a.chip{text-decoration:none;color:var(--fg)}
.ew-act{text-align:center;margin:-4px 0 4px;font-size:12px;color:#c3cae2}.ew-act b{color:#fff}
.past{list-style:none;margin:0;padding:0}.past li{display:grid;grid-template-columns:118px 1fr 58px;gap:8px;align-items:center;padding:3px 0;font-size:13px}
.past li i{font-style:normal}.past li span i{font-size:10px;color:#9aa4c4;margin-left:3px}.past em{font-style:normal;font-weight:800;text-align:right;font-variant-numeric:tabular-nums}
.pb{height:10px;border-radius:5px;background:rgba(255,255,255,.07);overflow:hidden}.pb i{display:block;height:100%;border-radius:5px}
.pb i.up{background:#22c55e}.pb i.dn{background:#f43f5e}.pb i.im{background:var(--c);box-shadow:0 0 10px var(--c)}
.past li.impl{border-top:1px dashed rgba(255,255,255,.18);margin-top:4px;padding-top:6px}.past li.impl span:first-child{font-weight:700;color:#fff}
.verdict{margin-top:8px;text-align:center;border:1px solid color-mix(in srgb,var(--c) 50%,transparent);border-radius:10px;padding:6px 8px;font-size:14px}
.verdict b{font-size:18px;color:var(--c);margin-right:6px}.pre{text-align:center;font-size:13px;margin:8px 0 0;color:#d5dbf0}
b.up{color:#4ade80}b.dn{color:#fb7185}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:-4px 0 6px}.tabs button,.tabs a{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:6px 12px;font-size:13px;cursor:pointer;text-decoration:none}
.tabs button.on{background:var(--acc);border-color:var(--acc);color:#fff}
.ewc{position:relative}.rk{position:absolute;top:8px;right:10px;font-weight:900;font-size:13px;color:var(--c);text-shadow:0 0 8px var(--c)}
.ewg.big .ewc{padding:16px}.ewg.big .ewc-m{font-size:36px}
.sech{display:flex;align-items:baseline;gap:10px;margin:26px 0 10px}.sech h2{margin:0;font-size:20px}.sech span{color:var(--muted);font-size:13px}
@media(max-width:480px){.past li{grid-template-columns:96px 1fr 50px;font-size:12px}}td a{color:inherit;text-decoration:none}td a:hover{color:var(--acc)}
@media(max-width:480px){.ew{padding:14px}.q4{grid-template-columns:repeat(2,1fr);row-gap:8px}.q4 div:nth-child(3){border-left:0}.corr li{grid-template-columns:44px 54px 1fr 44px;gap:6px}}
@media(max-width:700px){.hide-sm{display:none}.hero{padding:18px}.bar .t{width:40px}th,td{padding:8px 6px}}"""

SORT_JS = """document.querySelectorAll('table.sortable th').forEach((th,i)=>{th.addEventListener('click',()=>{
const t=th.closest('table'),b=t.tBodies[0],rows=[...b.rows],asc=th.dataset.asc!=='1';th.dataset.asc=asc?'1':'0';
rows.sort((a,c)=>{const x=a.cells[i].dataset.v??a.cells[i].innerText,y=c.cells[i].dataset.v??c.cells[i].innerText;
const nx=parseFloat(x),ny=parseFloat(y);const r=(!isNaN(nx)&&!isNaN(ny))?nx-ny:x.localeCompare(y);return asc?r:-r});
rows.forEach(r=>b.appendChild(r))})});
document.querySelectorAll('.tabs button').forEach(b=>b.addEventListener('click',()=>{const g=document.getElementById('ewg');if(!g)return;
const k=b.dataset.sort;[...g.children].sort((x,y)=>(+x.dataset[k])-(+y.dataset[k])).forEach(c=>g.appendChild(c));
b.parentNode.querySelectorAll('button').forEach(o=>o.classList.toggle('on',o===b));g.classList.toggle('ranked',k==='rank')}));
(function(){const k='ewcs-theme',r=document.documentElement,b=document.getElementById('theme');let s=null;try{s=localStorage.getItem(k)}catch(_){}
if(s)r.dataset.theme=s;const dark=()=>r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
const lab=()=>{if(b)b.textContent=dark()?'☀':'☾'};lab();if(b)b.addEventListener('click',()=>{r.dataset.theme=dark()?'light':'dark';try{localStorage.setItem(k,r.dataset.theme)}catch(_){}lab()})})();"""


DISCLAIMER = ("<p class='disc'><strong>Not financial advice.</strong> This page is for informational purposes only and "
  "does not recommend buying or selling any security. Data may be delayed, incomplete, or inaccurate, and earnings dates can change. "
  "Options-implied moves are a market-derived estimate, not a forecast. Verify all information independently.</p>")

NEWS = f"""<section class="card"><h3>Get the weekly cheat sheet by email</h3>
<form action="{FORMSPREE}" method="POST"><label>Email <input type="email" name="email" required></label>
<button type="submit">Subscribe</button></form></section>"""

def page(title, desc, path, body, depth):
    rel = "../" * depth
    url = SITE_URL + path
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
{'<meta name="robots" content="noindex,nofollow,noarchive">' if HIDDEN or not LICENSE_CLEARED else ''}
{"" if HIDDEN else f'<link rel="canonical" href="{url}">'}
<meta property="og:type" content="website"><meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">{"" if HIDDEN else f'<meta property="og:url" content="{url}">'}
<meta name="twitter:card" content="summary">
<meta name="color-scheme" content="light dark"><style>{CSS}</style></head><body>
<header class="top"><div class="wrap"><a class="brand" href="{rel}index.html"><span class="logo" aria-hidden="true"></span>{SITE_NAME}</a>
<nav><a href="{rel}index.html">This week</a><a href="{rel}anticipated.html">Most anticipated</a><a href="{rel}sectors.html">By sector</a><a href="{rel}archive/index.html">Archive</a><a href="{rel}about/index.html">Method &amp; disclaimer</a></nav>
<button id="theme" type="button" aria-label="Toggle dark/light theme">☾</button></div></header><div class="wrap">
{"" if LICENSE_CLEARED else "<p class='disc'><strong>Internal preview — not for publication.</strong> Data-source terms do not yet permit public display.</p>"}
<main>{body}</main>
<footer>
<!-- SPONSOR SLOT: intentionally empty. Replace with a real, clearly labeled sponsor only. -->
<p class="small" style="text-align:right"><a href="mailto:{FEEDBACK}?subject=Sponsor%20Earnings%20Cheat%20Sheet">Advertise / sponsor this page</a></p>
{NEWS if SHOW_FORM else "<!-- NEWSLETTER HOOK: set FORM_ID env var to enable signup -->"}
<p class="small">Feedback or corrections: <a href="mailto:{FEEDBACK}?subject=Earnings%20Cheat%20Sheet%20feedback">{FEEDBACK}</a></p>
{DISCLAIMER}</footer></div><script>{SORT_JS}</script></body></html>"""

def nice(d): return date.fromisoformat(d).strftime("%b %-d, %Y")
def dow(d): return date.fromisoformat(d).strftime("%a %b %-d")

TCLS = {"Before open": "bmo", "After close": "amc"}

def svg_movers(rows, n=15):
    top = sorted(rows, key=lambda r: -r["move_pct"])[:n]
    mx = max(r["move_pct"] for r in top) or 1
    rh, lw, W = 26, 64, 640
    h = rh * len(top) + 10
    out = [f"<svg viewBox='0 0 {W} {h}' role='img' aria-label='Top {len(top)} expected moves by ticker'>",
           "<defs><linearGradient id='g1' x1='0' x2='1'><stop offset='0' stop-color='#06b6d4'/><stop offset='1' stop-color='#6366f1'/></linearGradient></defs>"]
    for i, r in enumerate(top):
        y = 5 + i * rh; bw = (W - lw - 90) * r["move_pct"] / mx
        fl = " ⚑" if r["note"] else ""
        out.append(f"<text x='0' y='{y+17}' font-size='13' font-weight='700'>{e(r['symbol'])}</text>"
                   f"<rect x='{lw}' y='{y+4}' width='{bw:.1f}' height='16' rx='5' fill='url(#g1)'><title>{e(r['name'])}: ±{r['move_pct']:.2f}% (±${r['move_usd']:,.2f}){fl}</title></rect>"
                   f"<text x='{lw+bw+6:.1f}' y='{y+17}' font-size='12' class='mut'>±{r['move_pct']:.2f}%{fl}</text>")
    out.append("</svg>")
    return "".join(out)

def svg_days(rows):
    days = sorted({r["report_date"] for r in rows})
    cnt = {d: {t: sum(1 for r in rows if r["report_date"] == d and r["timing"] == t) for t in ("Before open", "After close", "Unconfirmed")} for d in days}
    mx = max(sum(c.values()) for c in cnt.values()) or 1
    W, H, base = 400, 230, 195
    cw = W / len(days); bw = min(46, cw * .55)
    out = [f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='Report counts by day'>"]
    for i, d in enumerate(days):
        x = i * cw + (cw - bw) / 2; y = base
        for t, col in (("Before open", "#f59e0b"), ("After close", "#6366f1"), ("Unconfirmed", "#94a3b8")):
            v = cnt[d][t]
            if not v: continue
            hh = (base - 30) * v / mx; y -= hh
            out.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{bw:.1f}' height='{hh:.1f}' rx='4' fill='{col}'><title>{dow(d)} {t}: {v}</title></rect>")
        tot = sum(cnt[d].values())
        out.append(f"<text x='{x+bw/2:.1f}' y='{y-6:.1f}' font-size='13' font-weight='700' text-anchor='middle'>{tot}</text>"
                   f"<text x='{x+bw/2:.1f}' y='{base+20}' font-size='12' text-anchor='middle' class='mut'>{date.fromisoformat(d).strftime('%a %-d')}</text>")
    out.append("</svg>")
    leg = "<div class='legend'><span><i class='sw' style='background:#f59e0b'></i>Before open</span><span><i class='sw' style='background:#6366f1'></i>After close</span>"
    if any(c["Unconfirmed"] for c in cnt.values()): leg += "<span><i class='sw' style='background:#94a3b8'></i>Unconfirmed</span>"
    return "".join(out) + leg + "</div>"

def calendar(w):
    rows = w["rows"]; start = date.fromisoformat(w["week_of"]); cards = []
    for k in range(5):
        d = (start + timedelta(days=k)).isoformat(); dr = [r for r in rows if r["report_date"] == d]
        body = ""
        for t in ("Before open", "After close", "Unconfirmed"):
            s = sorted((r for r in dr if r["timing"] == t), key=lambda r: -r["move_pct"])
            if s:
                body += f"<div class='slot'>{t}</div><div class='chips'>" + "".join(
                    f"<span class='chip' title='{e(r['name'])}'><b>{e(r['symbol'])}</b><i>±{r['move_pct']:.1f}%{' ⚑' if r['note'] else ''}</i></span>" for r in s) + "</div>"
        cards.append(f"<div class='day'><h4>{dow(d)}<span>{len(dr)} report{'s' if len(dr)!=1 else ''}</span></h4>{body or '<p class=small>No selected reports.</p>'}</div>")
    return "<div class='days'>" + "".join(cards) + "</div>"

# ---------- earnings-watch cards ----------
BRAND = {"NFLX":"#ff2a3d","TSLA":"#ff3344","META":"#2f7bff","SPOT":"#1ed760","T":"#19b5fe","IBM":"#4f8dff","GM":"#4d8bff",
         "AAL":"#9aa9c0","UAL":"#4a7dff","LUV":"#ffbf00","COF":"#e0393e","AXP":"#3c8cff","PG":"#3d7bff","GE":"#5aa0ff",
         "CMCSA":"#a06bff","NEE":"#2fd38a","TXN":"#ff3b3b","LMT":"#5b8cff","NEM":"#ffc23d","PM":"#c9a24b","VLO":"#3fa9f5"}
NEON = ["#ff3d7f","#36c5ff","#a46bff","#2ee6a6","#ffb020","#ff6b3d","#4d8bff","#e04dff","#26d9d9","#9bff3d"]
def bcolor(s): return BRAND.get(s) or NEON[sum(map(ord, s)) % len(NEON)]
def money(v, sign=False):
    if v is None: return "n/a"
    a = abs(v); neg = "-" if v < 0 else ""
    for d, u in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if a >= d: return f"{neg}${a/d:,.2f}{u}"
    return f"{neg}${a:,.0f}"
def eps_s(v): return "n/a" if v is None else (f"-${abs(v):,.2f}" if v < 0 else f"${v:,.2f}")
def pct_s(v): return "n/a" if v is None else f"{v:.1f}%"
def r_s(r): return f"{'+' if r > 0 else ('−' if r < 0 else '')}{abs(r):.2f}"
def shortd(d): return date.fromisoformat(d).strftime("%b %-d") if d else ""
def when(r): return f"{date.fromisoformat(r['report_date']).strftime('%a %b %-d')} · {r['timing']}"
def tbadge(s, cls="tk"): return f"<span class='{cls}' style='--c:{bcolor(s)}' aria-hidden='true'>{e(s)}</span>"

def quarter_block(r):
    f = r.get("fundamentals")
    if not f: return "<section class='ew-box'><h3>Latest quarter</h3><p class='ew-na'>n/a — no Robinhood fundamentals for this ticker.</p></section>"
    per, eper = f.get("period"), f.get("eps_period")
    same = per and eper and per.replace("FQ", "Q") == eper
    head = per or (f"EPS {eper}" if eper else "")
    end = f" · ended {nice(f['period_end'])}" if f.get("period_end") else ""
    cells = [("Revenue", money(f.get("revenue"))), ("Net income", money(f.get("net_income"))),
             ("Net margin", pct_s(f.get("net_margin"))),
             ("EPS" + ("" if same or not eper else f" ({eper})"), eps_s(f.get("eps")))]
    cell = "".join(f"<div><span>{e(k)}</span><b class='{'na' if v=='n/a' else ''}'>{e(v)}</b></div>" for k, v in cells)
    return (f"<section class='ew-box'><h3>Latest quarter ({e(head)})</h3><div class='q4'>{cell}</div>"
            f"<p class='ew-note'>Revenue / net income / net margin: Robinhood quarterly financials{e(end)}. "
            f"EPS: Robinhood earnings results 'actual'{(' (reported ' + nice(f['eps_report_date']) + ')') if f.get('eps_report_date') else ''}; may be adjusted (non-GAAP).</p></section>")

def corr_block(r, n=4):
    c = r.get("correlations")
    if not c or not (c["stocks"] or c["etfs"]):
        return "<section class='ew-box'><h3>Correlated stocks</h3><p class='ew-na'>n/a — not enough price history.</p></section>"
    rows = "".join(f"<li>{tbadge(x['symbol'],'tk xs')}<b>{e(x['symbol'])}</b><span class='cb'><i style='width:{max(x['r'],0)*100:.0f}%'></i></span><em>{r_s(x['r'])}</em></li>"
                   for x in c["stocks"][:n]) or "<li class='ew-na'>No stock peers with full history.</li>"
    etf = (" · ".join(f"{e(x['symbol'])} {r_s(x['r'])}" for x in c["etfs"])) if c["etfs"] else ""
    return (f"<section class='ew-box'><h3>Correlated stocks</h3><p class='ew-sub'>{c['n_returns']} daily returns · {shortd(c['start'])} – {nice(c['end'])}</p>"
            f"<ul class='corr'>{rows}</ul>{f'<p class=etfp>ETF proxies: {etf}</p>' if etf else ''}"
            f"<p class='ew-note'>Pearson correlation of daily close-to-close returns vs. {c['candidates']} hand-picked same-sector candidates. Not causation.</p></section>")

def big_num(v):
    if v is None: return "n/a"
    return f"{v/1e6:.2f}M" if v >= 1e6 else (f"{v/1e3:.0f}K" if v >= 1e3 else f"{v:,.0f}")
def sgn(v): return "n/a" if v is None else f"{'+' if v > 0 else ('−' if v < 0 else '')}{abs(v):.1f}%"

def past_block(r):
    p = r.get("past_moves")
    if not p: return "<section class='ew-box'><h3>Implied vs. past earnings moves</h3><p class='ew-na'>n/a — no Robinhood earnings history or price data.</p></section>"
    mv = p.get("moves") or []
    mx = max([abs(m["move_pct"]) for m in mv] + [r["move_pct"]]) or 1
    rows = "".join(f"<li><span>{e(date.fromisoformat(m['report_date']).strftime('%b %-d, %Y'))} <i>{'BMO' if m['timing']=='am' else 'AMC'}</i></span>"
                   f"<span class='pb'><i class='{'up' if m['move_pct']>=0 else 'dn'}' style='width:{abs(m['move_pct'])/mx*100:.0f}%'></i></span><em>{sgn(m['move_pct'])}</em></li>" for m in reversed(mv))
    rows += f"<li class='impl'><span>This week (implied)</span><span class='pb'><i class='im' style='width:{r['move_pct']/mx*100:.0f}%'></i></span><em>±{r['move_pct']:.1f}%</em></li>"
    ratio = p.get("ratio")
    verdict = (f"<div class='verdict'><b>{ratio:.2f}×</b> {e(p['label'])}</div>" if ratio is not None else "<div class='verdict'><b>n/a</b> Not enough past reports for a comparison</div>")
    caveat = "<p class='ew-flag'>⚑ Monthly expiry used, so the implied figure includes extra non-earnings time value and overstates the comparison.</p>" if r["note"] else ""
    pre = p.get("pre_change")
    pre_s = (f"<p class='pre'>Stock change, last {pre['sessions']} sessions ({shortd(pre['start'])} – {nice(pre['end'])} close): <b class='{'up' if pre['change_pct']>=0 else 'dn'}'>{sgn(pre['change_pct'])}</b></p>"
             if pre else "<p class='pre'>30-session change: n/a</p>")
    avg = f"±{p['avg_abs']:.1f}%" if p.get("avg_abs") is not None else "n/a"
    return (f"<section class='ew-box'><h3>Implied vs. past earnings moves</h3><p class='ew-sub'>Last {len(mv)} reports · close before → close after · avg absolute move <b>{avg}</b></p>"
            f"<ul class='past'>{rows}</ul>{verdict}{caveat}{pre_s}"
            "<p class='ew-note'>Past moves: Robinhood earnings dates/timing + daily closes. Ratio = implied ÷ average absolute past move. Non-directional; not a prediction or advice.</p></section>")

def act_line(r):
    a = r.get("options_activity") or {}
    if not a.get("total"): return "<p class='ew-act'>Options activity: n/a</p>"
    return (f"<p class='ew-act'>Most-anticipated rank <b>#{r['anticipated_rank']}</b> · options OI {big_num(a['open_interest'])} + volume {big_num(a['volume'])} = "
            f"<b>{big_num(a['total'])}</b> contracts</p>")

def big_card(r, w, h="h2"):
    p = r.get("profile") or {}
    sub = " · ".join(x for x in (p.get("sector"), p.get("industry")) if x)
    lo, hi = r["price"] - r["move_usd"], r["price"] + r["move_usd"]
    flag = f"<p class='ew-flag'>⚑ {e(r['note'])}</p>" if r["note"] else ""
    return f"""<article class="ew" style="--c:{bcolor(r['symbol'])}">
<header class="ew-h">{tbadge(r['symbol'])}<div><{h} class="ew-n">{e(r['name'])} <small>({e(r['symbol'])})</small></{h}>{f'<p class=ew-s>{e(sub)}</p>' if sub else ''}</div></header>
<p class="ew-when">Earnings: <b>{e(when(r).upper())}</b></p>{act_line(r)}
<section class="ew-box ew-move"><h3>Option-implied price move</h3><div class="big">±{r['move_pct']:.1f}%</div><div class="usd">±${r['move_usd']:,.2f}</div>
<p>Implied range: <b>${lo:,.2f} – ${hi:,.2f}</b></p><p class="ref">Reference stock price: ${r['price']:,.2f} <span>(last trade {e(r['price_ts'])})</span></p>
<p class="ew-note">ATM straddle, {e(r['expiration'])} expiry @ {r['strike']:g}; option quotes {e(r['quote_ts'])}. Non-directional.</p>{flag}</section>
{past_block(r)}{quarter_block(r)}{corr_block(r)}
<footer class="ew-f">Source: {e(w['source'])}, retrieved {e(w['retrieved'])}. Implied moves are non-directional estimates, not forecasts. Correlation is not earnings-event causation.</footer></article>"""

def mini_card(r, href, show_rank=False):
    f = r.get("fundamentals") or {}; c = r.get("correlations") or {}
    lo, hi = r["price"] - r["move_usd"], r["price"] + r["move_usd"]
    per, eper = f.get("period"), f.get("eps_period")
    rev = f"Rev {money(f['revenue'])}" if f.get("revenue") is not None else ""
    ep = f"EPS {eps_s(f['eps'])}" if f.get("eps") is not None else ""
    if rev and ep and per and eper and per.replace("FQ", "Q") != eper: rev, ep = f"{rev} ({per})", f"{ep} ({eper})"
    lab = (per if rev else eper) if (rev or ep) else ""
    q = (f"{lab}: " if lab and "(" not in rev else "") + " · ".join(x for x in (rev, ep) if x) if (rev or ep) else "Latest quarter n/a"
    top = c.get("stocks") or c.get("etfs") or []
    tc = f"Top corr: {e(top[0]['symbol'])} {r_s(top[0]['r'])}" if top else "Correlation n/a"
    a = r.get("options_activity") or {}; pm = r.get("past_moves") or {}
    rk = (f"<span class='rk'>#{r['anticipated_rank']}</span>" if show_rank and r.get("anticipated_rank") else "")
    al = f"<div class='ewc-l'>Options activity {big_num(a.get('total'))}{' · #' + str(r['anticipated_rank']) if r.get('anticipated_rank') else ''}</div>"
    pl = f"<div class='ewc-l'>Implied vs. past avg: {pm['ratio']:.2f}×</div>" if pm.get("ratio") is not None else ""
    inner = rk + (f"<div class='ewc-h'>{tbadge(r['symbol'],'tk sm')}<div><b>{e(r['name'])}</b><span>{e(when(r))}</span></div></div>"
             f"<div class='ewc-m'>±{r['move_pct']:.1f}%<small>±${r['move_usd']:,.2f}{' ⚑' if r['note'] else ''}</small></div>"
             f"<div class='ewc-l'>Range ${lo:,.2f} – ${hi:,.2f}</div><div class='ewc-l'>{e(q)}</div><div class='ewc-l'>{tc}</div>{al}{pl}")
    da = f"data-i='{r.get('_i',0)}' data-rank='{r.get('anticipated_rank') or 999}'"
    return (f"<a class='ewc' {da} style='--c:{bcolor(r['symbol'])}' href='{href}'>{inner}</a>" if href
            else f"<div class='ewc' {da} style='--c:{bcolor(r['symbol'])}'>{inner}</div>")

def has_cards(w): return any("fundamentals" in r or "correlations" in r for r in w["rows"])

def cards_section(w, tref):
    """tref: relative prefix to docs/t/ or None (older weeks: no ticker pages)."""
    if not has_cards(w): return ""
    by = {r["symbol"]: r for r in w["rows"]}
    feat = [by[s] for s in w.get("featured", []) if s in by][:2]
    out = ""
    if len(feat) == 2:
        a, b = feat
        out += (f"<h2 class='sec'>Featured matchup</h2><div class='vs-t'><span style='color:{bcolor(a['symbol'])}'>{e(a['name'].upper())}</span> <i>vs</i> "
                f"<span style='color:{bcolor(b['symbol'])}'>{e(b['name'].upper())}</span><small>Earnings watch · {e(w.get('featured_basis',''))}</small></div>"
                f"<div class='vs'>{big_card(a, w, 'h3')}{big_card(b, w, 'h3')}</div>")
    for i, r in enumerate(w["rows"]): r["_i"] = i
    root = tref[:-2] if tref else None   # "t/" -> "", "../../t/" -> "../../"
    tabs = ""
    if tref and any(r.get("anticipated_rank") for r in w["rows"]):
        tabs = ("<div class='tabs' role='group' aria-label='Sort cards'><button type='button' class='on' data-sort='i'>Report date</button>"
                "<button type='button' data-sort='rank'>Most anticipated</button>"
                f"<a href='{root}anticipated.html'>Ranked page →</a><a href='{root}sectors.html'>By sector →</a></div>")
    out += ("<h2 class='sec'>Earnings watch cards</h2>" + tabs + "<p class='small'>One card per company. "
            + ("Tap a card for the full view with past earnings moves, latest-quarter figures and correlated stocks." if tref else "") + "</p>"
            + "<div class='ewg' id='ewg'>" + "".join(mini_card(r, f"{tref}{r['symbol']}.html" if tref else None) for r in w["rows"]) + "</div>")
    return out

def ticker_body(r, w):
    same = [x for x in w["rows"] if x["report_date"] == r["report_date"] and x["symbol"] != r["symbol"]]
    chips = "".join(f"<a class='chip' href='{e(x['symbol'])}.html'><b>{e(x['symbol'])}</b><i>±{x['move_pct']:.1f}%</i></a>" for x in same)
    return (f"<p class='small' style='margin-top:18px'><a href='../index.html'>← All reporters, week of {nice(w['week_of'])}</a></p>"
            f"<div class='ew-one'>{big_card(r, w, 'h1')}</div>"
            f"<div class='card'><h3>Also reporting {e(dow(r['report_date']))}</h3><div class='chips'>{chips or '<span class=small>None among the selected tickers.</span>'}</div></div>"
            f"<div class='card'><h3>Method</h3><p class='small'>{e(w['method'])}</p><p class='small'>{e(w.get('cards_method',''))}</p>"
            f"<p class='small'>n/a = not available from Robinhood for this ticker; nothing is estimated or filled in.</p></div>")

def _ensure_i(w):
    for i, r in enumerate(w["rows"]): r.setdefault("_i", i)

def anticipated_body(w):
    _ensure_i(w)
    rk = [r for r in w["rows"] if r.get("anticipated_rank")]
    if not rk:
        return "<div class='card'><h2>Most anticipated</h2><p>n/a — options-activity data was not available this week, so no ranking is shown.</p></div>"
    rk.sort(key=lambda r: r["anticipated_rank"])
    top, rest = rk[:15], rk[15:]
    miss = [r["symbol"] for r in w["rows"] if not (r.get("options_activity") or {}).get("total")]
    return (f"<div class='hero'><h1>Most anticipated earnings — week of {nice(w['week_of'])}</h1>"
            f"<p class='small'><b>How it is ranked:</b> {e(w.get('anticipated_method',''))}</p>"
            + (f"<p class='small'>No options-activity data: {e(', '.join(miss))} (listed last).</p>" if miss else "") + "</div>"
            "<h2 class='sec'>Top 15</h2><div class='ewg big'>" + "".join(mini_card(r, f"t/{r['symbol']}.html", True) for r in top) + "</div>"
            + (f"<h2 class='sec'>The rest ({len(rest)})</h2><div class='ewg'>" + "".join(mini_card(r, f"t/{r['symbol']}.html", True) for r in rest) + "</div>" if rest else "")
            + f"<p class='small'>Options activity counts contracts across all listed expirations, not only the earnings expiry. It reflects how actively a stock's options trade overall — large, popular stocks rank high every week. Not advice.</p>")

def _median(v):
    v = sorted(v); n = len(v)
    return None if not n else (v[n//2] if n % 2 else (v[n//2-1] + v[n//2]) / 2)

def sector_svg(groups):
    rowh, lw, bw, W = 30, 190, 300, 600
    mc = max(len(g) for _, g in groups)
    H = rowh * len(groups) + 34
    out = [f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='Reporters per sector and median implied move'>",
           f"<text x='{lw+6}' y='16' class='mut' font-size='11'>Companies reporting</text><text x='{W-4}' y='16' text-anchor='end' class='mut' font-size='11'>Median implied move</text>"]
    for i, (sec, g) in enumerate(groups):
        y = 28 + i * rowh; w_ = max(4, len(g) / mc * bw); med = _median([r["move_pct"] for r in g])
        out.append(f"<text x='{lw}' y='{y+15}' text-anchor='end' font-size='12'>{e(sec)}</text>"
                   f"<rect x='{lw+6}' y='{y+3}' width='{w_:.0f}' height='16' rx='4' fill='var(--acc)'/>"
                   f"<text x='{lw+12+w_:.0f}' y='{y+15}' font-size='12' font-weight='700'>{len(g)}</text>"
                   f"<text x='{W-4}' y='{y+15}' text-anchor='end' font-size='12' font-weight='700'>±{med:.1f}%</text>")
    return "".join(out) + "</svg>"

def sectors_body(w):
    _ensure_i(w)
    g = {}
    for r in w["rows"]: g.setdefault((r.get("profile") or {}).get("sector") or "Sector n/a", []).append(r)
    key = lambda r: (r.get("anticipated_rank") or 999, -r["move_pct"])
    groups = sorted(((k, sorted(v, key=key)) for k, v in g.items()), key=lambda kv: (kv[0] == "Sector n/a", -len(kv[1]), kv[0]))
    nav = "".join(f"<a class='chip' href='#s{i}'><b>{e(k)}</b><i>{len(v)}</i></a>" for i, (k, v) in enumerate(groups))
    secs = "".join(f"<div class='sech' id='s{i}'><h2>{e(k)}</h2><span>{len(v)} {'company' if len(v)==1 else 'companies'} · median implied move ±{_median([r['move_pct'] for r in v]):.1f}%</span></div>"
                   "<div class='ewg'>" + "".join(mini_card(r, f"t/{r['symbol']}.html", True) for r in v) + "</div>" for i, (k, v) in enumerate(groups))
    return (f"<div class='hero'><h1>Earnings by sector — week of {nice(w['week_of'])}</h1>"
            f"<p class='small'>{len(w['rows'])} companies grouped by Robinhood's sector classification. Within each sector, cards are ordered by most-anticipated rank (options activity; #n on each card).</p></div>"
            f"<div class='card'><h3>Sector summary</h3>{sector_svg(groups)}</div><div class='chips'>{nav}</div>{secs}")

def week_body(w, tref=None):
    rs = w["rows"]
    mx = max((r["move_pct"] for r in rs), default=1) or 1
    rows = []
    link = bool(tref) and has_cards(w)
    for r in rs:
        flag = f"<div class='flag'>⚑ {e(r['note'])}</div>" if r["note"] else ""
        tk = f"<a href='{tref}{r['symbol']}.html'>{r['symbol']}</a>" if link else r["symbol"]
        rows.append(f"<tr><td><strong>{tk}</strong>{' <span class=flag>⚑</span>' if r['note'] else ''}</td><td class='hide-sm'>{e(r['name'])}</td>"
          f"<td data-v='{r['report_date']}{'0' if r['timing']=='Before open' else '1'}'>{dow(r['report_date'])}</td><td><span class='pill {TCLS.get(r['timing'],'')}'>{r['timing']}</span></td>"
          f"<td class='n' data-v='{r['price']}'>${r['price']:,.2f}</td>"
          f"<td class='n' data-v='{r['move_usd']}'>±${r['move_usd']:,.2f}</td><td class='n' data-v='{r['move_pct']}'><div class='bar'><span class='t'><i style='width:{100*r['move_pct']/mx:.0f}%'></i></span>±{r['move_pct']:.2f}%</div></td>"
          f"<td class='hide-sm'>{r['expiration']} @ {r['strike']:g}{flag}</td><td class='small hide-sm'>{r['quote_ts']}</td></tr>")
    gaps = "".join(f"<li>{g['symbol']}: {e(g['reason'])}</li>" for g in w["gaps"]) or "<li>None among the selected tickers.</li>"
    if w.get("excluded"):
        gaps += ("<li>US-domiciled companies only. Excluded foreign issuers: "
                 + "; ".join(f"{e(x['symbol'])} ({e(x['reason'].split(': ',1)[-1].replace(' (Robinhood company profile)',''))})" for x in w["excluded"])
                 + " — per Robinhood company profiles.</li>")
    end = (date.fromisoformat(w["week_of"]) + timedelta(days=4)).isoformat()
    stats = ""
    if rs:
        big = max(rs, key=lambda r: r["move_pct"])
        pcts = sorted(r["move_pct"] for r in rs); n = len(pcts)
        med = pcts[n//2] if n % 2 else (pcts[n//2-1] + pcts[n//2]) / 2
        busy = max(sorted({r["report_date"] for r in rs}), key=lambda d: sum(1 for r in rs if r["report_date"] == d))
        bc = sum(1 for r in rs if r["report_date"] == busy)
        stats = (f"<div class='stats'><div class='stat'><b>{n}</b><span>companies reporting</span></div>"
          f"<div class='stat'><b>{big['symbol']} ±{big['move_pct']:.2f}%</b><span>largest implied move</span></div>"
          f"<div class='stat'><b>±{med:.2f}%</b><span>median implied move</span></div>"
          f"<div class='stat'><b>{dow(busy)}</b><span>busiest day · {bc} reports</span></div></div>")
    return f"""<section class="hero"><h2>Earnings week of {nice(w['week_of'])} – {nice(end)}</h2>
<p>{len(rs)} notable companies scheduled to report, with the options-implied expected move.</p>{stats}</section>
<p class="disc"><strong>Delayed data.</strong> Prices and option quotes may be delayed and are snapshots as of the quote time in each row; they will change before the reports.</p>
<p class="small"><strong>Source: {w['source']}, retrieved {w['retrieved']}.</strong> Stock prices are last regular-session trades ({e(rs[0]['price_ts'] if rs else '')}); option bid/ask times are shown per row. Selection: {e(w['selection'])}</p>
<div class="grid2"><div class="card"><h3>Top {min(15,len(rs))} expected moves (%)</h3>{svg_movers(rs) if rs else ''}<p class="small">⚑ = monthly expiry used; likely overstates the earnings-only move.</p></div>
<div class="card"><h3>Reports by day</h3>{svg_days(rs) if rs else ''}</div></div>
{cards_section(w, tref)}
<h2 class="sec">Calendar</h2>{calendar(w)}
<h2 class="sec">Full table</h2><p class="small">Click any column header to sort (e.g. by date or expected move %).</p>
<div class="tw"><table class="sortable"><thead><tr><th>Ticker</th><th class='hide-sm'>Company</th><th>Report date</th><th>Timing</th><th>Price</th><th>Exp. move $</th><th>Exp. move %</th><th class='hide-sm'>Expiry @ ATM strike</th><th class='hide-sm'>Quote time</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p class="small">Method: {e(w['method'])} ⚑ = no weekly expiration was listed, so the nearest monthly was used and the figure likely overstates the earnings-only move.</p>
<div class="card"><h3>Data notes</h3><ul>{''.join(f'<li>{e(c)}</li>' for c in w.get('calendar_notes',[]))}{gaps}</ul>
<p class="small">Raw data: <a href="data.json">data.json</a></p>{f'<p class="small">{e(w["cards_method"])}</p>' if w.get("cards_method") else ''}</div>"""

def main():
    weeks = sorted((json.load(open(f)) for f in glob.glob(f"{ROOT}/data/week-*.json")), key=lambda w: w["week_of"])
    if os.path.isdir(DOCS): shutil.rmtree(DOCS)
    os.makedirs(DOCS)
    urls = ["/"]
    for w in weeks:
        d = os.path.join(DOCS, "weeks", w["week_of"]); os.makedirs(d)
        t = f"Earnings Week of {nice(w['week_of'])}: Dates, Timing & Expected Moves | {SITE_NAME}"
        desc = f"{len(w['rows'])} earnings reports for the week of {nice(w['week_of'])} with report timing and options-implied expected moves. Free, updated weekly."
        cur_w = w is weeks[-1]
        open(f"{d}/index.html","w").write(page(t, desc, f"/weeks/{w['week_of']}/", week_body(w, "../../t/" if cur_w else None), 2))
        json.dump(w, open(f"{d}/data.json","w"), indent=1)
        urls.append(f"/weeks/{w['week_of']}/")
    cur = weeks[-1]
    open(f"{DOCS}/index.html","w").write(page(f"{SITE_NAME} — Earnings This Week & Expected Moves",
        f"Free weekly earnings calendar: this week's notable reports, before/after market timing and options-implied expected moves.",
        "/", week_body(cur, "t/").replace('href="data.json"', f'href="weeks/{cur["week_of"]}/data.json"'), 0))
    if has_cards(cur):   # per-ticker earnings-watch pages for the current week
        os.makedirs(f"{DOCS}/t")
        for r in cur["rows"]:
            t = f"{r['name']} ({r['symbol']}) Earnings Watch: Implied Move, Latest Quarter & Correlated Stocks | {SITE_NAME}"
            desc = (f"{r['name']} reports {dow(r['report_date'])} ({r['timing'].lower()}). Options imply a ±{r['move_pct']:.1f}% move "
                    f"(±${r['move_usd']:,.2f}); latest-quarter figures and most-correlated stocks.")
            open(f"{DOCS}/t/{r['symbol']}.html","w").write(page(t, desc, f"/t/{r['symbol']}.html", ticker_body(r, cur), 1))
            urls.append(f"/t/{r['symbol']}.html")
    if has_cards(cur):
        open(f"{DOCS}/anticipated.html","w").write(page(f"Most Anticipated Earnings This Week (Options Activity) | {SITE_NAME}",
            f"This week's earnings reporters ranked by options open interest plus volume.", "/anticipated.html", anticipated_body(cur), 0))
        open(f"{DOCS}/sectors.html","w").write(page(f"Earnings This Week by Sector | {SITE_NAME}",
            f"This week's earnings reporters grouped by sector, with counts and median implied moves.", "/sectors.html", sectors_body(cur), 0))
        urls += ["/anticipated.html", "/sectors.html"]
    os.makedirs(f"{DOCS}/archive")
    items = "".join(f"<li><a href='../weeks/{w['week_of']}/index.html'>Week of {nice(w['week_of'])}</a> — {len(w['rows'])} companies</li>" for w in reversed(weeks))
    open(f"{DOCS}/archive/index.html","w").write(page(f"Archive | {SITE_NAME}", "Past weekly earnings cheat sheets with expected moves.", "/archive/", f"<div class='card'><h2>Archive</h2><ul>{items}</ul></div>", 1))
    os.makedirs(f"{DOCS}/about")
    about = f"<div class='card'><h2>Method &amp; disclaimer</h2><p>{e(cur['method'])}</p><p>Source: Robinhood market data (earnings calendar, stock quotes, option chains and quotes). Data may be delayed; dates may change. Tickers without a usable option chain are skipped.</p></div>{DISCLAIMER}"
    open(f"{DOCS}/about/index.html","w").write(page(f"Method & Disclaimer | {SITE_NAME}", "How expected moves are calculated, data sources and disclaimer.", "/about/", about, 1))
    urls += ["/archive/", "/about/"]
    if not HIDDEN: open(f"{DOCS}/sitemap.xml","w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{SITE_URL}{u}</loc><lastmod>{cur['week_of'] if u=='/' else ''}</lastmod></url>\n".replace("<lastmod></lastmod>","") for u in urls) + "</urlset>\n")
    open(f"{DOCS}/robots.txt","w").write("User-agent: *\nDisallow: /\n" if HIDDEN or not LICENSE_CLEARED else f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
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
