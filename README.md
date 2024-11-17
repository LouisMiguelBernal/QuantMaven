# QuantMaven Dashboard

QuantMaven is a comprehensive Streamlit-based stock market and economic dashboard. It combines real-time stock data analysis, market insights, and economic metrics to help users make informed investment decisions. QuantMaven pulls data from Yahoo Finance and other APIs to visualize stock prices, indicators, economic trends, and more. 

## Features

- **Stock Data Analysis:**
  - User input for stock ticker and date range.
  - Automated adjustments for start date if the date range is less than one year.
  - Real-time data fetched from Yahoo Finance.
  - Candlestick charts with moving averages, Bollinger Bands, and other technical indicators.
  - Relative Strength Index (RSI) chart.
  - Historical stock data and metrics (Yearly Return, Volatility, etc.).

- **Company Data & Financials:**
  - Company overview, industry, sector, and website.
  - Financial statements (Income Statement, Balance Sheet, and Cash Flow).
  - News articles related to the stock.

- **Market Overview:**
  - S&P 500 metrics and trends with charts and moving averages.
  - Detailed analysis of the S&P 500 index with historical performance and metrics.

- **Economic Insights:**
  - Visualization of major economic metrics using FRED API data.
  - Key indicators: GDP, Federal Funds Rate, Inflation Rate (CPI), and Unemployment Rate.

## Prerequisites

- **Python Version**: 3.12.6
- **Libraries**: 
  - `streamlit`
  - `yfinance`
  - `plotly`
  - `datetime`
  - `pandas`
  - `numpy`
  - `Fred` API access (for economic metrics)

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/QuantMaven.git
   cd QuantMaven
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv env
   source env/bin/activate  # For Unix-based systems
   env\Scripts\activate  # For Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Streamlit app:**
   ```bash
   streamlit run QuantMaven.py
   ```

## Usage

1. **Enter Stock Ticker**: Input the desired stock ticker (e.g., `AAPL`, `MSFT`) to fetch stock data.
2. **Select Date Range**: Pick a start and end date for the stock data visualization.
3. **Navigate Tabs**: Use the tabs for:
   - **Trading Dashboard**: Stock-specific data, charts, and metrics.
   - **Market Overview**: Insights into the S&P 500 performance.
   - **Economic Insights**: Key economic indicators for macroeconomic analysis.

## File Structure

```
QuantMaven/
│
├── QuantMaven.py                   # Main Streamlit application
├── assets/
│   └── stock.mp4            # Stock market informational video (optional)
├── README.md                # Project README file
├── requirements.txt         # Python dependencies
└── LICENSE                  # Project license (if applicable)
```


## Contributing

We welcome contributions to improve QuantMaven! Please fork the repository and submit pull requests.

---

Thank you for using QuantMaven. We hope this tool empowers you in making data-driven market decisions!
