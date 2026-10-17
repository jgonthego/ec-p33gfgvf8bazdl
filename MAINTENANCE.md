# Maintenance — Earnings Week Cheat Sheet

Times: ET. Site (hidden, not indexed): https://jgonthego.github.io/ec-p33gfgvf8bazdl/ (GitHub Pages via Actions; repo jgonthego/ec-p33gfgvf8bazdl,
renamed from earnings-cheatsheet on Oct 17, 2026; the old URL is intentionally dead).

## Data source decision
Source: **Robinhood market data** (via the Robinhood MCP connector). On Oct 15, 2026 the site owner
chose to publish it and accepts the terms risk. `LICENSE_CLEARED = True` in build.py makes pages indexable.
Nasdaq's public calendar may be used **only** to cross-check for missing tickers; never publish Nasdaq or Cboe data.

## Weekly refresh (Thu evening – Sun, ET)
1. An agent pulls fresh data using **only these read-only** `user-Robinhood-xai` tools. Never call order, alert, watchlist, or exercise tools.
   Save each raw response under `data/raw/` (gitignored; never committed or published):
   - `get_earnings_calendar` start_date=<day>, days=1, filter=high_market_cap → `data/raw/cal/`. One day per call; Tue/Wed/Thu often truncate at ~20 KB.
   - For names missing from a truncated day (cross-check vs Nasdaq's public calendar): `get_earnings_results` symbol=X → `data/raw/er/`.
   - Update `TICKERS` in fetch.py (target 30–60 notable names).
   - `get_equity_quotes` (≤12 symbols per call) → `data/raw/quotes/`.
   - `get_option_chains` when unsure which expirations exist, then `get_option_instruments` chain_symbol, expiration_dates=<first expiry on/after report; strictly after for after-close>, strike_price=<nearest listed strike> → `data/raw/inst/<SYM>.txt` (exactly one call/put pair per file).
   - `get_option_quotes` (≤10 ids per call) → `data/raw/optq/`.
   - Clear last week's `data/raw/` first. Never copy from other agents' outputs in `/workspace/agent-tools`; they hold unrelated lookups.
   - **Earnings-watch cards** (same read-only rules; the connector may now be named `user-Robinhood`). Call with
     `write_to_file: true` and move each result file into the folder below (only files from your own calls):
     - `get_financials` symbols=<≤20 reporters>, period=quarterly, limit=1 → `data/raw/fin/` (3 calls for ~60 names)
     - `get_earnings_results` symbol=X for every reporter → `data/raw/er/` (one per call; gives the latest reported "actual" EPS)
     - `get_equity_fundamentals` ≤10 symbols → `data/raw/fund/` (market cap for the featured matchup, sector/industry)
     - `get_equity_historicals` interval=day, start ≈ 4 months back, end=now, ≤10 symbols per call → `data/raw/hist/`
       for every symbol printed by `python3 fetch.py --universe` (reporters + their `PEERS` candidates; ~24 calls).
     - `get_equity_historicals` interval=day, start ≈ 19 months back, end=now, ≤10 **reporters** per call → `data/raw/hist_long/`
       (past earnings-day moves + 30-session change; ~6 calls). `get_earnings_results` (above) supplies report dates and am/pm timing.
     - `preview_scan` (read-only; runs a scan without saving one) with filter `symbol` ANY_OF <all reporters> and columns
       `optionsTotalOpenInterest`, `optionsTotalDayVolume` (≥ the number of reporters as limit) → `data/raw/scan/` (1 call).
       Feeds the most-anticipated ranking. Do not use the 10-day-average options columns (inconsistent values seen Oct 2026).
     Run calls in small parallel batches (≈10 at a time) to respect rate limits. Edit `PEERS` in fetch.py when `TICKERS` changes;
     `FEATURED` there overrides the auto pick (two largest reporters by market cap).
2. `python3 fetch.py YYYY-MM-DD "Mon D, YYYY, H:MM AM/PM ET"` → `data/week-YYYY-MM-DD.json`. It enforces:
   after-close expiry rule, skip if ATM strike is >5% from price, skip if a bid/ask is missing or zero, ⚑ if expiry >8 days after report.
   To add or refresh only the cards on an existing week file (keeps the expected-move rows untouched):
   `python3 fetch.py --cards data/week-YYYY-MM-DD.json`. Missing metrics stay `null` and render as "n/a"; nothing is estimated.
   Correlations use a common session calendar (days with a real bar for ≥90% of symbols), so a partially published latest
   day is dropped; the window dates are shown on every card.
3. `python3 build.py` locally to preview `docs/` and regenerate `newsletter/week-*.md` (draft; nothing is sent automatically).
4. Commit `data/week-*.json` (+ code/newsletter) and push to `main`. `.github/workflows/pages.yml` rebuilds docs/ and deploys it.

## Page requirements
"Source: Robinhood market data, retrieved <ET time>" · delayed-data notice · not-financial-advice disclaimer · neutral wording ·
empty, labelled sponsor slot · newsletter form via `FORM_ID` env var (currently `xaeqlezp`, set in the build step env of `.github/workflows/pages.yml`; unset = form hidden) · feedback mailto d.bot@mail.grokbot.com.

## US-only rule (owner decision, Oct 17, 2026)
- Publish **US-domiciled companies only**. `US_ONLY = True` in fetch.py; `apply_us_only()` runs on every `fetch.py` run
  (and on `--cards`) before the cards are added, removes non-US reporters from rows/gaps and lists them in the JSON
  `excluded` field (shown under "Data notes").
- Test = Robinhood company profile (`get_equity_fundamentals` → `headquarters_state`) is a US state or DC. **No profile → not
  verified → excluded**; never assume. Therefore `data/raw/fund/` must cover every reporter *and* every peer from
  `python3 fetch.py --universe` (~20 calls of ≤10 symbols).
- Correlation peers: single stocks must pass the same test; US-listed ETFs in `ETFS` are always allowed.
- Known edge cases: Chubb (CB) files US 10-Ks but Robinhood lists HQ Zurich → excluded. SLB (incorporated in Curaçao) and
  similar names with a US HQ in Robinhood's profile are kept. Irish-domiciled US-run names (ACN, ETN, MDT) are excluded as
  peers. For a verified exception set `DOMICILE_OVERRIDES = {"SYM": (True/False, "reason + source")}`.
- Foreign issuers were also removed from `TICKERS`/`PEERS`; when adding names, still fetch their profiles—the filter is the backstop.

## Earnings-watch cards
- `docs/t/<TICKER>.html`: full dark-neon card per reporter (current week only). Homepage + current week page: "Featured matchup"
  (two big cards) and a grid of compact cards linking to the ticker pages; table tickers link there too.
- Latest quarter = Robinhood quarterly revenue / net income / net margin + latest "actual" EPS (may be adjusted). Operating
  margin and free cash flow are not offered by `get_financials`, so they are not shown. Some companies have no quarterly
  financials on Robinhood → EPS only or n/a.
- No "Watch:" line (no factual source for it). No logos: tickers are drawn as coloured badges (`BRAND`/`NEON` in build.py).

## Most anticipated & by sector (owner decision, Oct 17, 2026)
- `add_activity()` in fetch.py: rank = options open interest (all expirations) + latest-session options volume, from the scan file.
  Stored as `options_activity` + `anticipated_rank`; the method text (`anticipated_method`, with retrieval time) is printed on
  `docs/anticipated.html`. Names without data get `null` and are ranked last; if `data/raw/scan/` is empty, no ranking is
  produced and the page says n/a. Caveat shown on the page: all-expirations activity, not earnings-expiry-only (pricing every
  contract of every expiry would need ~6,400 contract ids / ~90 quote calls per week).
- `docs/sectors.html`: groups by Robinhood `get_equity_fundamentals` → `sector`, sections ordered by count, cards within a sector
  by anticipated rank (then implied move); SVG summary = count + median implied move per sector.
- Homepage grid has a Report date / Most anticipated sort toggle and links to both pages; nav links on every page.

## Implied vs. past earnings moves
- `add_history()` in fetch.py, per reporter: for each past reported quarter (`eps.actual` present, timing am/pm) the move from the
  last close before the report to the first close after it (am: prior session close → report-day close; pm: report-day close →
  next session close). Unknown timing → that quarter is skipped. Last ≤8 moves, average absolute move, ratio = implied ÷ average
  (only with ≥4 past moves). Labels: ≥1.15 "bigger than usual", ≤0.85 "smaller than usual", otherwise "in line". ⚑ monthly-expiry
  names carry a caveat (the implied figure includes extra time value). Also the % change over the last 30 common sessions before
  the report (window dates shown). Non-directional; missing → n/a.
- Robinhood earnings history currently starts at Q1 2025, so most names show 6 past moves.

## Notes
- **Hidden site (owner decision, Oct 17, 2026):** `HIDDEN = True` in build.py → every page carries
  `<meta name="robots" content="noindex,nofollow,noarchive">`, no canonical / og:url, no sitemap.xml, robots.txt = `Disallow: /`.
  (On a project subpath crawlers only read the domain-root robots.txt, so the meta tag is what matters.) Do not submit to
  search engines or link the URL publicly; keep the repo description, homepage and topics empty.
- The DST offset is handled automatically (zoneinfo America/New_York).
