import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from utils import get_stock_data, get_key_metrics, format_data_for_download
import io

# Page config
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

# Title and description
st.title("📈 Stock Analysis Dashboard")
st.markdown("""
This dashboard provides financial analysis and historical data for stocks. 
Enter a stock symbol to get started.
""")

# Sidebar inputs
with st.sidebar:
    st.header("Configuration")
    symbol = st.text_input("Enter Stock Symbol", value="AAPL").upper()
    
    # Date range selector
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input("Start Date", value=start_date)
    with date_col2:
        end_date = st.date_input("End Date", value=end_date)

# Main content
if symbol:
    hist_data, stock_info = get_stock_data(symbol, start_date, end_date)
    
    if hist_data is not None and stock_info is not None:
        # Stock info header
        st.header(f"{stock_info.get('longName', symbol)} ({symbol})")
        st.markdown(f"**Sector:** {stock_info.get('sector', 'N/A')} | **Industry:** {stock_info.get('industry', 'N/A')}")
        
        # Current price metrics
        col1, col2, col3 = st.columns(3)
        current_price = hist_data['Close'].iloc[-1]
        price_change = hist_data['Close'].iloc[-1] - hist_data['Close'].iloc[-2]
        price_change_pct = (price_change / hist_data['Close'].iloc[-2]) * 100
        
        col1.metric("Current Price", f"${current_price:.2f}")
        col2.metric("Price Change", f"${price_change:.2f}")
        col3.metric("% Change", f"{price_change_pct:.2f}%")
        
        # Stock price chart
        st.subheader("Historical Price Chart")
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=hist_data.index,
            open=hist_data['Open'],
            high=hist_data['High'],
            low=hist_data['Low'],
            close=hist_data['Close'],
            name='OHLC'
        ))
        fig.update_layout(
            title=f"{symbol} Stock Price",
            yaxis_title='Price (USD)',
            xaxis_title='Date',
            template='plotly_white',
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Key metrics table
        st.subheader("Key Financial Metrics")
        metrics_df = get_key_metrics(stock_info)
        st.table(metrics_df.set_index('Metric'))
        
        # Download button for CSV
        st.subheader("Download Historical Data")
        csv_data = format_data_for_download(hist_data)
        
        buffer = io.BytesIO()
        csv_data.to_csv(buffer)
        buffer.seek(0)
        
        st.download_button(
            label="Download CSV",
            data=buffer,
            file_name=f"{symbol}_historical_data.csv",
            mime="text/csv"
        )
        
    else:
        st.error(f"Error: Could not fetch data for symbol {symbol}. Please check if the symbol is correct.")
else:
    st.info("Please enter a stock symbol to begin analysis.")
