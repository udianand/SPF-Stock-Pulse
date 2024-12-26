import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from utils import get_stock_data, get_key_metrics, format_data_for_download, get_news_sentiment
import io
from plotly.subplots import make_subplots
from strategy_simulator import InvestmentStrategy

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
Enter stock symbols to analyze and compare.
""")

# Sidebar inputs
with st.sidebar:
    st.header("Configuration")
    # Multiple stock selection
    symbols_input = st.text_input("Enter Stock Symbols (comma-separated)", value="AAPL,MSFT").upper()
    symbols = [sym.strip() for sym in symbols_input.split(',')][:2]  # Limit to 2 stocks for better visualization

    # Date range selector
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input("Start Date", value=start_date)
    with date_col2:
        end_date = st.date_input("End Date", value=end_date)

# Main content
if symbols:
    # Create tabs for different analysis views
    tab1, tab2, tab3 = st.tabs(["Individual Analysis", "Comparison Analysis", "Strategy Simulator"])

    with tab1:
        # Individual stock analysis
        for symbol in symbols:
            st.header(f"Analysis for {symbol}")
            hist_data, stock_info = get_stock_data(symbol, start_date, end_date)

            if hist_data is not None and stock_info is not None:
                # Stock info header
                st.subheader(f"{stock_info.get('longName', symbol)} ({symbol})")
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
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True, key=f"price_chart_{symbol}")

                # Sentiment Analysis Section
                st.subheader("News Sentiment Analysis")
                news_df, overall_sentiment, timeline_df = get_news_sentiment(symbol)

                if not news_df.empty:
                    # Display overall sentiment
                    sentiment_color = "green" if overall_sentiment > 0 else "red" if overall_sentiment < 0 else "gray"
                    st.markdown(f"### Overall Sentiment Score: <span style='color:{sentiment_color}'>{overall_sentiment:.2f}</span>", unsafe_allow_html=True)

                    # Sentiment Timeline
                    fig_timeline = go.Figure()
                    fig_timeline.add_trace(go.Scatter(
                        x=timeline_df['Timestamp'],
                        y=timeline_df['Sentiment'],
                        mode='markers',
                        name='Individual Sentiment',
                        marker=dict(
                            size=8,
                            color=timeline_df['Sentiment'].apply(
                                lambda x: 'green' if x > 0 else 'red' if x < 0 else 'gray'
                            )
                        )
                    ))
                    fig_timeline.add_trace(go.Scatter(
                        x=timeline_df['Timestamp'],
                        y=timeline_df['Cumulative Sentiment'],
                        mode='lines',
                        name='Cumulative Average Sentiment',
                        line=dict(color='blue', width=2)
                    ))
                    fig_timeline.update_layout(
                        title="News Sentiment Timeline",
                        xaxis_title="Date",
                        yaxis_title="Sentiment Score",
                        template='plotly_white',
                        height=300
                    )
                    st.plotly_chart(fig_timeline, use_container_width=True, key=f"sentiment_timeline_{symbol}")
                else:
                    st.warning("No recent news available for sentiment analysis.")

                st.divider()

    with tab2:
        if len(symbols) >= 2:
            st.header("Stock Comparison Analysis")

            # Fetch data for both stocks
            stock_data = {}
            sentiments = {}

            for symbol in symbols:
                hist_data, stock_info = get_stock_data(symbol, start_date, end_date)
                news_df, overall_sentiment, timeline_df = get_news_sentiment(symbol)

                if hist_data is not None and stock_info is not None:
                    stock_data[symbol] = {
                        'hist_data': hist_data,
                        'info': stock_info
                    }
                    sentiments[symbol] = {
                        'overall': overall_sentiment,
                        'timeline': timeline_df
                    }

            if len(stock_data) >= 2:
                # Price Comparison Chart
                st.subheader("Price Performance Comparison")
                fig = go.Figure()

                for symbol in symbols:
                    hist_data = stock_data[symbol]['hist_data']
                    # Normalize prices to percentage change from start
                    normalized_prices = (hist_data['Close'] / hist_data['Close'].iloc[0] - 1) * 100

                    fig.add_trace(go.Scatter(
                        x=hist_data.index,
                        y=normalized_prices,
                        name=symbol,
                        mode='lines'
                    ))

                fig.update_layout(
                    title="Relative Price Performance (%)",
                    yaxis_title='Price Change (%)',
                    xaxis_title='Date',
                    template='plotly_white',
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True, key="price_comparison")

                # Sentiment Comparison
                st.subheader("Sentiment Analysis Comparison")

                # Create side-by-side sentiment timeline comparison
                fig = make_subplots(rows=len(symbols), cols=1,
                                    subplot_titles=[f"{sym} Sentiment Timeline" for sym in symbols],
                                    vertical_spacing=0.1)

                for i, symbol in enumerate(symbols, 1):
                    if symbol in sentiments and not sentiments[symbol]['timeline'].empty:
                        timeline_df = sentiments[symbol]['timeline']

                        # Add sentiment points
                        fig.add_trace(
                            go.Scatter(
                                x=timeline_df['Timestamp'],
                                y=timeline_df['Sentiment'],
                                mode='markers',
                                name=f'{symbol} Sentiment',
                                marker=dict(
                                    size=8,
                                    color=timeline_df['Sentiment'].apply(
                                        lambda x: 'green' if x > 0 else 'red' if x < 0 else 'gray'
                                    )
                                )
                            ),
                            row=i, col=1
                        )

                        # Add moving average line
                        fig.add_trace(
                            go.Scatter(
                                x=timeline_df['Timestamp'],
                                y=timeline_df['Cumulative Sentiment'],
                                mode='lines',
                                name=f'{symbol} Trend',
                                line=dict(color='blue', width=2)
                            ),
                            row=i, col=1
                        )

                fig.update_layout(
                    height=600,
                    showlegend=True,
                    template='plotly_white'
                )
                st.plotly_chart(fig, use_container_width=True, key="sentiment_comparison")

                # Metrics Comparison
                st.subheader("Key Metrics Comparison")

                metrics_comparison = []
                for symbol in symbols:
                    metrics_df = get_key_metrics(stock_data[symbol]['info'])
                    metrics_comparison.append(metrics_df.set_index('Metric')['Value'].rename(symbol))

                comparison_df = pd.concat(metrics_comparison, axis=1)
                st.table(comparison_df)

            else:
                st.error("Could not fetch data for both stocks. Please check the symbols.")
        else:
            st.info("Please enter at least two stock symbols for comparison analysis.")
    with tab3:
        if len(symbols) > 0:
            st.header("Investment Strategy Simulator")

            # Simulation parameters
            st.subheader("Simulation Parameters")
            col1, col2 = st.columns(2)
            with col1:
                initial_capital = st.number_input("Initial Capital ($)", 
                                               min_value=1000.0, 
                                               value=10000.0, 
                                               step=1000.0)

            # Run simulation button
            if st.button("Run Simulation", key="run_sim"):
                # Get data for the selected stock
                symbol = symbols[0]  # Use first selected stock
                hist_data, _ = get_stock_data(symbol, start_date, end_date)
                _, _, sentiment_data = get_news_sentiment(symbol)

                if hist_data is not None and not sentiment_data.empty:
                    # Calculate technical indicators
                    hist_data['SMA_20'] = hist_data['Close'].rolling(window=20).mean()
                    hist_data['SMA_50'] = hist_data['Close'].rolling(window=50).mean()

                    # Run simulation
                    strategy = InvestmentStrategy(initial_capital=initial_capital)
                    results = strategy.simulate(hist_data, sentiment_data)

                    # Display results
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Final Portfolio Value", 
                              f"${results['final_value']:,.2f}")
                    col2.metric("Total Return", 
                              results['total_return_pct'])
                    col3.metric("Sharpe Ratio", 
                              f"{results['sharpe_ratio']:.2f}")

                    # Portfolio value chart
                    st.subheader("Portfolio Value Over Time")
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=results['portfolio_history']['dates'],
                        y=results['portfolio_history']['values'],
                        name='Portfolio Value',
                        line=dict(color='blue')
                    ))
                    fig.add_trace(go.Scatter(
                        x=results['portfolio_history']['dates'],
                        y=results['portfolio_history']['cash'],
                        name='Cash',
                        line=dict(color='green', dash='dash')
                    ))
                    fig.update_layout(
                        title="Portfolio Performance",
                        xaxis_title="Date",
                        yaxis_title="Value ($)",
                        template='plotly_white',
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True, key="portfolio_performance")

                    # Trade history
                    st.subheader("Trade History")
                    trades_df = pd.DataFrame(results['trades'])
                    if not trades_df.empty:
                        trades_df['profit'] = trades_df.apply(
                            lambda x: -x['value'] if x['type'] == 'buy' else x['value'],
                            axis=1
                        )
                        st.dataframe(trades_df[['date', 'type', 'shares', 'price', 'value']])
                    else:
                        st.info("No trades were executed during the simulation period.")

                    # Additional metrics
                    st.subheader("Risk Metrics")
                    metrics_df = pd.DataFrame({
                        'Metric': ['Initial Capital', 'Final Value', 'Total Return', 
                                  'Sharpe Ratio', 'Max Drawdown', 'Number of Trades'],
                        'Value': [f"${results['initial_capital']:,.2f}",
                                 f"${results['final_value']:,.2f}",
                                 results['total_return_pct'],
                                 f"{results['sharpe_ratio']:.2f}",
                                 results['max_drawdown_pct'],
                                 results['trades_count']]
                    })
                    st.table(metrics_df)
                else:
                    st.error("Could not fetch required data for simulation. Please check the selected stock and date range.")
        else:
            st.info("Please enter at least one stock symbol to run the strategy simulation.")

else:
    st.info("Please enter stock symbols to begin analysis.")