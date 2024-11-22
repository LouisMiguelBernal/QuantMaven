# QuantMaven

QuantMaven is a Streamlit-based web application designed to provide real-time insights into stock markets, technical analysis, and economic indicators. It fetches data from Yahoo Finance and other APIs to deliver comprehensive visualization and analysis tools for investors, analysts, and financial enthusiasts.

## Web Application Link: https://quantmaven.streamlit.app/

## Features

- **Real-Time Stock Market Analysis:**
  - Fetch stock data for specific tickers and date ranges.
  - Real-time price charts and technical indicators (e.g., Moving Averages, Bollinger Bands, RSI).
  - Historical performance data.

- **Company Insights:**
  - Overview of companies, including sector, industry, and key statistics.
  - Display of relevant company news.

- **S&P 500 Market Overview:**
  - Metrics and performance visualization with moving averages.
  - Analysis of the overall S&P 500 index.

- **Economic Insights and Indicators:**
  - Integration with FRED API for GDP, interest rates, CPI (inflation), unemployment rates, and other macroeconomic data.

## Prerequisites

- **Python Version**: 3.12.6
- **Required Libraries**: Listed in `requirements.txt`

## Getting Started

### 1. Clone the repository:
```bash
git clone https://github.com/LouisMiguelBernal/QuantMaven.git
cd QuantMaven
```

### 2. Create a virtual environment (optional):
```bash
python -m venv env
source env/bin/activate  # For Unix/macOS
env\Scripts\activate     # For Windows
```

### 3. Install dependencies:
```bash
pip install -r requirements.txt
```

### 4. Run the application:
```bash
streamlit run QuantMaven.py
```

## Directory Structure

```
QuantMaven/
├── assets/                # Directory for assets (e.g., videos, images)
├── LICENSE                # Project license file
├── QuantMaven.py          # Main Streamlit application file
├── README.md              # Project README file
└── requirements.txt       # Python dependencies file
```

## Usage

1. **Stock Data Input**: Enter the stock ticker symbol and date range.
2. **Analysis Tabs**:
   - **Trading Dashboard**: View stock charts, price movements, and indicators.
   - **Market Overview**: Get insights into S&P 500 trends.
   - **Economic Insights**: Access macroeconomic indicators and trends.

## Contributing

Contributions are welcome! Please fork the repository, create a new branch, and submit a pull request with your enhancements.

## License

This project is licensed under the Apache-2.0 License. See the [LICENSE](LICENSE) file for details.

## Contact

For inquiries, feedback, or support, please reach out to [Louis Miguel Bernal](miguellouis.work@gmail.com).

