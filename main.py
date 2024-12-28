import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from utils import get_stock_data, format_data_for_download, get_fundamental_metrics
import io
from plotly.subplots import make_subplots
from strategy_simulator import InvestmentStrategy
from prediction import StockPredictor

# Page config
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

# Sidebar configuration
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
    tab1, tab2, tab3, tab4 = st.tabs([
        "Individual Analysis", 
        "Comparison Analysis", 
        "Strategy Simulator",
        "Trend Prediction"
    ])

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

                # Replace Morningstar section with Fundamental Analysis
                st.subheader("Fundamental Analysis Report")

                metrics_df = get_fundamental_metrics(stock_info)
                if not metrics_df.empty:
                    # Display metrics by category
                    for category in metrics_df['Category'].unique():
                        st.markdown(f"### {category}")
                        category_metrics = metrics_df[metrics_df['Category'] == category]

                        # Create columns for metrics display
                        cols = st.columns(2)
                        for i, (_, row) in enumerate(category_metrics.iterrows()):
                            col_idx = i % 2
                            with cols[col_idx]:
                                st.metric(
                                    label=row['Metric'],
                                    value=row['Value']
                                )

                        st.divider()
                else:
                    st.warning("Unable to fetch detailed metrics for this stock.")

                st.divider()

    with tab2:
        if len(symbols) >= 2:
            st.header("Stock Comparison Analysis")

            # Fetch data for both stocks
            stock_data = {}

            for symbol in symbols:
                hist_data, stock_info = get_stock_data(symbol, start_date, end_date)

                if hist_data is not None and stock_info is not None:
                    stock_data[symbol] = {
                        'hist_data': hist_data,
                        'info': stock_info
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

                # Update the comparison section header
                st.subheader("Fundamental Metrics Comparison")
                metrics_comparison = []
                for symbol in symbols:
                    metrics_df = get_fundamental_metrics(stock_data[symbol]['info'])
                    if not metrics_df.empty:
                        # Pivot the metrics for side-by-side comparison
                        symbol_metrics = metrics_df.set_index(['Category', 'Metric'])['Value']
                        metrics_comparison.append(symbol_metrics.rename(symbol))

                if metrics_comparison:
                    comparison_df = pd.concat(metrics_comparison, axis=1)
                    # Display metrics by category
                    for category in metrics_df['Category'].unique():
                        st.markdown(f"### {category}")
                        category_metrics = comparison_df.loc[category]
                        st.dataframe(category_metrics, use_container_width=True)
                        st.divider()
                else:
                    st.warning("Unable to fetch comparison metrics for the selected stocks.")

            else:
                st.error("Could not fetch data for both stocks. Please check the symbols.")
        else:
            st.info("Please enter at least two stock symbols for comparison analysis.")

    with tab3:
        if len(symbols) > 0:
            st.header("Investment Strategy Simulator")

            # Simulation parameters
            st.subheader("Simulation Parameters")
            col1, col2, col3 = st.columns(3)
            with col1:
                initial_capital = st.number_input("Initial Capital ($)", 
                                               min_value=1000.0, 
                                               value=10000.0, 
                                               step=1000.0)
            with col2:
                strategy_type = st.selectbox(
                    "Trading Strategy",
                    options=['ma_crossover', 'rsi', 'macd'],
                    help="""
                    MA Crossover: Uses 20 and 50-day moving averages
                    RSI: Uses Relative Strength Index
                    MACD: Uses Moving Average Convergence Divergence
                    """
                )
            with col3:
                risk_per_trade = st.slider(
                    "Risk per Trade (%)",
                    min_value=1.0,
                    max_value=5.0,
                    value=2.0,
                    step=0.5,
                    help="Maximum risk per trade as percentage of portfolio"
                ) / 100

            # Run simulation button
            if st.button("Run Simulation", key="run_sim"):
                # Get data for the selected stock
                symbol = symbols[0]  # Use first selected stock
                hist_data, _ = get_stock_data(symbol, start_date, end_date)

                if hist_data is not None:
                    # Run simulation
                    strategy = InvestmentStrategy(initial_capital=initial_capital)
                    results = strategy.simulate(hist_data, strategy_type, risk_per_trade)

                    # Display results
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Final Portfolio Value", 
                               f"${results['final_value']:,.2f}")
                    col2.metric("Total Return", 
                               results['total_return_pct'])
                    col3.metric("Sharpe Ratio", 
                               f"{results['sharpe_ratio']:.2f}")
                    col4.metric("Win Rate",
                               results['win_rate'])

                    # Portfolio value chart
                    st.subheader("Portfolio Performance")
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
                        title="Portfolio Value Over Time",
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
                        st.dataframe(
                            trades_df[['date', 'type', 'shares', 'price', 'value']],
                            use_container_width=True
                        )
                    else:
                        st.info("No trades were executed during the simulation period.")

                    # Risk metrics
                    st.subheader("Risk & Performance Metrics")
                    metrics_df = pd.DataFrame({
                        'Metric': ['Initial Capital', 'Final Value', 'Total Return', 
                                 'Sharpe Ratio', 'Max Drawdown', 'Win Rate', 'Number of Trades'],
                        'Value': [f"${results['initial_capital']:,.2f}",
                                 f"${results['final_value']:,.2f}",
                                 results['total_return_pct'],
                                 f"{results['sharpe_ratio']:.2f}",
                                 results['max_drawdown_pct'],
                                 results['win_rate'],
                                 results['trades_count']]
                    })
                    st.table(metrics_df)

                    # Strategy explanation
                    st.subheader("Strategy Explanation")
                    strategy_explanations = {
                        'ma_crossover': """
                        The Moving Average Crossover strategy uses 20 and 50-day moving averages to generate trading signals.
                        - Buy when the 20-day MA crosses above the 50-day MA
                        - Sell when the 20-day MA crosses below the 50-day MA
                        Signal strength is adjusted based on the distance between moving averages.
                        """,
                        'rsi': """
                        The Relative Strength Index (RSI) strategy uses overbought and oversold levels to generate trading signals.
                        - Buy when RSI drops below 30 (oversold)
                        - Sell when RSI rises above 70 (overbought)
                        """,
                        'macd': """
                        The Moving Average Convergence Divergence (MACD) strategy uses the MACD line and signal line crossovers.
                        - Buy when MACD crosses above the signal line
                        - Sell when MACD crosses below the signal line
                        Signal strength is adjusted based on the momentum of the crossover.
                        """
                    }
                    st.markdown(strategy_explanations[strategy_type])

                else:
                    st.error("Could not fetch required data for simulation. Please check the selected stock and date range.")
        else:
            st.info("Please enter at least one stock symbol to run the strategy simulation.")

    with tab4:
        if len(symbols) > 0:
            st.header("Stock Trend Prediction")

            # Select stock for prediction
            symbol = st.selectbox(
                "Select Stock for Prediction",
                options=symbols,
                key="predict_stock"
            )

            # Get data for selected stock
            hist_data, _ = get_stock_data(symbol, start_date, end_date)

            if hist_data is not None:
                predictor = StockPredictor()

                # Train model and show metrics
                with st.spinner("Training prediction model..."):
                    metrics = predictor.train(hist_data)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Training Score",
                            f"{metrics['train_score']:.2%}"
                        )
                    with col2:
                        st.metric(
                            "Testing Score",
                            f"{metrics['test_score']:.2%}"
                        )

                # Make prediction
                prediction = predictor.predict_next_day(hist_data)

                # Display prediction results
                st.subheader("Price Prediction")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Current Price",
                        f"${prediction['current_price']:.2f}"
                    )
                with col2:
                    st.metric(
                        "Predicted Price",
                        f"${prediction['predicted_price']:.2f}"
                    )
                with col3:
                    st.metric(
                        "Predicted Change",
                        f"{prediction['predicted_change_percent']:.2f}%",
                        delta=f"{prediction['predicted_change_percent']:.2f}%"
                    )

                # Feature importance
                st.subheader("Feature Importance")
                importance_df = pd.DataFrame(
                    sorted(metrics['feature_importance'].items(),
                          key=lambda x: x[1],
                          reverse=True),
                    columns=['Feature', 'Importance']
                )

                fig = go.Figure(go.Bar(
                    x=importance_df['Feature'],
                    y=importance_df['Importance'],
                    text=importance_df['Importance'].round(3),
                    textposition='auto',
                ))

                fig.update_layout(
                    title="Feature Importance in Prediction",
                    xaxis_title="Features",
                    yaxis_title="Importance Score",
                    template='plotly_white',
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

                # Disclaimer
                st.warning("""
                    **Disclaimer:** This prediction is based on historical data and technical analysis.
                    It should not be used as the sole basis for investment decisions.
                    Past performance does not guarantee future results.
                """)
            else:
                st.error("Could not fetch required data for prediction. Please check the selected stock and date range.")
        else:
            st.info("Please enter at least one stock symbol to run the prediction model.")

else:
    st.info("Please enter stock symbols to begin analysis.")