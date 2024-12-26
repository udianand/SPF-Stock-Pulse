import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_stock_data(symbol, start_date, end_date):
    """
    Fetch stock data from Yahoo Finance
    """
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(start=start_date, end=end_date)
        return hist, stock.info
    except Exception as e:
        return None, None

def get_key_metrics(stock_info):
    """
    Extract key financial metrics from stock info
    """
    metrics = {}
    keys = [
        'marketCap', 'trailingPE', 'forwardPE', 'dividendYield',
        'fiftyTwoWeekHigh', 'fiftyTwoWeekLow', 'volume',
        'averageVolume', 'priceToBook'
    ]
    
    for key in keys:
        if key in stock_info:
            value = stock_info[key]
            if key == 'marketCap':
                value = f"${value:,.0f}"
            elif key in ['trailingPE', 'forwardPE', 'priceToBook']:
                value = f"{value:.2f}"
            elif key == 'dividendYield' and value is not None:
                value = f"{value:.2%}"
            metrics[key] = value
        else:
            metrics[key] = 'N/A'
    
    return pd.DataFrame(metrics.items(), columns=['Metric', 'Value'])

def format_data_for_download(hist_data):
    """
    Format historical data for CSV download
    """
    df = hist_data.copy()
    df.index = df.index.strftime('%Y-%m-%d')
    df = df.round(2)
    return df
