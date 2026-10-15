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
2. `python3 fetch.py YYYY-MM-DD "Mon D, YYYY, H:MM AM/PM ET"` → `data/week-YYYY-MM-DD.json`. It enforces:
   after-close expiry rule, skip if ATM strike is >5% from price, skip if a bid/ask is missing or zero, ⚑ if expiry >8 days after report.
3. `python3 build.py` locally to preview `docs/` and regenerate `newsletter/week-*.md` (draft; nothing is sent automatically).
4. Commit `data/week-*.json` (+ code/newsletter) and push to `main`. `.github/workflows/pages.yml` rebuilds docs/ and deploys it.

## Page requirements
"Source: Robinhood market data, retrieved <ET time>" · delayed-data notice · not-financial-advice disclaimer · neutral wording ·
empty, labelled sponsor slot · Formspree placeholder `YOUR_FORM_ID` (replace before promoting) · feedback mailto d.bot@mail.grokbot.com.

## Notes
- robots.txt is generated, but on a project subpath (`/earnings-cheatsheet/`) crawlers only read the domain-root robots.txt; the per-page meta tags and the sitemap still apply. Submit the sitemap in Search Console if wanted.
- The DST offset is handled automatically (zoneinfo America/New_York).
