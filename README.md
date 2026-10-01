# Bucholtz · Meridian · McWhirter Market Research App

Streamlit conversion of the supplied **V10.2.3 Ultra Lazy** notebook. Its Python calculations and patch order are preserved. This is a research tool, not a brokerage connection; it never places orders.

## Start here: GitHub and Render

1. Extract this ZIP on your computer.
2. In GitHub, create a new repository named `bucholtz-market-app`. A private repository keeps your source and embedded database from being openly downloadable. Do not add passwords to GitHub.
3. Open the repository, choose **Add file → Upload files**, and upload the **contents** of the extracted `bucholtz-market-app` folder. `app.py`, `requirements.txt` and `render.yaml` must sit at the repository root. Preserve `engine`, `source` and `.streamlit` folders. Commit the upload. If your browser omits hidden files, the app still runs with Streamlit defaults; use Git for the complete project.
4. In Render, choose **New → Blueprint**, connect GitHub, and select this repository. Render reads `render.yaml`.
5. Review the proposed service and pricing before creating it. The blueprint requests a **Starter** paid service. You can change the plan in the YAML before deploying. No deployment or purchase has been performed for you.
6. Enter a strong `APP_PASSWORD` when Render asks. Keep this password in Render, not GitHub. This is a simple shared-password gate for personal use, not a multi-user account system.
7. Apply the blueprint. When the build finishes, open the service's Render URL and sign in.
8. Start with 3–10 manual tickers. Click **Run analysis**, inspect the evidence, then **Prepare PDF, CSV and HTML reports**. The download buttons appear when reports are ready.

If using **New → Web Service** instead of Blueprint, use:

- Runtime: **Python**
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true`
- Environment variables: `PYTHON_VERSION=3.11.11` and your own `APP_PASSWORD`
- Health check: `/_stcore/health`

Documentation: https://render.com/docs/infrastructure-as-code and https://render.com/docs/web-services

## Run on Windows locally

Install Python 3.11, then open Command Prompt inside the extracted project folder:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL shown in Command Prompt. Leave that window open while using the app. Press Ctrl+C to stop.

## Included features

- Manual ticker input, Finviz/watchlist CSV (`Ticker` or `Symbol` column), liquid-stock and S&P 500 universes.
- Stocks, commodities, or both; date, session mode, long-only gate, result count and symbol limit.
- Expanded embedded first-trade database; optional replacement CSV with strict input checks. Replacement uploads apply to that scan only, not all visitors, and are not merged.
- Preserved Bucholtz, Meridian, McWhirter, technical gates, selection scoring, source quality and trade-plan levels.
- Lazy timing for the final result set: prior close, overnight, premarket, and session.
- Complete final-notebook PDF and CSV; legacy V8.4 HTML, clearly labelled.
- Bundled 2026–2030 trigger calendar/database downloads and source-rule audit.
- Separate calculation state, database and output folder per browser session.

## Operation and limits

Yahoo Finance is still the notebook's price source. It can fail or throttle requests. During-market mode does not make daily bars a real-time execution feed. Check `Data through` before acting. No live-market success is claimed from offline tests.

The original session validator uses date and New York clock time, and the previous-day timing helper skips weekends. It does **not** implement a complete exchange holiday/early-close calendar. Those limitations were retained to avoid silently changing the model.

The notebook's technical prefilter excludes weak or invalid rows before full scoring. Long-only prevents short eligibility but can retain short NO TRADE research rows. Top N applies separately to stocks and commodities. S&P 500 takes the first N source symbols, not a ranking of unscanned symbols; increase the symbol limit to widen coverage. Wikipedia/source failures can cause the inherited S&P function to fall back to the liquid universe.

Timing and PDF creation can be CPU intensive. Operations are serialised across sessions to protect Swiss Ephemeris process state. This initial version is intended for personal use and small scans. Session data, uploads and reports are temporary and reset on service restart or a new scan. Download anything you wish to keep.

No ephemeris data files were present in the notebook. The same Swiss Ephemeris call/fallback behaviour is retained; supplying external data files can change numerical output. The conversion does not certify the source books' implementation or predictive validity. Scoring preservation is not evidence of trading profitability.

Swiss Ephemeris/pyswisseph have licensing obligations. Before distributing this software or offering a public/commercial service, review the applicable AGPL/professional licensing terms and the rights to redistribute the supplied embedded database. No licence to the uploaded notebook/database has been invented. See https://www.astro.com/swisseph/swephinfo_e.htm and https://www.astro.com/swisseph/swedownload_e.htm .

## Developer validation

```sh
python -m pip install pytest
python -m pytest -q
```

See `CONVERSION.md` for extraction details and validation results. The original notebook is included under `source/` for comparison. Render installs dependencies during the build, rather than installing packages during each scan.
