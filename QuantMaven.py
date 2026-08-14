"""
QuantMaven — equity research terminal: price action, fundamentals, a sector
leaderboard, and macro series from FRED.

Run:  streamlit run QuantMaven.py
"""

from __future__ import annotations

import base64
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots

import theme

ROOT = Path(__file__).parent
ASSETS = ROOT / "assets"

st.set_page_config(
    page_title="QuantMaven — Equity Research Terminal",
    page_icon=str(ASSETS / "logo.png") if (ASSETS / "logo.png").exists() else "📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

P = theme.apply("quantmaven")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@st.cache_data
def logo_data_uri() -> str | None:
    path = ASSETS / "logo.png"
    if not path.exists():
        return None
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


LOGO = logo_data_uri()


# Corporate boilerplate that carries no identity — "NVIDIA Corporation" should
# initialise as NV, not NC.
_FILLER = {
    "the", "inc", "inc.", "corp", "corp.", "corporation", "company", "co",
    "co.", "group", "incorporated", "holdings", "holding", "plc", "ltd",
    "ltd.", "limited", "sa", "nv", "ag", "&", "and", "class",
}


def _initials(name: str) -> str:
    words = [
        w.strip(".,'\"()")
        for token in str(name).replace("-", " ").split()
        for w in [token]
    ]
    words = [w for w in words if w and w.lower() not in _FILLER and w[0].isalnum()]
    if not words:
        return "·"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def monogram(name: str, size: int = 38) -> str:
    """Initials tile used wherever a company mark is needed.

    Deliberately local: remote logo services need a network round-trip per row
    and leave broken images behind when they change or disappear.
    """
    initials = _initials(name)
    return (
        f'<div style="width:{size}px;height:{size}px;flex:0 0 {size}px;'
        f"border-radius:9px;background:var(--surface-2);"
        f"border:1px solid var(--line-strong);display:flex;align-items:center;"
        f"justify-content:center;font-family:var(--mono);font-weight:600;"
        f'font-size:{size * 0.36:.0f}px;color:var(--accent);letter-spacing:.02em;">'
        f"{initials or '·'}</div>"
    )


def as_series(obj) -> pd.Series:
    """yfinance returns a DataFrame when a frame carries multiple tickers.
    Collapse to the first column so downstream maths always sees a Series."""
    if isinstance(obj, pd.DataFrame):
        obj = obj.iloc[:, 0]
    return pd.to_numeric(obj, errors="coerce")


def max_profit(prices: pd.Series) -> float:
    """Best achievable P&L with unlimited round-trips and perfect foresight.

    Every upward move is capturable, so the answer is the sum of the positive
    day-over-day differences. The previous implementation recursed over every
    (start, end) pair, which was exponential without the memo and still
    O(n²) space with it — on two years of daily bars it hung the page.
    """
    diff = prices.dropna().diff()
    return float(diff[diff > 0].sum())


def fmt_big(value) -> str:
    """Compact currency for large figures: 3.42T, 918.6B, 45.2M."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    for cutoff, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(v) >= cutoff:
            return f"${v / cutoff:,.2f}{suffix}"
    return f"${v:,.2f}"


# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_prices(symbol: str, start, end) -> pd.DataFrame:
    try:
        data = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=False)
        if data is None or data.empty:
            return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [c[0] for c in data.columns]
        return data
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_info(symbol: str) -> dict:
    try:
        return yf.Ticker(symbol).info or {}
    except Exception:
        return {}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_financials(symbol: str) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    try:
        tk = yf.Ticker(symbol)
        for attr in ("financials", "balance_sheet", "cashflow"):
            try:
                frame = getattr(tk, attr)
                out[attr] = frame if isinstance(frame, pd.DataFrame) else pd.DataFrame()
            except Exception:
                out[attr] = pd.DataFrame()
    except Exception:
        out = {k: pd.DataFrame() for k in ("financials", "balance_sheet", "cashflow")}
    return out


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_news(symbol: str) -> list[dict]:
    """Normalise the two yfinance news schemas into one flat shape.

    Older releases return flat dicts with `title`/`link`/`providerPublishTime`;
    current ones nest everything under `content` with ISO timestamps.
    """
    try:
        raw = yf.Ticker(symbol).news or []
    except Exception:
        return []

    items = []
    for entry in raw:
        content = entry.get("content") or entry
        title = content.get("title") or entry.get("title")
        if not title:
            continue

        link = (
            (content.get("canonicalUrl") or {}).get("url")
            if isinstance(content.get("canonicalUrl"), dict)
            else None
        ) or (
            (content.get("clickThroughUrl") or {}).get("url")
            if isinstance(content.get("clickThroughUrl"), dict)
            else None
        ) or entry.get("link")

        provider = content.get("provider")
        publisher = (
            provider.get("displayName") if isinstance(provider, dict) else provider
        ) or entry.get("publisher") or "Unknown"

        published = ""
        if content.get("pubDate"):
            published = str(content["pubDate"])[:10]
        elif entry.get("providerPublishTime"):
            published = datetime.fromtimestamp(
                entry["providerPublishTime"], tz=timezone.utc
            ).strftime("%Y-%m-%d")

        items.append(
            {
                "title": title,
                "link": link,
                "publisher": publisher,
                "published": published,
                "summary": content.get("summary") or "",
            }
        )
    return items


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = as_series(df["Close"])
    out = df.copy()
    out["SMA50"] = close.rolling(50).mean()
    out["SMA200"] = close.rolling(200).mean()
    mid = close.rolling(20).mean()
    sd = close.rolling(20).std()
    out["BB Mid"] = mid
    out["BB Upper"] = mid + sd * 2
    out["BB Lower"] = mid - sd * 2

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    out["RSI"] = 100 - 100 / (1 + gain / loss.replace(0, pd.NA))
    return out


# ---------------------------------------------------------------------------
# Sidebar — controls
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        '<div class="tk-eyebrow">QuantMaven</div>'
        '<div style="font-size:1.05rem;font-weight:700;letter-spacing:-.02em;'
        'margin:.3rem 0 1.2rem;">Equity Research Terminal</div>',
        unsafe_allow_html=True,
    )

    # `?ticker=NVDA` seeds the field, so a view can be linked to directly.
    ticker = (
        st.text_input(
            "Ticker",
            value=st.query_params.get("ticker", ""),
            placeholder="AAPL",
        )
        .upper()
        .strip()
    )
    if ticker:
        st.query_params["ticker"] = ticker
    elif "ticker" in st.query_params:
        del st.query_params["ticker"]

    RANGES = {"1Y": 365, "2Y": 730, "5Y": 1825, "10Y": 3650}
    preset = st.radio("Range", list(RANGES) + ["Custom"], index=1, horizontal=True)

    today = datetime.today().date()
    if preset == "Custom":
        c1, c2 = st.columns(2)
        with c1:
            start_date = st.date_input("From", value=today - timedelta(days=730))
        with c2:
            end_date = st.date_input("To", value=today)
        if (end_date - start_date).days < 30:
            st.caption("Widened to a 30-day minimum.")
            start_date = end_date - timedelta(days=30)
    else:
        end_date = today
        start_date = today - timedelta(days=RANGES[preset])

    st.markdown(
        f'<div style="margin:.4rem 0 1rem;">{theme.badge(f"{start_date} → {end_date}")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    show_bb = st.checkbox("Bollinger bands", value=True)
    show_ma = st.checkbox("Moving averages", value=True)
    show_vol = st.checkbox("Volume", value=True)

    st.markdown(
        '<div style="color:var(--faint);font-size:.75rem;line-height:1.6;'
        'margin-top:1.6rem;">Market data via Yahoo Finance, macro series via '
        "FRED. Research only — not investment advice.</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

theme.hero(
    "Quant<em>Maven</em>",
    "Price action, fundamentals, and macro context in one surface — candles and "
    "indicators, company financials, a ranked sector board, and the FRED series "
    "that move all of it.",
    eyebrow="Equity Research Terminal",
    meta=[
        theme.badge("Yahoo Finance", "accent"),
        theme.badge("FRED macro"),
        theme.badge("Live data", "pos", dot=True),
    ],
    mark=LOGO,
)

tab_dash, tab_board, tab_market, tab_econ = st.tabs(
    ["Dashboard", "Leaderboard", "Market", "Economy"]
)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

with tab_dash:
    if not ticker:
        theme.empty_state(
            "Enter a ticker to begin",
            "Type a symbol in the sidebar — AAPL, NVDA, MSFT, ^GSPC, BTC-USD. "
            "Price history, indicators, fundamentals, and news load together.",
        )
        st.markdown(
            '<div style="display:flex;gap:.4rem;flex-wrap:wrap;justify-content:center;'
            'margin-top:1rem;">'
            + "".join(
                theme.badge(s)
                for s in ("AAPL", "NVDA", "MSFT", "AMZN", "JPM", "XOM", "^GSPC", "BTC-USD")
            )
            + "</div>",
            unsafe_allow_html=True,
        )
    else:
        with st.spinner(f"Loading {ticker}…"):
            prices = fetch_prices(ticker, start_date, end_date)
            info = fetch_info(ticker)

        if prices.empty:
            st.error(
                f"No price data returned for **{ticker}** over {start_date} → {end_date}. "
                "Check the symbol, or widen the range."
            )
        else:
            name = info.get("longName") or info.get("shortName") or ticker
            df = add_indicators(prices)
            close = as_series(df["Close"]).dropna()

            last = float(close.iloc[-1])
            first = float(close.iloc[0])
            prev = float(close.iloc[-2]) if len(close) > 1 else last
            day_chg = last - prev
            day_pct = day_chg / prev * 100 if prev else 0.0
            period_pct = (last / first - 1) * 100 if first else 0.0

            returns = close.pct_change().dropna()
            vol = float(returns.std() * (252 ** 0.5) * 100) if not returns.empty else 0.0
            ann_ret = float(returns.mean() * 252 * 100) if not returns.empty else 0.0
            rsi_now = df["RSI"].dropna()
            rsi_now = float(rsi_now.iloc[-1]) if not rsi_now.empty else float("nan")

            st.markdown(
                '<div style="display:flex;align-items:center;gap:.85rem;margin:.4rem 0 1.2rem;">'
                + monogram(name, 44)
                + '<div><div style="font-size:1.5rem;font-weight:700;letter-spacing:-.025em;'
                f'line-height:1.15;">{name}</div>'
                f'<div style="color:var(--faint);font-size:.8rem;font-family:var(--mono);'
                f'margin-top:.15rem;">{ticker}'
                + (f" · {info['exchange']}" if info.get("exchange") else "")
                + (f" · {info['sector']}" if info.get("sector") else "")
                + "</div></div></div>",
                unsafe_allow_html=True,
            )

            theme.stat_row(
                [
                    {
                        "label": "Last close",
                        "value": f"${last:,.2f}",
                        "delta": f"{day_chg:+,.2f} ({day_pct:+.2f}%) on the day",
                        "tone": "pos" if day_chg >= 0 else "neg",
                    },
                    {
                        "label": "Period return",
                        "value": f"{period_pct:+.1f}%",
                        "delta": f"{start_date} → {end_date}",
                        "tone": "pos" if period_pct >= 0 else "neg",
                    },
                    {
                        "label": "Annualised vol",
                        "value": f"{vol:.1f}%",
                        "delta": "From daily returns",
                    },
                    {
                        "label": "Annualised return",
                        "value": f"{ann_ret:+.1f}%",
                        "delta": "Mean daily × 252",
                        "tone": "pos" if ann_ret >= 0 else "neg",
                    },
                    {
                        "label": "RSI (14)",
                        "value": "—" if rsi_now != rsi_now else f"{rsi_now:.0f}",
                        "delta": (
                            "—"
                            if rsi_now != rsi_now
                            else "Overbought" if rsi_now > 70
                            else "Oversold" if rsi_now < 30
                            else "Neutral"
                        ),
                        "tone": (
                            "neg" if rsi_now > 70 else "pos" if rsi_now < 30 else ""
                        ),
                    },
                    {
                        "label": "Market cap",
                        "value": fmt_big(info.get("marketCap")),
                        "delta": info.get("industry", "") or "",
                    },
                ]
            )

            # ---- price chart -------------------------------------------------
            rows = 2 if show_vol else 1
            heights = [0.76, 0.24] if show_vol else [1.0]
            fig = make_subplots(
                rows=rows, cols=1, shared_xaxes=True,
                vertical_spacing=0.04, row_heights=heights,
            )
            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=as_series(df["Open"]),
                    high=as_series(df["High"]),
                    low=as_series(df["Low"]),
                    close=as_series(df["Close"]),
                    name=ticker,
                    increasing=dict(line=dict(color=P["pos"], width=1), fillcolor=P["pos"]),
                    decreasing=dict(line=dict(color=P["neg"], width=1), fillcolor=P["neg"]),
                ),
                row=1, col=1,
            )
            if show_bb:
                fig.add_trace(
                    go.Scatter(
                        x=df.index, y=df["BB Upper"], name="BB upper",
                        line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip",
                    ), row=1, col=1,
                )
                fig.add_trace(
                    go.Scatter(
                        x=df.index, y=df["BB Lower"], name="Bollinger 20 · 2σ",
                        line=dict(color="rgba(0,0,0,0)"),
                        fill="tonexty", fillcolor="rgba(90,214,224,0.07)", hoverinfo="skip",
                    ), row=1, col=1,
                )
            if show_ma:
                for col, colour, dash in (
                    ("SMA50", P["accent_2"], "dot"),
                    ("SMA200", P["warn"], "dash"),
                ):
                    if not df[col].isna().all():
                        fig.add_trace(
                            go.Scatter(
                                x=df.index, y=df[col], name=col.replace("SMA", "SMA "),
                                line=dict(color=colour, width=1.2, dash=dash),
                                hovertemplate="$%{y:,.2f}<extra>" + col + "</extra>",
                            ), row=1, col=1,
                        )
            if show_vol and "Volume" in df:
                colors = [
                    P["pos"] if c >= o else P["neg"]
                    for c, o in zip(as_series(df["Close"]), as_series(df["Open"]))
                ]
                fig.add_trace(
                    go.Bar(
                        x=df.index, y=as_series(df["Volume"]), name="Volume",
                        marker_color=colors, marker_line_width=0, opacity=0.45,
                        hovertemplate="%{y:,.0f}<extra>Volume</extra>",
                    ), row=2, col=1,
                )
                fig.update_yaxes(title_text="Volume", row=2, col=1)

            fig.update_yaxes(title_text="Price", row=1, col=1)
            fig.update_layout(xaxis_rangeslider_visible=False)
            theme.style_fig(fig, height=560)
            st.plotly_chart(fig, use_container_width=True)

            # ---- RSI ---------------------------------------------------------
            if not df["RSI"].isna().all():
                fig_rsi = go.Figure(
                    go.Scatter(
                        x=df.index, y=df["RSI"], name="RSI (14)",
                        line=dict(color=P["accent"], width=1.4),
                        hovertemplate="%{y:.1f}<extra>RSI</extra>",
                    )
                )
                fig_rsi.add_hrect(
                    y0=30, y1=70, fillcolor="rgba(255,255,255,0.025)", line_width=0
                )
                for level, colour in ((70, P["neg"]), (30, P["pos"])):
                    fig_rsi.add_hline(
                        y=level, line_dash="dot", line_color=colour, line_width=1
                    )
                fig_rsi.update_yaxes(range=[0, 100], title_text="RSI")
                theme.style_fig(fig_rsi, height=190, legend=False)
                st.plotly_chart(fig_rsi, use_container_width=True)

            # ---- detail tabs -------------------------------------------------
            t_over, t_co, t_fin, t_news = st.tabs(
                ["Overview", "Company", "Financials", "News"]
            )

            with t_over:
                theme.section("Session statistics")
                hi = float(as_series(df["High"]).max())
                lo = float(as_series(df["Low"]).min())
                c1, c2 = st.columns([1, 1])
                with c1:
                    theme.kv_panel(
                        "Range",
                        [
                            ("Period high", f"${hi:,.2f}"),
                            ("Period low", f"${lo:,.2f}"),
                            ("52w high", f"${info['fiftyTwoWeekHigh']:,.2f}" if info.get("fiftyTwoWeekHigh") else "—"),
                            ("52w low", f"${info['fiftyTwoWeekLow']:,.2f}" if info.get("fiftyTwoWeekLow") else "—"),
                            ("Sessions", f"{len(df):,}"),
                        ],
                    )
                with c2:
                    theme.kv_panel(
                        "Performance",
                        [
                            ("Best day", f"{returns.max() * 100:+.2f}%" if not returns.empty else "—"),
                            ("Worst day", f"{returns.min() * 100:+.2f}%" if not returns.empty else "—"),
                            ("Avg daily return", f"{returns.mean() * 100:+.3f}%" if not returns.empty else "—"),
                            ("Perfect-foresight P&L", f"${max_profit(close):,.2f}"),
                            ("Buy and hold", f"${last - first:,.2f}"),
                        ],
                    )
                st.caption(
                    "Perfect-foresight P&L is the theoretical maximum from capturing "
                    "every up-move with unlimited round-trips — an upper bound on any "
                    "strategy over this window, not an achievable target."
                )

                theme.section("Price history")
                table = df[["Open", "High", "Low", "Close", "Volume"]].dropna().copy()
                table.index.name = "Date"
                st.dataframe(
                    table.sort_index(ascending=False),
                    use_container_width=True,
                    height=340,
                    column_config={
                        c: st.column_config.NumberColumn(c, format="$%.2f")
                        for c in ("Open", "High", "Low", "Close")
                    },
                )
                st.download_button(
                    f"Download {ticker} history",
                    data=table.to_csv().encode(),
                    file_name=f"{ticker}_{start_date}_{end_date}.csv",
                    mime="text/csv",
                )

            with t_co:
                if not info:
                    st.info("No company profile available for this symbol.")
                else:
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        theme.kv_panel(
                            "Profile",
                            [
                                ("Sector", info.get("sector", "—")),
                                ("Industry", info.get("industry", "—")),
                                ("Country", info.get("country", "—")),
                                ("Employees", f"{info['fullTimeEmployees']:,}" if info.get("fullTimeEmployees") else "—"),
                                ("Exchange", info.get("exchange", "—")),
                            ],
                        )
                    with c2:
                        theme.kv_panel(
                            "Valuation",
                            [
                                ("Market cap", fmt_big(info.get("marketCap"))),
                                ("Trailing P/E", f"{info['trailingPE']:.1f}" if info.get("trailingPE") else "—"),
                                ("Forward P/E", f"{info['forwardPE']:.1f}" if info.get("forwardPE") else "—"),
                                ("Price / book", f"{info['priceToBook']:.2f}" if info.get("priceToBook") else "—"),
                                ("Dividend yield", f"{info['dividendYield']:.2f}%" if info.get("dividendYield") else "—"),
                                ("Beta", f"{info['beta']:.2f}" if info.get("beta") else "—"),
                            ],
                        )
                    if info.get("website"):
                        st.markdown(f"[{info['website']}]({info['website']})")
                    if info.get("longBusinessSummary"):
                        theme.section("Business")
                        st.write(info["longBusinessSummary"])

            with t_fin:
                fins = fetch_financials(ticker)
                labels = {
                    "financials": "Income statement",
                    "balance_sheet": "Balance sheet",
                    "cashflow": "Cash flow",
                }
                if all(f.empty for f in fins.values()):
                    st.info("Yahoo Finance returned no statements for this symbol.")
                for key, label in labels.items():
                    frame = fins.get(key, pd.DataFrame())
                    if frame.empty:
                        continue
                    theme.section(label, "Figures as reported, most recent period first.")
                    display = frame.copy()
                    display.columns = [
                        c.strftime("%Y-%m-%d") if hasattr(c, "strftime") else str(c)
                        for c in display.columns
                    ]
                    st.dataframe(display, use_container_width=True, height=380)

            with t_news:
                items = fetch_news(ticker)
                if not items:
                    st.info("No recent headlines for this symbol.")
                for item in items[:12]:
                    title = theme.esc(item["title"])
                    head = (
                        f'<a href="{item["link"]}" target="_blank">{title}</a>'
                        if item["link"]
                        else title
                    )
                    meta = " · ".join(x for x in (item["publisher"], item["published"]) if x)
                    summary = theme.esc(item["summary"][:220]) if item["summary"] else ""
                    st.markdown(
                        f'<div class="tk-panel" style="padding:1rem 1.15rem;">'
                        f'<div style="font-size:.95rem;font-weight:600;line-height:1.45;">{head}</div>'
                        f'<div style="color:var(--faint);font-size:.74rem;font-family:var(--mono);'
                        f'margin-top:.4rem;">{theme.esc(meta)}</div>'
                        + (
                            f'<p style="margin-top:.55rem;font-size:.85rem;">{summary}…</p>'
                            if summary
                            else ""
                        )
                        + "</div>",
                        unsafe_allow_html=True,
                    )


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

SECTOR_LEADERS = [
    ("JPM", "Financials"),
    ("UNH", "Healthcare"),
    ("NVDA", "Information Technology"),
    ("AMZN", "Consumer Discretionary"),
    ("PG", "Consumer Staples"),
    ("XOM", "Energy"),
    ("NEE", "Utilities"),
    ("PLD", "Real Estate"),
    ("SHW", "Materials"),
    ("CAT", "Industrials"),
]


@st.cache_data(ttl=3600, show_spinner=False)
def build_leaderboard(start, end) -> list[dict]:
    rows = []
    for symbol, sector in SECTOR_LEADERS:
        frame = fetch_prices(symbol, start, end)
        info = fetch_info(symbol)
        row = {
            "ticker": symbol,
            "sector": sector,
            "name": info.get("longName") or info.get("shortName") or symbol,
            "avg_daily": 0.0,
            "period": 0.0,
            "price": 0.0,
            "spark": [],
        }
        if not frame.empty:
            close = as_series(frame["Close"]).dropna()
            if len(close) > 1:
                pct = close.pct_change().dropna()
                row["avg_daily"] = float(pct.mean() * 100)
                row["period"] = float((close.iloc[-1] / close.iloc[0] - 1) * 100)
                row["price"] = float(close.iloc[-1])
                # Thin the series so the sparkline stays cheap to draw.
                step = max(1, len(close) // 60)
                row["spark"] = close.iloc[::step].tolist()
        rows.append(row)
    return rows


def sparkline(values: list[float], colour: str) -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            y=values, mode="lines",
            line=dict(color=colour, width=1.4),
            fill="tozeroy", fillcolor="rgba(255,255,255,0.035)",
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        height=44, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, xaxis=dict(visible=False),
        yaxis=dict(visible=False, range=[min(values) * 0.98, max(values) * 1.02]),
    )
    return fig


with tab_board:
    theme.section(
        "Sector leaders",
        "One bellwether per GICS sector, ranked by mean daily return over the "
        "selected window.",
    )

    sort_key = st.radio(
        "Rank by",
        ["Average daily return", "Period return", "Price"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if st.button("Load leaderboard", type="primary") or st.session_state.get("board_on"):
        st.session_state["board_on"] = True
        with st.spinner("Fetching ten tickers…"):
            board = build_leaderboard(start_date, end_date)

        key = {
            "Average daily return": "avg_daily",
            "Period return": "period",
            "Price": "price",
        }[sort_key]
        board.sort(key=lambda r: r[key], reverse=True)

        head = st.columns([0.5, 3.4, 2, 1.6, 1.6, 1.6])
        for col, label in zip(
            head, ["#", "Company", "Trend", "Avg daily", "Period", "Price"]
        ):
            col.markdown(
                f'<div class="tk-eyebrow" style="padding-bottom:.4rem;">{label}</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            '<div style="height:1px;background:var(--line);margin-bottom:.3rem;"></div>',
            unsafe_allow_html=True,
        )

        for rank, row in enumerate(board, 1):
            c = st.columns([0.5, 3.4, 2, 1.6, 1.6, 1.6])
            c[0].markdown(
                f'<div class="mono" style="color:var(--faint);padding-top:.85rem;">'
                f"{rank:02d}</div>",
                unsafe_allow_html=True,
            )
            c[1].markdown(
                '<div style="display:flex;align-items:center;gap:.7rem;padding-top:.35rem;">'
                + monogram(row["name"], 34)
                + f'<div><div style="font-weight:600;font-size:.93rem;line-height:1.3;">'
                f'{theme.esc(row["name"])}</div>'
                f'<div style="color:var(--faint);font-size:.72rem;font-family:var(--mono);">'
                f'{row["ticker"]} · {theme.esc(row["sector"])}</div></div></div>',
                unsafe_allow_html=True,
            )
            with c[2]:
                if row["spark"]:
                    st.plotly_chart(
                        sparkline(
                            row["spark"], P["pos"] if row["period"] >= 0 else P["neg"]
                        ),
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key=f"spark_{row['ticker']}",
                    )
            for col, value, suffix, colour in (
                (c[3], row["avg_daily"], "%", True),
                (c[4], row["period"], "%", True),
                (c[5], row["price"], "", False),
            ):
                tone = (
                    "var(--pos)" if value >= 0 else "var(--neg)"
                ) if colour else "var(--text)"
                text = f"{value:+.2f}{suffix}" if colour else f"${value:,.2f}"
                col.markdown(
                    f'<div class="mono" style="padding-top:.85rem;font-size:.92rem;'
                    f'font-weight:600;color:{tone};">{text}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                '<div style="height:1px;background:var(--line);margin:.35rem 0;"></div>',
                unsafe_allow_html=True,
            )

        theme.section("Reading the board")
        theme.panel(
            "What these ten represent",
            "<p>Each name is the largest or most characteristic constituent of its "
            "GICS sector, so the board doubles as a rough map of where the index is "
            "carrying risk. Technology and consumer discretionary tend to lead in "
            "expansions and give it back fastest; staples, utilities and healthcare "
            "compress in both directions; energy and materials track the commodity "
            "cycle rather than the equity one.</p>"
            "<p>Mean daily return is deliberately unweighted and un-annualised. It "
            "answers a narrow question — which of these compounded most reliably per "
            "session over the window — and says nothing about the volatility taken to "
            "get there. Read it next to the sparkline, not on its own.</p>",
        )
    else:
        theme.empty_state(
            "Leaderboard is idle",
            "Loading pulls ten tickers from Yahoo Finance. It is behind a button so "
            "the rest of the terminal stays fast.",
        )


# ---------------------------------------------------------------------------
# Market
# ---------------------------------------------------------------------------

with tab_market:
    theme.section("S&P 500", "The index, with the same indicator set as the dashboard.")

    spx = fetch_prices("^GSPC", start_date, end_date)
    if spx.empty:
        st.error("Could not fetch S&P 500 data for this range.")
    else:
        spx = add_indicators(spx)
        close = as_series(spx["Close"]).dropna()
        last = float(close.iloc[-1])
        period_pct = (last / float(close.iloc[0]) - 1) * 100
        rets = close.pct_change().dropna()
        dd = float((close / close.cummax() - 1).min() * 100)

        theme.stat_row(
            [
                {"label": "Level", "value": f"{last:,.2f}", "tone": "accent"},
                {
                    "label": "Period return",
                    "value": f"{period_pct:+.1f}%",
                    "tone": "pos" if period_pct >= 0 else "neg",
                },
                {
                    "label": "Annualised vol",
                    "value": f"{rets.std() * (252 ** 0.5) * 100:.1f}%",
                },
                {"label": "Max drawdown", "value": f"{dd:.1f}%", "tone": "neg"},
                {"label": "Sessions", "value": f"{len(spx):,}"},
            ]
        )

        fig_spx = go.Figure()
        fig_spx.add_trace(
            go.Scatter(
                x=spx.index, y=spx["BB Upper"], line=dict(color="rgba(0,0,0,0)"),
                showlegend=False, hoverinfo="skip",
            )
        )
        fig_spx.add_trace(
            go.Scatter(
                x=spx.index, y=spx["BB Lower"], name="Bollinger 20 · 2σ",
                line=dict(color="rgba(0,0,0,0)"), fill="tonexty",
                fillcolor="rgba(90,214,224,0.07)", hoverinfo="skip",
            )
        )
        fig_spx.add_trace(
            go.Scatter(
                x=spx.index, y=close, name="S&P 500",
                line=dict(color=P["accent"], width=1.7),
                hovertemplate="%{y:,.2f}<extra>Close</extra>",
            )
        )
        for col, colour, dash in (("SMA50", P["accent_2"], "dot"), ("SMA200", P["warn"], "dash")):
            if not spx[col].isna().all():
                fig_spx.add_trace(
                    go.Scatter(
                        x=spx.index, y=spx[col], name=col.replace("SMA", "SMA "),
                        line=dict(color=colour, width=1.1, dash=dash),
                        hovertemplate="%{y:,.2f}<extra>" + col + "</extra>",
                    )
                )
        fig_spx.update_yaxes(title_text="Index level")
        theme.style_fig(fig_spx, height=520)
        st.plotly_chart(fig_spx, use_container_width=True, key="market_spx")

        theme.section("Drawdown")
        fig_dd = go.Figure(
            go.Scatter(
                x=close.index, y=(close / close.cummax() - 1) * 100,
                fill="tozeroy", fillcolor="rgba(255,107,107,0.15)",
                line=dict(color=P["neg"], width=1.1), name="Drawdown",
                hovertemplate="%{y:.1f}%<extra>Drawdown</extra>",
            )
        )
        fig_dd.update_yaxes(ticksuffix="%")
        theme.style_fig(fig_dd, height=240, legend=False)
        st.plotly_chart(fig_dd, use_container_width=True, key="market_dd")

        theme.panel(
            "About the index",
            "<p>The S&P 500 tracks 500 large-cap US companies weighted by float-"
            "adjusted market capitalisation, which means a handful of the largest "
            "names drive a disproportionate share of its movement. It is the "
            "default benchmark for US equity risk and the reference series behind "
            "most index funds, futures and options quoted as \"the market\".</p>"
            "<p>Because the weighting is by size rather than equally, index-level "
            "strength can coexist with a majority of constituents falling. Compare "
            "it against the sector board before concluding the move is broad.</p>",
        )


# ---------------------------------------------------------------------------
# Economy (FRED)
# ---------------------------------------------------------------------------

FRED_SERIES = {
    "GDP": ("GDP", "Gross domestic product", "$B"),
    "FEDFUNDS": ("FEDFUNDS", "Federal funds rate", "%"),
    "CPIAUCNS": ("CPIAUCNS", "Consumer price index", "Index"),
    "UNRATE": ("UNRATE", "Unemployment rate", "%"),
}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fred(api_key: str, series_id: str) -> pd.Series:
    from fredapi import Fred

    series = Fred(api_key=api_key).get_series(series_id)
    series = pd.Series(series)
    if not isinstance(series.index, pd.DatetimeIndex):
        series.index = pd.to_datetime(series.index)
    return series


with tab_econ:
    theme.section(
        "Macro backdrop",
        "Four series from the St. Louis Fed that set the discount rate every "
        "equity is priced against.",
    )

    # Never hardcode the key — this repo is public. Environment variable first,
    # then .streamlit/secrets.toml.
    api_key = os.environ.get("FRED_API_KEY", "")
    if not api_key:
        try:
            api_key = st.secrets["FRED_API_KEY"]
        except Exception:
            api_key = ""

    if not api_key:
        theme.empty_state(
            "FRED key not configured",
            "Economic data is disabled. Get a free key at "
            "fredaccount.stlouisfed.org/apikeys, then set FRED_API_KEY as an "
            "environment variable or add it to .streamlit/secrets.toml.",
        )
    else:
        try:
            with st.spinner("Fetching FRED series…"):
                data = {
                    sid: fetch_fred(api_key, sid) for sid, _, _ in FRED_SERIES.values()
                }

            latest = []
            for sid, (_, label, unit) in FRED_SERIES.items():
                series = data[sid].dropna()
                if series.empty:
                    continue
                value = float(series.iloc[-1])
                prior = float(series.iloc[-2]) if len(series) > 1 else value
                latest.append(
                    {
                        "label": label,
                        "value": f"{value:,.2f}" + ("%" if unit == "%" else ""),
                        "delta": f"{value - prior:+.2f} vs prior · "
                        f"{series.index[-1].strftime('%b %Y')}",
                        "tone": "pos" if value >= prior else "neg",
                    }
                )
            theme.stat_row(latest)

            colors = theme.series_colors()
            for idx, (sid, (_, label, unit)) in enumerate(FRED_SERIES.items()):
                series = data[sid].dropna()
                if series.empty:
                    continue
                fig = go.Figure(
                    go.Scatter(
                        x=series.index, y=series.values, name=label,
                        line=dict(color=colors[idx % len(colors)], width=1.5),
                        fill="tozeroy", fillcolor="rgba(255,255,255,0.025)",
                        hovertemplate="%{y:,.2f}<extra>" + label + "</extra>",
                    )
                )
                fig.update_layout(title=f"{label} · {sid}")
                fig.update_yaxes(title_text=unit)
                theme.style_fig(fig, height=260, legend=False)
                st.plotly_chart(fig, use_container_width=True, key=f"fred_{sid}")

            theme.panel(
                "Why these four",
                theme.bullets(
                    [
                        "**GDP. **The level of output. Equity earnings are a claim on "
                        "it, so sustained contraction shows up in forward estimates "
                        "before it shows up in prices.",
                        "**Federal funds rate. **The policy rate, and the base of "
                        "every discount rate. Rising rates compress the multiple on "
                        "long-duration cash flows hardest — growth before value.",
                        "**CPI. **Headline consumer prices. It drives the policy rate "
                        "above, which is the channel through which it reaches equities.",
                        "**Unemployment. **The lagging half of the Fed's mandate. It "
                        "turns after the cycle does, which makes it a confirmation "
                        "series rather than a leading one.",
                    ]
                ),
            )
        except Exception as exc:
            st.error(f"FRED request failed — {exc}")


theme.footer(
    '<b>QuantMaven</b> · Equity research terminal',
    "Yahoo Finance · FRED · Streamlit — research use only",
)
