import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from utils import get_stock_data, format_data_for_download, get_fundamental_metrics
import io
from plotly.subplots import make_subplots
from prediction import StockPredictor
import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Page config
st.set_page_config(
    page_title="SPF Stock Pulse",
    page_icon="📈",
    layout="wide"
)

# Sidebar configuration
with st.sidebar:
    st.header("SPF Stock Pulse")
    # Stock selection
    symbols_input = st.text_input("Enter Stock Symbol", value="AAPL").upper()
    symbols = [symbols_input.strip()]

    # Date range selector
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input("Start Date", value=start_date)
    with date_col2:
        end_date = st.date_input("End Date", value=end_date)

def generate_pdf_report(symbol, hist_data, stock_info, metrics_df):
    """Generate PDF report for the stock analysis"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    story.append(Paragraph(f"Investment Analysis Report - {symbol}", title_style))
    story.append(Spacer(1, 12))

    # Company Info
    story.append(Paragraph(f"Company: {stock_info.get('longName', symbol)}", styles['Heading2']))
    story.append(Paragraph(f"Sector: {stock_info.get('sector', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"Industry: {stock_info.get('industry', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Current Price Info
    current_price = hist_data['Close'].iloc[-1]
    price_change = hist_data['Close'].iloc[-1] - hist_data['Close'].iloc[-2]
    price_change_pct = (price_change / hist_data['Close'].iloc[-2]) * 100

    story.append(Paragraph("Current Price Information", styles['Heading2']))
    price_data = [
        ["Metric", "Value"],
        ["Current Price", f"${current_price:.2f}"],
        ["Price Change", f"${price_change:.2f}"],
        ["Percentage Change", f"{price_change_pct:.2f}%"]
    ]
    price_table = Table(price_data)
    price_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(price_table)
    story.append(Spacer(1, 20))

    # Fundamental Analysis
    story.append(Paragraph("Fundamental Analysis", styles['Heading2']))
    for category in metrics_df['Category'].unique():
        story.append(Paragraph(category, styles['Heading3']))
        category_metrics = metrics_df[metrics_df['Category'] == category]

        metrics_data = [["Metric", "Value"]]
        for _, row in category_metrics.iterrows():
            metrics_data.append([row['Metric'], str(row['Value'])])

        metrics_table = Table(metrics_data)
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 12))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# Main content
if symbols:
    # Create tabs for different analysis views
    tab1, tab2 = st.tabs([
        "Investment Analysis",
        "Trend Prediction"
    ])

    with tab1:
        # Individual stock analysis
        symbol = symbols[0]
        st.header(f"Analysis for {symbol}")
        hist_data, stock_info = get_stock_data(symbol, start_date, end_date)

        if hist_data is not None and stock_info is not None:
            # Stock info header
            st.subheader(f"{stock_info.get('longName', symbol)} ({symbol})")
            st.markdown(f"**Sector:** {stock_info.get('sector', 'N/A')} | **Industry:** {stock_info.get('industry', 'N/A')}")

            # Current price metrics
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            current_price = hist_data['Close'].iloc[-1]
            price_change = hist_data['Close'].iloc[-1] - hist_data['Close'].iloc[-2]
            price_change_pct = (price_change / hist_data['Close'].iloc[-2]) * 100

            col1.metric("Current Price", f"${current_price:.2f}")
            col2.metric("Price Change", f"${price_change:.2f}")
            col3.metric("% Change", f"{price_change_pct:.2f}%")

            # Export PDF button
            with col4:
                metrics_df = get_fundamental_metrics(stock_info)
                if st.button("Export PDF"):
                    pdf_buffer = generate_pdf_report(symbol, hist_data, stock_info, metrics_df)
                    st.download_button(
                        label="Download Report",
                        data=pdf_buffer,
                        file_name=f"{symbol}_analysis_report.pdf",
                        mime="application/pdf"
                    )

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
            st.plotly_chart(fig, use_container_width=True)

            # Fundamental Analysis
            st.subheader("Fundamental Analysis Report")

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

    with tab2:
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
    st.info("Please enter a stock symbol to begin analysis.")