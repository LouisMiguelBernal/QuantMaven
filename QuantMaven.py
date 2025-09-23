# test_fixed.py
import os
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
from fredapi import Fred
import requests
import base64
from urllib.parse import urlparse

# ------------------------------
# Page config and CSS (same)
# ------------------------------
st.set_page_config(page_title='QuantMaven',
                   page_icon="assets/logo.png",
                   layout="wide")

st.markdown("""
    <style>
    .title {
      font-size: 60px;
      font-family: 'Arial', sans-serif;
      text-align: center;
      margin-bottom: 20px;
    }
    .green {
        color: #00704A;
    }
    .main > div {
        padding-top: 30px;
    }
    .stTabs [role="tablist"] button {
        font-size: 1.2rem;
        padding: 12px 24px;
        margin-right: 10px;
        border-radius: 8px;
        background-color: #00704A;
        color: white;
    }
    .stTabs [role="tablist"] button:focus, .stTabs [role="tablist"] button[aria-selected="true"] {
        background-color: #005a36;
        color: white;
    }
    .stTabs [role="tabpanel"] {
        padding-top: 30px;
    }
    .logo-and-name {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .logo-img {
        border-radius: 50%;
        width: 50px;
        height: 50px;
    }                
    </style>
    """, unsafe_allow_html=True)

# ------------------------------
# Helpers: base64 image
# ------------------------------
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            return encoded
    except Exception:
        return None

logo_base64 = get_base64_image('assets/logo.png')

# Header with logo
st.markdown(
    f"""
    <div style="display: flex; align-items: center; padding-top: 50px;">
        <img src="data:image/png;base64,{logo_base64}" style="width: 80px; height: auto; margin-right: 10px;">
        <h1 style="margin: 0;">Quant<span style="color:green;">Maven</span></h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ------------------------------
# Inputs
# ------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    ticker = st.text_input('Enter Stock Ticker:').upper().strip()

with col2:
    start_date = st.date_input('Start Date', value=datetime.today() - timedelta(days=365*2))

with col3:
    end_date = st.date_input('End Date', value=datetime.today())

# Ensure at least 1 year window if user provided smaller
if end_date and start_date:
    if (end_date - start_date).days < 365:
        start_date = end_date - timedelta(days=365)

# ------------------------------
# Cached fetch functions
# ------------------------------
@st.cache_data(ttl=60*60)  # cache for 1 hour
def fetch_stock_data(ticker_symbol: str, start, end):
    """Return DataFrame (can be empty)"""
    try:
        # yfinance accepts date-like objects
        data = yf.download(ticker_symbol, start=start, end=end, progress=False)
        if data is None:
            return pd.DataFrame()
        return data
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60*60)
def fetch_ticker_info(ticker_symbol: str):
    """Safely fetch ticker.info dict; return {} on failure"""
    try:
        tk = yf.Ticker(ticker_symbol)
        info = {}
        try:
            info = tk.info or {}
        except Exception:
            info = {}
        return info
    except Exception:
        return {}


@st.cache_data(ttl=60*60)
def fetch_financials(ticker_symbol: str):
    """Return a dict of financial DataFrames; fall back to empty DataFrames"""
    try:
        tk = yf.Ticker(ticker_symbol)
        fin = {}
        # wrap each attribute access; sometimes these are empty or raise
        for attr in ("financials", "balance_sheet", "cashflow", "calendar"):
            try:
                fin[attr] = getattr(tk, attr) or pd.DataFrame()
            except Exception:
                fin[attr] = pd.DataFrame()
        return fin
    except Exception:
        return {"financials": pd.DataFrame(), "balance_sheet": pd.DataFrame(), "cashflow": pd.DataFrame(), "calendar": pd.DataFrame()}


@st.cache_data(ttl=60*60)
def fetch_sp500(start, end):
    try:
        df = yf.download('^GSPC', start=start, end=end, progress=False)
        if df is None:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


def safe_extract_domain(website_str: str):
    """Given a website (maybe with http(s)), return netloc or empty string"""
    if not website_str or not isinstance(website_str, str):
        return ""
    website_str = website_str.strip()
    # If it doesn't have scheme, add to parse correctly
    if not website_str.startswith(("http://", "https://")):
        website_str = "https://" + website_str
    try:
        parsed = urlparse(website_str)
        # remove www.
        domain = parsed.netloc.replace("www.", "")
        return domain
    except Exception:
        return ""

# ------------------------------
# Tabs
# ------------------------------
trading_dashboard, stock_rank, market_overview, economy = st.tabs(
    ['Trading Dashboard', 'Stock Leaderboard', 'Market Overview', 'Economic Insights']
)

# ------------------------------
# Trading Dashboard Tab
# ------------------------------
with trading_dashboard:
    if not ticker:
        st.markdown("<h1>Money Talks We <span style='color:green'>TRANSLATE</span></h1>", unsafe_allow_html=True)
        if os.path.exists("assets/stock.mp4"):
            st.video("assets/stock.mp4")

    if ticker:
        with st.spinner("Fetching stock data..."):
            stock_data = fetch_stock_data(ticker, start_date, end_date)
            stock_info = fetch_ticker_info(ticker)

            # ---- Company Name ----
            company_name = stock_info.get('longName') or stock_info.get('shortName') or ticker

            # ---- Logo Handling ----
            company_website = stock_info.get("website", "")
            domain = safe_extract_domain(company_website)
            logo_url = f"https://logo.clearbit.com/{domain}" if domain else None
            if not logo_url:
                logo_url = "assets/logo.png" if os.path.exists("assets/logo.png") else None

        # ---- HEADER ----
        if logo_url:
            if stock_data.empty:
                last_close_str = ""
            else:
                close_series = stock_data["Close"]
                if isinstance(close_series, pd.DataFrame):  # multi-ticker case
                    close_series = close_series.iloc[:, 0]
                close_series = close_series.dropna()
                last_close_str = f"${close_series.iloc[-1]:.2f}" if not close_series.empty else ""

            st.markdown(f"""
                <div class="logo-and-name">
                    <img class="logo-img" src="{logo_url}" alt="Company Logo" onerror="this.style.display='none'">
                    <h1 style="display:inline;">{company_name} <span style="color:green">{last_close_str}</span></h1>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.header(company_name)

        # ---- EMPTY DATA CHECK ----
        if stock_data.empty:
            st.warning("No data available for the given ticker and date range. Please check the ticker symbol or date range.")
        else:
            # ---- INDICATORS ----
            df = stock_data.copy()

            # Ensure series for OHLC
            open_series = df["Open"]
            high_series = df["High"]
            low_series = df["Low"]
            close_series = df["Close"]

            if isinstance(open_series, pd.DataFrame):  # handle multi-ticker case
                open_series = open_series.iloc[:, 0]
            if isinstance(high_series, pd.DataFrame):
                high_series = high_series.iloc[:, 0]
            if isinstance(low_series, pd.DataFrame):
                low_series = low_series.iloc[:, 0]
            if isinstance(close_series, pd.DataFrame):
                close_series = close_series.iloc[:, 0]

            # Moving averages & Bollinger Bands
            df['SMA50'] = close_series.rolling(window=50).mean()
            df['SMA200'] = close_series.rolling(window=200).mean()
            df['20SMA'] = close_series.rolling(window=20).mean()
            df['Upper Band'] = df['20SMA'] + (close_series.rolling(window=20).std() * 2)
            df['Lower Band'] = df['20SMA'] - (close_series.rolling(window=20).std() * 2)

            # RSI
            delta = close_series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # ---- CANDLESTICK CHART ----
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=open_series,
                high=high_series,
                low=low_series,
                close=close_series,
                name="Candlestick",
                increasing_line_color="green",
                decreasing_line_color="red"
            )])

            # Add SMA & Bollinger Bands
            for col in ["SMA50", "SMA200", "Upper Band", "Lower Band"]:
                if col in df and not df[col].isna().all():
                    fig.add_trace(go.Scatter(x=df.index, y=df[col], mode="lines", name=col))

            fig.update_layout(
                title=f"{ticker} Price Chart",
                xaxis_title="Date",
                yaxis_title="Price",
                width=1700,
                height=700,
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(fig, use_container_width=True)

            # ---- RSI CHART ----
            if "RSI" in df.columns and not df["RSI"].isna().all():
                fig_rsi = go.Figure(go.Scatter(x=df.index, y=df["RSI"], mode="lines", name="RSI"))
                fig_rsi.update_layout(
                    title="Relative Strength Index (RSI)",
                    xaxis_title="Date",
                    yaxis_title="RSI",
                    width=1700,
                    height=300,
                    yaxis=dict(range=[0, 100])
                )
                st.plotly_chart(fig_rsi, use_container_width=True)


            # ---- TABS ----
            stock_overview, company_data, stock_update = st.tabs(['Stock Overview', 'Company Data', 'Stock News'])

            # ---- STOCK OVERVIEW ----
            with stock_overview:
                st.markdown(f"""
                    <div class="logo-and-name" style="margin-bottom: 20px;">
                        <img class="logo-img" src="{logo_url}" alt="Company Logo" onerror="this.style.display='none'" style="border-radius: 50%; width: 50px; height: 50px;">
                        <h2 style="display:inline; vertical-align: middle; margin-left: 10px;">
                            {company_name} <span style="color: green;">Metrics</span>
                        </h2>
                    </div>
                """, unsafe_allow_html=True)

                # Metrics calculations
               # ---- METRICS ----
                returns = close_series.pct_change().dropna()
                avg_daily_return = returns.mean() * 100 if not returns.empty else 0.0
                yearly_return = returns.mean() * 252 * 100 if not returns.empty else 0.0
                volatility = returns.std() * (252**0.5) * 100 if not returns.empty else 0.0

                # Max profit (DP)
                prices = close_series.dropna().tolist()

                def max_profit(prices_list, start_idx, end_idx, memo=None):
                    if memo is None:
                        memo = {}
                    if end_idx <= start_idx:
                        return 0
                    if (start_idx, end_idx) in memo:
                        return memo[(start_idx, end_idx)]
                    max_profit_val = 0
                    for i in range(start_idx + 1, end_idx + 1):
                        profit = prices_list[i] - prices_list[start_idx]
                        if i + 1 <= end_idx:
                            profit += max_profit(prices_list, i + 1, end_idx, memo)
                        max_profit_val = max(max_profit_val, profit)
                    memo[(start_idx, end_idx)] = max_profit_val
                    return max_profit_val

                max_profit_val = max_profit(prices, 0, len(prices) - 1) if prices else 0.0

                # Market cap
                market_cap_raw = stock_info.get("marketCap", None)
                if market_cap_raw is None:
                    market_cap_str = "N/A"
                else:
                    try:
                        market_cap_str = f"${int(market_cap_raw):,}"
                    except Exception:
                        market_cap_str = str(market_cap_raw)

                # ---- METRICS DISPLAY ----
                mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
                mcol1.metric("Max Profit", f"{max_profit_val:.2f}")
                mcol2.metric("Yearly Return", f"{yearly_return:.2f}%")
                mcol3.metric("Annualized Volatility", f"{volatility:.2f}%")
                mcol4.metric("Average Daily Return", f"{avg_daily_return:.2f}%")
                mcol5.metric("Market Cap", market_cap_str)

                # ---- INFO TABLE ----
                st.subheader("Stock Information Chart")

                # Extract OHLC safely
                df_display = df[['Open', 'High', 'Low', 'Close']].dropna().copy()

                # If columns are MultiIndex (e.g., ('NVDA','Open')), flatten them
                if isinstance(df_display.columns, pd.MultiIndex):
                    df_display.columns = [col[-1] for col in df_display.columns]  # keep only Open/High/Low/Close

                # Reset index -> make Date a column
                df_display = df_display.reset_index()

                # Rename first column explicitly to "Date"
                df_display.rename(columns={df_display.columns[0]: "Date"}, inplace=True)

                # Drop any accidental duplicates
                df_display = df_display.loc[:, ~df_display.columns.duplicated()]

                st.dataframe(df_display)




            # --- Company Data ---
            with company_data:
                    try:
                       # Display company information header with a logo
                        st.markdown(f"""
                        <div class="logo-and-name" style="margin-bottom: 20px;">
                            <img class="logo-img" src="{logo_url}" alt="Company Logo" onerror="this.style.display='none'" style="border-radius: 50%; width: 50px; height: 50px;">
                            <h2 style="display:inline; vertical-align: middle; margin-left: 10px;">
                                {company_name} <span style="color: green;">Information</span>
                            </h2>
                        </div>
                        """, unsafe_allow_html=True)

       
                        col1, col2 = st.columns(2)
                        col1.metric("Sector", stock_info.get("sector", "N/A"))
                        col2.metric("Industry", stock_info.get("industry", "N/A"))
                        st.metric("Website", stock_info.get("website", "N/A"))

                        # Display company bio
                        if 'longBusinessSummary' in stock_info:
                            st.subheader('Company Bio')
                            st.write(stock_info['longBusinessSummary'])
                        else:
                            st.write("Company bio is not available.")

                        # Fetch financial data
                        stock = yf.Ticker(ticker)
                        financials = {
                            "income_statement": stock.financials,
                            "balance_sheet": stock.balance_sheet,
                            "cashflow": stock.cashflow,
                            "calendar": stock.calendar,
                        }

                        # Display financials
                        st.header('Company Financials')
                        st.subheader("Income Statement:")
                        st.dataframe(financials["income_statement"])

                        st.subheader("Balance Sheet:")
                        st.dataframe(financials["balance_sheet"])

                        st.subheader("Cashflow Statement:")
                        st.dataframe(financials["cashflow"])

                    except Exception as e:
                        st.error(f"An error occurred while fetching financials: {e}")

            # --- Stock News ---
            with stock_update:
                    st.markdown(f"""
                        <div class="logo-and-name" style="margin-bottom: 20px;">
                            <img class="logo-img" src="{logo_url}" alt="Company Logo" onerror="this.style.display='none'" style="border-radius: 50%; width: 50px; height: 50px;">
                            <h2 style="display:inline; vertical-align: middle; margin-left: 10px;">
                                {company_name} <span style="color: green;">News</span>
                            </h2>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    try:
                        stock_news = ticker.news
                        if stock_news:
                            for news in stock_news[:10]:  # Displaying the top 10 news articles
                                st.write(f"### [{news['title']}]({news['link']})")
                                st.write(news['publisher'])
                                readable_date = datetime.utcfromtimestamp(news['providerPublishTime']).strftime('%Y-%m-%d %H:%M:%S')
                                st.write(f'Publised: {readable_date}')
                        else:
                            st.write("No news articles available for this stock.")
                    except Exception as e:
                        st.error(f"An error occurred while fetching stock news: {e}")

    else:
        st.warning('No data available for the given ticker and date range. Please check the ticker symbol or date range.')
    


# ------------------------------
# Stock Ranking (Merge Sort)
# ------------------------------
with stock_rank:
    # Improved merge_sort using indices (O(n log n) merges without pop(0))
    def merge_sort(stocks_list, key):
        if len(stocks_list) <= 1:
            return stocks_list

        mid = len(stocks_list) // 2
        left = merge_sort(stocks_list[:mid], key)
        right = merge_sort(stocks_list[mid:], key)
        return merge(left, right, key)

    def merge(left, right, key):
        i, j = 0, 0
        sorted_list = []
        while i < len(left) and j < len(right):
            # descending order by key
            if left[i].get(key, 0) >= right[j].get(key, 0):
                sorted_list.append(left[i])
                i += 1
            else:
                sorted_list.append(right[j])
                j += 1
        # append remainders
        if i < len(left):
            sorted_list.extend(left[i:])
        if j < len(right):
            sorted_list.extend(right[j:])
        return sorted_list

    # base stock set
    stock_list = [
        {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financials"},
        {"ticker": "UNH", "name": "UnitedHealth Group", "sector": "Healthcare"},
        {"ticker": "NVDA", "name": "NVIDIA", "sector": "Information Technology"},
        {"ticker": "AMZN", "name": "Amazon", "sector": "Consumer Discretionary"},
        {"ticker": "PG", "name": "Procter & Gamble", "sector": "Consumer Staples"},
        {"ticker": "XOM", "name": "ExxonMobil", "sector": "Energy"},
        {"ticker": "NEE", "name": "NextEra Energy", "sector": "Utilities"},
        {"ticker": "PLD", "name": "Prologis", "sector": "Real Estate"},
        {"ticker": "SHW", "name": "Sherwin-Williams", "sector": "Materials"},
        {"ticker": "CAT", "name": "Caterpillar", "sector": "Industrials"},
    ]

    # fetch & compute metrics
    stocks_data = []
    with st.spinner("Fetching leaderboard tickers..."):
        for s in stock_list:
            t = s["ticker"]
            df = fetch_stock_data(t, start_date, end_date)
            stock_info = fetch_ticker_info(t)
            company_name = stock_info.get('longName') or stock_info.get('shortName') or t
            company_website = stock_info.get("website", "")
            domain = safe_extract_domain(company_website)
            logo_url = f"https://logo.clearbit.com/{domain}" if domain else ("assets/logo.png" if os.path.exists("assets/logo.png") else None)

            avg_daily_return = 0.0
            current_price = 0.0
            if not df.empty:
                temp = df.copy()

                # Ensure Close is a Series (not DataFrame with multiple tickers)
                close_series = temp['Close']
                if isinstance(close_series, pd.DataFrame):
                    close_series = close_series.iloc[:, 0]  # take first ticker col

                temp['Percent Change'] = close_series.pct_change()
                temp.dropna(inplace=True)

                avg_daily_return = (temp['Percent Change'].mean() * 100) if not temp.empty else 0.0

                # ensure scalar close
                try:
                    current_price = float(close_series.dropna().iloc[-1])
                except Exception:
                    current_price = 0.0

            stocks_data.append({
                "ticker": t,
                "company_name": company_name,
                "sector": s.get("sector"),
                "avg_daily_return": avg_daily_return,
                "current_price": current_price,
                "logo_url": logo_url
            })

    sorted_stocks = merge_sort(stocks_data, key='avg_daily_return')

    st.markdown(f"""
                    <div class="logo-and-name">
                        <h1 style="display:inline;">Top Stocks by
                            <span style="color:green">Sector</span>
                        </h1>
                    </div>
                """, unsafe_allow_html=True)

    # headers
    col1_h, col2_h, col3_h, col4_h = st.columns([1, 3, 1, 2])
    with col3_h:
        st.markdown("""
            <span style='font-weight:bold; font-size:20px; margin-left:-60px;'>Average Daily </span>
            <span style='color:green; font-weight:bold; font-size:20px;'>Return</span>
        """, unsafe_allow_html=True)
    with col4_h:
        st.markdown("""
            <span style='font-weight:bold; font-size:20px; margin-left:-20px;'>Current </span>
            <span style='color:green; font-weight:bold; font-size:20px;'>Price</span>
        """, unsafe_allow_html=True)

    # display each sorted stock
    for s in sorted_stocks:
        c1, c2, c3, c4 = st.columns([1, 3, 1, 2])
        with c1:
            if s.get('logo_url'):
                try:
                    st.image(s['logo_url'], width=50)
                except Exception:
                    # fallback to local logo_base64
                    if logo_base64:
                        st.image(f"data:image/png;base64,{logo_base64}", width=50)
        with c2:
            st.markdown(f"**<span style='font-size: 24px'>{s['company_name']}</span>**", unsafe_allow_html=True)
        with c3:
            st.markdown(f"**<span style='font-size: 24px'>{s['avg_daily_return']:.2f}%</span>**", unsafe_allow_html=True)
        with c4:
            st.markdown(f"**<span style='font-size: 24px'>${s['current_price']:.2f}</span>**", unsafe_allow_html=True)

    # sector explanation
    sector_info = """
        The companies in this portfolio are influential across their sectors...
        (same explanatory text omitted here for brevity; keep your original paragraph)
    """
    st.markdown("""
    # Stock <span style="color: green;">Sector</span>
    """, unsafe_allow_html=True)
    st.write(sector_info)


# Market Overview Tab
# -----------------------------
with market_overview:
    sp500 = fetch_sp500(start_date, end_date)
    if sp500.empty:
        st.error("Unable to fetch S&P 500 data for the selected range.")
    else:
        import pandas as pd

        sp = sp500.copy()

        # -----------------------------
        # Helper: extract a clean Close series
        # -----------------------------
        def _extract_close_series(df: pd.DataFrame) -> pd.Series:
            # direct exact match
            if "Close" in df.columns:
                cs = df["Close"]
            else:
                found = None
                for col in df.columns:
                    if isinstance(col, tuple):
                        name = str(col[-1]).lower()
                    else:
                        name = str(col).lower()
                    if name == "close" or name.endswith("close") or "close" in name:
                        found = col
                        break
                if found is not None:
                    cs = df[found]
                else:
                    if isinstance(df.columns, pd.MultiIndex):
                        for col in df.columns:
                            if str(col[-1]).lower() == "close":
                                cs = df[col]
                                break
                        else:
                            numeric_cols = df.select_dtypes(include="number").columns
                            if len(numeric_cols):
                                cs = df[numeric_cols[0]]
                            else:
                                raise KeyError("Couldn't find a 'Close' column.")
                    else:
                        numeric_cols = df.select_dtypes(include="number").columns
                        if len(numeric_cols):
                            cs = df[numeric_cols[0]]
                        else:
                            raise KeyError("Couldn't find a 'Close' column.")

            if isinstance(cs, pd.DataFrame):
                numeric_cols = cs.select_dtypes(include="number").columns
                cs = cs[numeric_cols[0]] if len(numeric_cols) else cs.iloc[:, 0]

            return cs.astype(float)

        # -----------------------------
        # Compute indicators
        # -----------------------------
        try:
            close_series = _extract_close_series(sp)
        except KeyError as e:
            st.error(str(e))
            sp500_cleaned = sp.copy()
        else:
            ind = pd.DataFrame(index=sp.index)
            ind["50_MA"] = close_series.rolling(window=50, min_periods=50).mean()
            ind["200_MA"] = close_series.rolling(window=200, min_periods=200).mean()
            ind["20_MA"] = close_series.rolling(window=20, min_periods=20).mean()
            ind["stddev"] = close_series.rolling(window=20, min_periods=20).std()
            ind["Upper_Band"] = ind["20_MA"] + (ind["stddev"] * 2)
            ind["Lower_Band"] = ind["20_MA"] - (ind["stddev"] * 2)

            sp = pd.concat([sp, ind], axis=1)

            required_cols = ["50_MA", "200_MA", "20_MA", "Upper_Band", "Lower_Band"]
            subset = [c for c in required_cols if c in sp.columns]

            sp500_cleaned = sp.dropna(subset=subset) if subset else sp.copy()

        # -----------------------------
        # Metrics Display
        # -----------------------------
        try:
            latest_close_price = float(close_series.dropna().iloc[-1])
            st.markdown(
                f"""
                <div class="logo-and-name">
                    <h1 style="display:inline;">S&P 500 Metrics 
                        <span style="color:green">${latest_close_price:.2f}</span>
                    </h1>
                </div>
                """,
                unsafe_allow_html=True,
            )
        except Exception:
            st.markdown("S&P 500 Metrics: Price not available")

        # -----------------------------
        # Plot S&P 500 with indicators
        # -----------------------------
        fig_sp = go.Figure()
        fig_sp.add_trace(
            go.Scatter(x=sp500_cleaned.index, y=close_series, mode="lines", name="Close")
        )

        plot_cols = {
            "50_MA": "SMA 50",
            "200_MA": "SMA 200",
            "Upper_Band": "Upper Band",
            "Lower_Band": "Lower Band",
        }
        for col, legend in plot_cols.items():
            if col in sp500_cleaned.columns:
                fig_sp.add_trace(
                    go.Scatter(
                        x=sp500_cleaned.index,
                        y=sp500_cleaned[col],
                        mode="lines",
                        name=legend,
                    )
                )

        fig_sp.update_layout(
            title="S&P 500 Chart",
            xaxis_title="Date",
            yaxis_title="Price",
            width=1700,
            height=700,
            template="plotly_dark",
        )

        # ✅ FIX: give chart a unique key
        st.plotly_chart(fig_sp, key="market_overview_sp500_chart")


        st.markdown(
            """
            # Index <span style="color: green;">Information</span>
            """,
            unsafe_allow_html=True,
        )

        sp500_info = """
        The S&P 500 stands as a prominent benchmark...
        (keep your original descriptive text)
        """
        st.write(sp500_info)


# ------------------------------
# Economy (FRED)
# ------------------------------
with economy:
    FRED_API_KEY = 'YOUR_FRED_API_KEY_HERE'  # removed trailing space
    fred = None
    try:
        fred = Fred(api_key=FRED_API_KEY)
    except Exception as e:
        st.error(f"FRED init error: {e}")

    st.markdown(f"""
        <div class="logo-and-name">
            <h1 style="display:inline;">Economic Metrics <span style="color:green"></span></h1>
        </div>
    """, unsafe_allow_html=True)

    if fred:
        try:
            with st.spinner("Fetching economic series from FRED..."):
                gdp = fred.get_series('GDP')
                interest_rate = fred.get_series('FEDFUNDS')
                inflation = fred.get_series('CPIAUCNS')
                unemployment = fred.get_series('UNRATE')

            def plot_economic_data(data_dict, title):
                fig = go.Figure()
                for series_name, data in data_dict.items():
                    if data is None or getattr(data, "empty", False):
                        continue
                    # ensure index is datetime
                    try:
                        series = pd.Series(data)
                        if not isinstance(series.index, pd.DatetimeIndex):
                            series.index = pd.to_datetime(series.index)
                        fig.add_trace(go.Scatter(x=series.index, y=series.values, mode='lines', name=series_name))
                    except Exception:
                        continue
                fig.update_layout(title=title, xaxis_title="Date", yaxis_title="Value", template="plotly_dark", xaxis_rangeslider_visible=True, width=1000, height=600)
                return fig

            # Plot GDP and Federal Funds Rate
            st.plotly_chart(plot_economic_data({'GDP': gdp, 'Federal Funds Rate': interest_rate}, "US GDP and Interest Rate"), use_container_width=True)
            st.plotly_chart(plot_economic_data({'Inflation Rate': inflation, 'Unemployment Rate': unemployment}, "US Inflation and Unemployment Rate"), use_container_width=True)

            st.markdown("""
            # Economic Metrics <span style="color: green;">Information</span>
            """, unsafe_allow_html=True)

            econ_info = """
            The Economy section provides key insights into the performance of the U.S. economy using four major economic indicators:
            1. GDP
            2. Federal Funds Rate
            3. Inflation Rate (CPI)
            4. Unemployment Rate
            """
            st.write(econ_info)

        except Exception as e:
            st.error(f"Error fetching economic data: {e}")
    else:
        st.write("FRED not initialized. Economic charts unavailable.")

# ------------------------------
# Footer
# ------------------------------
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">', unsafe_allow_html=True)

footer = f"""
<hr>
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; padding: 10px 0;">
  <div style="flex-grow: 1; text-align: left; padding-top: 20px;">
    <div style="display: flex; align-items: center;">
        <img src="data:image/png;base64,{logo_base64}" style="width: 80px; height: auto; margin-right: 10px;">
        <h1 style="margin: 0;">Quant<span style="color:green;">Maven</span></h1>
    </div>
  </div>
  <div style="flex-grow: 1; text-align: center; padding-top: 20px;">
    <span>Copyright 2024 | All Rights Reserved</span>
  </div>
  <div style="flex-grow: 1; text-align: right; padding-top: 20px;">
    <a href="https://www.linkedin.com" class="fa fa-linkedin" style="padding: 10px; font-size: 24px; background: #0077B5; color: white; text-decoration: none; margin: 5px;"></a>
    <a href="https://www.instagram.com" class="fa fa-instagram" style="padding: 10px; font-size: 24px; background: #E1306C; color: white; text-decoration: none; margin: 5px;"></a>
    <a href="https://www.youtube.com" class="fa fa-youtube" style="padding: 10px; font-size: 24px; background: #FF0000; color: white; text-decoration: none; margin: 5px;"></a>
    <a href="https://www.facebook.com" class="fa fa-facebook" style="padding: 10px; font-size: 24px; background: #3b5998; color: white; text-decoration: none; margin: 5px;"></a>
    <a href="https://twitter.com" class="fa fa-twitter" style="padding: 10px; font-size: 24px; background: #1DA1F2; color: white; text-decoration: none; margin: 5px;"></a>
  </div>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)
