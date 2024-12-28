import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from textblob import TextBlob
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

def get_news_sentiment(symbol):
    """
    Fetch news and perform sentiment analysis with timeline data
    """
    try:
        stock = yf.Ticker(symbol)
        news = stock.news

        if not news:
            return pd.DataFrame(), 0, pd.DataFrame()

        # Process each news item
        processed_news = []
        for item in news:  # Process all available news items
            title = item.get('title', '')
            timestamp = item.get('providerPublishTime', 0)
            # Convert timestamp to timezone-naive datetime
            date = pd.to_datetime(datetime.fromtimestamp(timestamp)).tz_localize(None)
            blob = TextBlob(title)
            sentiment = blob.sentiment.polarity

            processed_news.append({
                'Timestamp': date,
                'Date': date.strftime('%Y-%m-%d'),
                'Time': date.strftime('%H:%M:%S'),
                'Title': title,
                'Sentiment': sentiment,
                'Sentiment Label': 'Positive' if sentiment > 0 else 'Negative' if sentiment < 0 else 'Neutral'
            })

        # Create DataFrame and sort by timestamp
        news_df = pd.DataFrame(processed_news)
        if not news_df.empty:
            news_df = news_df.sort_values('Timestamp')

            # Calculate overall sentiment
            overall_sentiment = news_df['Sentiment'].mean()

            # Create timeline data
            timeline_df = news_df.copy()
            # Ensure timezone-naive datetime index
            timeline_df.set_index('Timestamp', inplace=True)
            timeline_df.index = timeline_df.index.tz_localize(None)
            timeline_df['Cumulative Sentiment'] = timeline_df['Sentiment'].expanding().mean()

            return news_df, overall_sentiment, timeline_df

        return pd.DataFrame(), 0, pd.DataFrame()
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return pd.DataFrame(), 0, pd.DataFrame()