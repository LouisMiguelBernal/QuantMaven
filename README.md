# QuantMaven

Equity research terminal — price action, fundamentals, a ranked sector board, and
the macro series everything is priced against, in one Streamlit surface.

**Live:** https://quantmaven.streamlit.app/

---

## Run it locally

Double-click `run.bat`, or from a terminal in the project folder:

```bash
run.bat
```

That creates a virtual environment on first run, installs the dependencies, and
opens the app at **http://localhost:8501**. Subsequent runs skip straight to launch.

Prefer to drive it yourself:

```bash
python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && streamlit run QuantMaven.py
```

---

## What's in it

**Dashboard** — candlesticks with volume, 50/200 SMAs, Bollinger bands and a
14-period RSI. Six headline statistics across the top: last close with the daily
move, period return, annualised volatility and return, RSI with its regime, and
market cap. Below that, four sub-tabs: session statistics, company profile and
valuation multiples, the three financial statements as reported, and recent
headlines.

**Leaderboard** — one bellwether per GICS sector, each with a sparkline, ranked by
mean daily return, period return, or price. Loading is behind a button because it
costs ten network round-trips.

**Market** — the S&P 500 with the same indicator set, plus a drawdown series.

**Economy** — GDP, the federal funds rate, CPI and unemployment from FRED, with
the latest reading and change for each.

Any view can be linked to directly: `?ticker=NVDA` seeds the ticker field.

---

## Configuration

The Economy tab needs a free [FRED API key](https://fredaccount.stlouisfed.org/apikeys).
Everything else works without configuration.

Set it as an environment variable:

```bash
set FRED_API_KEY=your_key_here
```

Or copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill it
in. That file is gitignored — never commit a key to a public repository.

Without a key the app runs normally and the Economy tab explains what is missing.

---

## Layout

```
QuantMaven/
├── .streamlit/
│   ├── config.toml              Base theme
│   └── secrets.toml.example     Template for the FRED key
├── assets/                      Logo and media
├── QuantMaven.py                The application
├── theme.py                     Shared design system
├── requirements.txt
└── run.bat                      One-command local launch
```

`theme.py` is shared verbatim with [DeepSP](https://github.com/LouisMiguelBernal/DeepSP)
and [GiftxAI](https://github.com/LouisMiguelBernal/GiftxAI) — one visual language,
one accent hue per project. Edit it in one place and copy it to the others.

---

## Notes

Market data comes from Yahoo Finance through `yfinance`, which is an unofficial
API — occasional gaps and schema changes are normal, and the app degrades to a
message rather than a traceback when a request comes back empty.

Research and educational use only. Nothing here is investment advice.

## License

Apache-2.0. See [LICENSE](LICENSE).

## Contact

[Louis Miguel Bernal](mailto:miguellouis.work@gmail.com)
