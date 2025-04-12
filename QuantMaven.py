import os
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
from fredapi import Fred
import requests
import base64

# Set the page title and layout
st.set_page_config(page_title='QuantMaven',
                   page_icon="assets/logo.png",
                   layout="wide")

# Custom CSS for styling
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

# Function to convert image to base64
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
    return encoded

# Convert logo to base64
logo_base64 = get_base64_image('assets/logo.png')

# Display the logo and title using HTML with added margin/padding to move it down
st.markdown(
    f"""
    <div style="display: flex; align-items: center; padding-top: 50px;">
        <img src="data:image/png;base64,{logo_base64}" style="width: 80px; height: auto; margin-right: 10px;">
        <h1 style="margin: 0;">Quant<span style="color:green;">Maven</span></h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Create columns for inputs
col1, col2, col3 = st.columns(3)

# Inputs in separate columns 
with col1:
    ticker = st.text_input('Enter Stock Ticker:').upper()

with col2:
    start_date = st.date_input('Start Date', value=datetime.today() - timedelta(days=365*2))

with col3:
    end_date = st.date_input('End Date', value=datetime.today())

# Automatically adjust start date if not a full year range
if end_date and start_date:
    if (end_date - start_date).days < 365:
        start_date = end_date - timedelta(days=365)

# Function to fetch stock data
@st.cache_data
def fetch_stock_data(ticker, start, end):
    try:
        data = yf.download(ticker, start=start, end=end)
        return data
    except Exception as e:
        return pd.DataFrame()

# Create Tabs for different sections of the dashboard
trading_dashboard, stock_rank, market_overview, economy = st.tabs(
    ['Trading Dashboard', 'Stock Leaderboard', 'Market Overview', 'Economic Insights']
)

# Trading Dashboard Tab
with trading_dashboard:
    if not ticker:
        st.markdown("<h1>Money Talks We <span style='color:green'> TRANSLATE</span></h1>", unsafe_allow_html=True)
        st.video("assets/stock.mp4")  # Replace with your video URL or file path

    if ticker:
        try:
            # Download stock data
            stock_data = fetch_stock_data(ticker, start_date, end_date)
            ticker_data = yf.Ticker(ticker)
            stock_info = ticker_data.info
            company_name = ticker_data.info.get('longName', ticker)
            company_domain = stock_info.get('website', 'example.com').replace('http://', '').replace('https://', '')
            logo_url = f"https://logo.clearbit.com/{company_domain}"

            # Display company logo and name
            st.markdown(f"""
                <div class="logo-and-name">
                    <img class="logo-img" src="{logo_url}" alt="Company Logo" onerror="this.style.display='none'">
                    <h1 style="display:inline;">{company_name} <span style="color:green">${stock_data['Close'].dropna().iloc[-1]:.2f}</span></h1>
                </div>
                """, unsafe_allow_html=True)

            # Ensure stock data is retrieved successfully
            if not stock_data.empty:
                # Calculate indicators for charts
                stock_data['SMA50'] = stock_data['Adj Close'].rolling(window=50).mean()
                stock_data['SMA200'] = stock_data['Adj Close'].rolling(window=200).mean()
                stock_data['20SMA'] = stock_data['Adj Close'].rolling(window=20).mean()
                stock_data['Upper Band'] = stock_data['20SMA'] + (stock_data['Adj Close'].rolling(window=20).std() * 2)
                stock_data['Lower Band'] = stock_data['20SMA'] - (stock_data['Adj Close'].rolling(window=20).std() * 2)
                delta = stock_data['Adj Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                stock_data['RSI'] = 100 - (100 / (1 + rs))

                # Candlestick Chart
                fig = go.Figure()
                candlestick_trace = go.Candlestick(
                    x=stock_data.index,
                    open=stock_data['Open'],
                    high=stock_data['High'],
                    low=stock_data['Low'],
                    close=stock_data['Adj Close'],
                    name='Candlestick',
                    increasing_line_color='green',
                    decreasing_line_color='red'
                )
                fig.add_trace(candlestick_trace)
                fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['SMA50'], mode='lines', name='SMA 50', line=dict(color='blue')))
                fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['SMA200'], mode='lines', name='SMA 200', line=dict(color='yellow')))
                fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Upper Band'], mode='lines', name='Upper Band', line=dict(color='lightblue')))
                fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Lower Band'], mode='lines', name='Lower Band', line=dict(color='slategrey')))
                fig.update_layout(title=f'{ticker} Chart', xaxis_title='Date', yaxis_title='Price', width=1700, height=700)
                st.plotly_chart(fig)

                # RSI Chart
                fig_rsi = go.Figure(go.Scatter(x=stock_data.index, y=stock_data['RSI'], mode='lines', name='RSI', line=dict(color='orange')))
                fig_rsi.update_layout(title='RSI', xaxis_title='Date', yaxis_title='RSI', width=1700, height=300, yaxis=dict(range=[0, 100]))
                st.plotly_chart(fig_rsi)

                # Stock Overview Tab
                stock_overview, company_data, stock_update = st.tabs(['Stock Overview', 'Company Data', 'Stock News'])

                with stock_overview:
                    st.markdown(f"""
                        <div class="logo-and-name" style="margin-bottom: 20px;">
                            <img class="logo-img" src="{logo_url}" alt="Company Logo" onerror="this.style.display='none'" style="border-radius: 50%; width: 50px; height: 50px;">
                            <h2 style="display:inline; vertical-align: middle; margin-left: 10px;">
                                {company_name} <span style="color: green;">Metrics</span>
                            </h2>
                        </div>
                    """, unsafe_allow_html=True)

                    # Isolated DataFrame for Average Daily Return
                    avg_daily_stock = stock_data[['Adj Close']].copy()
                    avg_daily_stock['Percent Change'] = avg_daily_stock['Adj Close'].pct_change()
                    avg_daily_stock.dropna(inplace=True)
                    avg_daily_return = avg_daily_stock['Percent Change'].mean() * 100

                    # Separate DataFrame for other metrics calculations
                    new_stock = stock_data.copy()
                    new_stock['Percent Change'] = new_stock['Adj Close'].pct_change()
                    new_stock.dropna(inplace=True)

                    yearly_return = new_stock['Percent Change'].mean() * 252 * 100
                    volatility = new_stock['Percent Change'].std() * (252**0.5) * 100  # Annualized volatility

                    # Max profit calculation with (Dynamic programming- Top Down Memoization)
                    prices = stock_data['Close'].dropna().tolist()
                    start = 0
                    end = len(prices) - 1

                    def max_profit(prices, start, end, memo=None):
                        if memo is None:
                            memo = {}
                        if end <= start:
                            return 0
                        if (start, end) in memo:
                            return memo[(start, end)]
                        max_profit_val = 0
                        for i in range(start + 1, end + 1):
                            profit = prices[i] - prices[start] + max_profit(prices, i + 1, end, memo)
                            max_profit_val = max(max_profit_val, profit)
                        memo[(start, end)] = max_profit_val
                        return max_profit_val

                    max_profit_val = max_profit(prices, start, end)

                    # Display metrics in columns
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric('Max Profit', f'{max_profit_val:.2f}')
                    col2.metric(label='Yearly Return', value=f'{yearly_return:.2f}%')
                    col3.metric('Annualized Volatility', f'{volatility:.2f}%')
                    col4.metric('Average Daily Return', f'{avg_daily_return:.2f}%')
                    col5.metric("Market Cap", stock_info.get("marketCap", "N/A"))

                    st.subheader('Stock Information Chart')
                    st.dataframe(new_stock)


                # Company Data tab - display financials
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

                # Stock News
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
                        stock_news = ticker_data.news
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

        except Exception as e:
            st.error(f'Error fetching data for {ticker}. Please check the ticker symbol or try again later. Error: {str(e)}')

# Stock Ranking (Divide & Conquer - Merge Sort)           
with stock_rank:
    # Define stock list data
    def merge_sort(stocks, key):
    # Base case: if the list has 1 or 0 elements, it's already sorted
        if len(stocks) <= 1:
            return stocks

        # Split the list into halves
        mid = len(stocks) // 2
        left_half = merge_sort(stocks[:mid], key)
        right_half = merge_sort(stocks[mid:], key)

        # Merge the sorted halves
        return merge(left_half, right_half, key)

    def merge(left, right, key):
        sorted_list = []
        while left and right:
            # Sort by the provided key in descending order
            if left[0][key] >= right[0][key]:
                sorted_list.append(left.pop(0))
            else:
                sorted_list.append(right.pop(0))

        # Append remaining elements
        sorted_list.extend(left or right)
        return sorted_list

    # Define stock list data
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

    # Fetch stock data, display company logo, and calculate average daily return
    stocks_data = []

    for stock in stock_list:
        ticker = stock['ticker']
        stock_data = fetch_stock_data(ticker, start_date, end_date)
        
        # Fetch company information and logo
        ticker_data = yf.Ticker(ticker)
        stock_info = ticker_data.info
        company_name = stock_info.get('longName', ticker)
        company_domain = stock_info.get('website', 'example.com').replace('http://', '').replace('https://', '')
        logo_url = f"https://logo.clearbit.com/{company_domain}"
        
        # Calculate Average Daily Return 
        avg_daily_stock = stock_data.copy()
        avg_daily_stock['Percent Change'] = avg_daily_stock['Adj Close'].pct_change()
        avg_daily_stock.dropna(inplace=True)
        avg_daily_return = avg_daily_stock['Percent Change'].mean() * 100

        # Get current price
        current_price = stock_data['Close'].dropna().iloc[-1]  

        # Store stock data with calculated values
        stock['avg_daily_return'] = avg_daily_return
        stock['current_price'] = current_price
        stock['logo_url'] = logo_url
        stock['company_name'] = company_name
        stocks_data.append(stock)

    # Sort stocks by average daily return using Merge Sort
    sorted_stocks = merge_sort(stocks_data, key='avg_daily_return')

    st.markdown(f"""
                    <div class="logo-and-name">
                        <h1 style="display:inline;">Top Stocks by
                            <span style="color:green">Sector</span>
                        </h1>
                    </div>
                """, unsafe_allow_html=True)

    # Display headers for metrics
    col1, col2, col3, col4 = st.columns([1, 3, 1, 2])  # Adjust column widths
    with col3:
        st.markdown("""
            <span style='font-weight:bold; font-size:20px; margin-left:-60px;'>Average Daily </span>
            <span style='color:green; font-weight:bold; font-size:20px;'>Return</span>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
            <span style='font-weight:bold; font-size:20px; margin-left:-20px;'>Current </span>
            <span style='color:green; font-weight:bold; font-size:20px;'>Price</span>
        """, unsafe_allow_html=True)

    # Layout: display logo, name, and metrics
    for stock in sorted_stocks:
        # Create columns for logo, company name, and metrics
        col1, col2, col3, col4 = st.columns([1, 3, 1, 2])  # Adjust the column widths

        with col1:
            st.image(stock['logo_url'], width=50, output_format='auto')

        with col2:
            st.markdown(f"**<span style='font-size: 24px'>{stock['company_name']}**", unsafe_allow_html=True)

        with col3:
            st.markdown(f"**<span style='font-size: 24px'>{stock['avg_daily_return']:.2f}%</span>**", unsafe_allow_html=True)

        with col4:
            st.markdown(f"**<span style='font-size: 24px'>${stock['current_price']:.2f}</span>**", unsafe_allow_html=True)
        # Add S&P 500 Information
    sector_info = """
        The companies in this portfolio are influential across their sectors, providing key insights into broader economic trends. JPMorgan Chase & Co. (JPM) serves as a bellwether for the Financials sector, where its performance reflects the stability of credit markets and economic growth. UnitedHealth Group (UNH) leads the Healthcare sector, shaping policy and spending in healthcare, while NVIDIA (NVDA) drives technological advancement in AI and semiconductors, impacting industries such as cloud computing, gaming, and AI. Similarly, Amazon (AMZN) influences consumer behavior and retail trends within the Consumer Discretionary sector, making it a critical indicator of consumer spending.

        In the Consumer Staples sector, Procter & Gamble (PG) offers valuable insight into consumer habits for essential goods, serving as a benchmark during economic downturns. ExxonMobil (XOM) dominates the Energy sector, with its stock being sensitive to commodity prices, geopolitics, and shifts toward renewable energy. NextEra Energy (NEE) in the Utilities sector highlights the growing role of renewable energy in shaping sustainable infrastructure. Meanwhile, Prologis (PLD) in Real Estate provides a clear signal of global trade and logistics demand, tied to macroeconomic health and e-commerce growth.

        Companies like Sherwin-Williams (SHW) and Caterpillar (CAT) play pivotal roles in Materials and Industrials, respectively. Sherwin-Williams reflects trends in construction and manufacturing, while Caterpillar's performance signals the health of global infrastructure, mining, and capital spending. Together, these companies offer a comprehensive view of the forces shaping the global economy, from consumer behavior and technological innovation to energy markets and infrastructure development. By tracking their performance, investors can gauge both sector-specific dynamics and broader economic conditions.
    """
    st.markdown("""
    # Stock <span style="color: green;">Sector</span>
    """, unsafe_allow_html=True)
    
    st.write(sector_info)

# Market Overview Tab
with market_overview:
    try:
        # Fetch S&P 500 data
        sp500 = yf.download('^GSPC', start=start_date, end=end_date)

        # Drop NA values and ensure the close price is available
        non_na_close = sp500['Close'].dropna()
        
        if not non_na_close.empty:
            # Get the latest close price (ensure it's a scalar)
            latest_close_price = non_na_close.iloc[-1]  # Get the last close price

            # If the retrieved price is not a scalar, convert it to a scalar
            if isinstance(latest_close_price, (float, int)):
                st.markdown(f"""
                    <div class="logo-and-name">
                        <h1 style="display:inline;">S&P 500 Metrics 
                            <span style="color:green">${latest_close_price:.2f}</span>
                        </h1>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("Error: Latest close price is not a valid number.")
        else:
            st.markdown("Error: No valid close price data available.")

    except Exception as e:
        # Handle any exceptions (e.g., issues with downloading the data)
        st.markdown(f"Error fetching data for S&P 500. Please try again later. Error: {e}")

    # S&P 500 Chart with Moving Averages and Bollinger Bands
    sp500['50_MA'] = sp500['Adj Close'].rolling(window=50).mean()
    sp500['200_MA'] = sp500['Adj Close'].rolling(window=200).mean()
    sp500['20_MA'] = sp500['Adj Close'].rolling(window=20).mean()
    sp500['stddev'] = sp500['Adj Close'].rolling(window=20).std()
    sp500['Upper_Band'] = sp500['20_MA'] + (sp500['stddev'] * 2)
    sp500['Lower_Band'] = sp500['20_MA'] - (sp500['stddev'] * 2)

    # Drop rows where the necessary columns have NaN values (e.g., for moving averages)
    sp500_cleaned = sp500.dropna(subset=['50_MA', '200_MA', '20_MA', 'Upper_Band', 'Lower_Band'])

    # Create Plotly figure
    fig_sp = go.Figure()

    # Add traces to the plot
    fig_sp.add_trace(go.Scatter(x=sp500_cleaned.index, y=sp500_cleaned['Adj Close'], mode='lines', name='Adj Close', line=dict(color='green')))
    fig_sp.add_trace(go.Scatter(x=sp500_cleaned.index, y=sp500_cleaned['50_MA'], mode='lines', name='SMA 50', line=dict(color='blue')))
    fig_sp.add_trace(go.Scatter(x=sp500_cleaned.index, y=sp500_cleaned['200_MA'], mode='lines', name='SMA 200', line=dict(color='yellow')))
    fig_sp.add_trace(go.Scatter(x=sp500_cleaned.index, y=sp500_cleaned['Upper_Band'], mode='lines', name='Upper Band', line=dict(color='lightblue')))
    fig_sp.add_trace(go.Scatter(x=sp500_cleaned.index, y=sp500_cleaned['Lower_Band'], mode='lines', name='Lower Band', line=dict(color='slategrey')))

    # Update layout for better visuals
    fig_sp.update_layout(
        title='S&P 500 Chart',
        xaxis_title='Date',
        yaxis_title='Price',
        width=1700,
        height=700,
        template='plotly_dark'  
    )

    # Show the Plotly chart
    st.plotly_chart(fig_sp)

    # Add S&P 500 Metrics
    st.markdown("""
    # S&P 500 <span style="color: green;">Metrics</span>
    """, unsafe_allow_html=True)
    
    ticker_data = yf.Ticker('^GSPC')
    stock_info = ticker_data.info

    # Add percentage change calculation
    new_stock = sp500.copy()
    new_stock['Percent Change'] = sp500['Adj Close'].pct_change()
    new_stock.dropna(inplace=True)

    yearly_return = new_stock['Percent Change'].mean() * 252 * 100
    volatility = new_stock['Percent Change'].std() * (252**0.5) * 100  # Annualized volatility
    avg_daily_return = new_stock['Percent Change'].mean() * 100

    # Display Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric(label='Yearly Return', value=f'{yearly_return:.2f}%')
    col2.metric('Annualized Volatility', f'{volatility:.2f}%')
    col3.metric('Average Daily Return', f'{avg_daily_return:.2f}%')

    # Add S&P 500 Information
    sp500_info = """
    The S&P 500 stands as a prominent benchmark for measuring the health and overall direction of the U.S. stock market. This carefully curated index tracks the performance of 500 of the largest companies listed on major U.S. stock exchanges, providing a comprehensive snapshot of the nation's economic vitality.

    Comprised of companies spanning a diverse range of industries, the S&P 500 offers a broad representation of the U.S. economy. From technology titans to consumer staples, the index encompasses a wide spectrum of sectors, ensuring that it captures the pulse of various economic drivers. The weighting of each company within the index is determined by its market capitalization, meaning larger companies exert a greater influence on its overall performance. This weighting system reflects the market's perception of a company's relative value and potential for growth.

    Beyond its role as a benchmark, the S&P 500 also serves as a valuable tool for investors and analysts. By tracking the index's movements, investors can gauge the broader market sentiment and make informed decisions about their investment portfolios. Analysts use the S&P 500 to assess the performance of individual stocks, sectors, and the economy as a whole. Additionally, the index is often used as a reference point for comparing the returns of various investment strategies and funds.
    """

    st.markdown("""
    # Index <span style="color: green;">Information</span>
    """, unsafe_allow_html=True)
    
    st.write(sp500_info)

with economy:
    # Initialize FRED API
    FRED_API_KEY = '016ec4d9c6225880b89164d0aa9d2074 '  
    fred = Fred(api_key=FRED_API_KEY)

    st.markdown(f"""
        <div class="logo-and-name">
            <h1 style="display:inline;">Economic Metrics <span style="color:green"></span></h1>
        </div>
    """, unsafe_allow_html=True)


    # Function to plot economic data
    def plot_economic_data(data_dict, title):
        fig = go.Figure()
        for series_name, data in data_dict.items():
            fig.add_trace(go.Scatter(x=data.index, y=data.values, mode='lines', name=series_name))

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Value",
            template="plotly_dark",  # Dark theme to match the example
            xaxis_rangeslider_visible=True,
            width=1000,  # Set width of the chart
            height=600   # Set height of the chart
        )
        return fig
    
    # Input for the FRED series IDs
    gdp = fred.get_series('GDP')
    interest_rate = fred.get_series('FEDFUNDS')
    inflation = fred.get_series('CPIAUCNS')
    unemployment = fred.get_series('UNRATE')

    # Display the first economic data chart (wide)
    st.plotly_chart(plot_economic_data(
        {'GDP': gdp, 'Federal Funds Rate': interest_rate}, 
        "US GDP and Interest Rate"
    ), use_container_width=True)

    # Display the second economic data chart (wide and below)
    st.plotly_chart(plot_economic_data(
        {'Inflation Rate': inflation, 'Unemployment Rate': unemployment}, 
        "US Inflation and Unemployment Rate "
    ), use_container_width=True)

    st.markdown("""
    # Economic Metrics <span style="color: green;">Information</span>
    """, unsafe_allow_html=True)

    econ_info = """
    The Economy section provides key insights into the performance of the U.S. economy using four major economic indicators:

    1. **Gross Domestic Product (GDP)**: 
        - GDP is the total monetary value of all goods and services produced within the U.S. over a specific period. It's a broad measure of overall economic activity and an important indicator of the economy’s health.

    2. **Federal Funds Rate (Interest Rate)**: 
        - The Federal Funds Rate is the interest rate at which depository institutions lend balances to other banks overnight. This rate is a crucial tool used by the Federal Reserve to control inflation and stabilize the economy. It influences borrowing costs for businesses and consumers.

    3. **Inflation Rate (CPI)**: 
        - Inflation, measured through the Consumer Price Index (CPI), tracks the change in prices paid by consumers for goods and services over time. It is a key indicator of the purchasing power of currency and the cost of living.

    4. **Unemployment Rate**: 
        - The unemployment rate measures the percentage of the total labor force that is unemployed but actively seeking employment. It's a vital indicator of labor market conditions and overall economic stability.
    """
    st.write(econ_info)


# Link to Font Awesome CSS for icons
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">', unsafe_allow_html=True)

# Footer content with logo and title moved down
footer = f"""
<hr>
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; padding: 10px 0;">
  <!-- QuantMaven Title and Logo -->
  <div style="flex-grow: 1; text-align: left; padding-top: 20px;">
    <div style="display: flex; align-items: center;">
        <img src="data:image/png;base64,{logo_base64}" style="width: 80px; height: auto; margin-right: 10px;">
        <h1 style="margin: 0;">Quant<span style="color:green;">Maven</span></h1>
    </div>
  </div>
  <!-- Copyright -->
  <div style="flex-grow: 1; text-align: center; padding-top: 20px;">
    <span>Copyright 2024 | All Rights Reserved</span>
  </div>
  <!-- Social media icons -->
  <div style="flex-grow: 1; text-align: right; padding-top: 20px;">
    <a href="https://www.linkedin.com" class="fa fa-linkedin" style="padding: 10px; font-size: 24px; background: #0077B5; color: white; text-decoration: none; margin: 5px;"></a>
    <a href="https://www.instagram.com" class="fa fa-instagram" style="padding: 10px; font-size: 24px; background: #E1306C; color: white; text-decoration: none; margin: 5px;"></a>
    <a href="https://www.youtube.com" class="fa fa-youtube" style="padding: 10px; font-size: 24px; background: #FF0000; color: white; text-decoration: none; margin: 5px;"></a>
    <a href="https://www.facebook.com" class="fa fa-facebook" style="padding: 10px; font-size: 24px; background: #3b5998; color: white; text-decoration: none; margin: 5px;"></a>
    <a href="https://twitter.com" class="fa fa-twitter" style="padding: 10px; font-size: 24px; background: #1DA1F2; color: white; text-decoration: none; margin: 5px;"></a>
  </div>
</div>
"""

# Display footer
st.markdown(footer, unsafe_allow_html=True)
