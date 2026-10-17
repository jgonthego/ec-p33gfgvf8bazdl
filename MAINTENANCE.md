# Maintenance — Earnings Week Cheat Sheet

Times: ET. Public site: https://jgonthego.github.io/earnings-cheatsheet (GitHub Pages via Actions).

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

## Earnings-watch cards
- `docs/t/<TICKER>.html`: full dark-neon card per reporter (current week only). Homepage + current week page: "Featured matchup"
  (two big cards) and a grid of compact cards linking to the ticker pages; table tickers link there too.
- Latest quarter = Robinhood quarterly revenue / net income / net margin + latest "actual" EPS (may be adjusted). Operating
  margin and free cash flow are not offered by `get_financials`, so they are not shown. Foreign (20-F) filers usually have no
  quarterly financials on Robinhood → EPS only or n/a.
- No "Watch:" line (no factual source for it). No logos: tickers are drawn as coloured badges (`BRAND`/`NEON` in build.py).

## Notes
- robots.txt is generated, but on a project subpath (`/earnings-cheatsheet/`) crawlers only read the domain-root robots.txt; the per-page meta tags and the sitemap still apply. Submit the sitemap in Search Console if wanted.
- The DST offset is handled automatically (zoneinfo America/New_York).
