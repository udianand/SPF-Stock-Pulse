import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def get_stock_data(symbol, start_date, end_date):
    """
    Fetch stock data from Yahoo Finance
    """
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(start=start_date, end=end_date)
        return hist, stock.info
    except Exception as e:
        print(f"Error fetching stock data: {str(e)}")
        return None, None

def get_stock_news(symbol: str, limit: int = 10) -> list:
    """
    Fetch latest news for a given stock symbol
    """
    try:
        stock = yf.Ticker(symbol)
        news = stock.news

        # Process and format news items
        formatted_news = []
        for item in news[:limit]:
            # Convert timestamp to datetime
            news_datetime = datetime.fromtimestamp(item['providerPublishTime'])

            formatted_news.append({
                'title': item['title'],
                'publisher': item['publisher'],
                'link': item['link'],
                'published_at': news_datetime,
                'type': item.get('type', 'Article'),
                'related_tickers': item.get('relatedTickers', []),
                'summary': item.get('summary', '')
            })

        return formatted_news
    except Exception as e:
        print(f"Error fetching news data: {str(e)}")
        return []

def get_fundamental_metrics(stock_info):
    """
    Extract and format comprehensive financial metrics for fundamental analysis
    """
    if not stock_info:
        return pd.DataFrame()

    metrics = {
        'Valuation': {
            'Market Cap': stock_info.get('marketCap', 'N/A'),
            'Enterprise Value': stock_info.get('enterpriseValue', 'N/A'),
            'P/E Ratio': stock_info.get('trailingPE', 'N/A'),
            'Forward P/E': stock_info.get('forwardPE', 'N/A'),
            'PEG Ratio': stock_info.get('pegRatio', 'N/A'),
            'Price/Book': stock_info.get('priceToBook', 'N/A'),
            'Price/Sales': stock_info.get('priceToSalesTrailing12Months', 'N/A')
        },
        'Financial Health': {
            'Quick Ratio': stock_info.get('quickRatio', 'N/A'),
            'Current Ratio': stock_info.get('currentRatio', 'N/A'),
            'Debt/Equity': stock_info.get('debtToEquity', 'N/A'),
            'Return on Equity': stock_info.get('returnOnEquity', 'N/A'),
            'Return on Assets': stock_info.get('returnOnAssets', 'N/A'),
            'Operating Margins': stock_info.get('operatingMargins', 'N/A'),
            'Profit Margins': stock_info.get('profitMargins', 'N/A')
        },
        'Growth & Performance': {
            'Revenue Growth': stock_info.get('revenueGrowth', 'N/A'),
            'Earnings Growth': stock_info.get('earningsGrowth', 'N/A'),
            'Dividend Rate': stock_info.get('dividendRate', 'N/A'),
            'Dividend Yield': stock_info.get('dividendYield', 'N/A'),
            'Payout Ratio': stock_info.get('payoutRatio', 'N/A'),
            'Beta': stock_info.get('beta', 'N/A'),
            '52-Week High': stock_info.get('fiftyTwoWeekHigh', 'N/A'),
            '52-Week Low': stock_info.get('fiftyTwoWeekLow', 'N/A')
        }
    }

    # Format the metrics
    formatted_metrics = []
    for category, category_metrics in metrics.items():
        for metric, value in category_metrics.items():
            formatted_value = value
            if isinstance(value, (int, float)) and value != 'N/A':
                if metric in ['Market Cap', 'Enterprise Value']:
                    formatted_value = f"${value:,.0f}"
                elif 'Ratio' in metric or metric in ['Beta', 'Price/Book', 'Price/Sales']:
                    formatted_value = f"{value:.2f}"
                elif '%' in metric or metric in ['Return on Equity', 'Return on Assets', 
                                               'Operating Margins', 'Profit Margins',
                                               'Revenue Growth', 'Earnings Growth',
                                               'Dividend Yield', 'Payout Ratio']:
                    formatted_value = f"{value:.2%}"
                elif metric in ['Dividend Rate']:
                    formatted_value = f"${value:.2f}"

            formatted_metrics.append({
                'Category': category,
                'Metric': metric,
                'Value': formatted_value
            })

    return pd.DataFrame(formatted_metrics)

def format_data_for_download(hist_data):
    """
    Format historical data for CSV download
    """
    df = hist_data.copy()
    df.index = df.index.strftime('%Y-%m-%d')
    df = df.round(2)
    return df