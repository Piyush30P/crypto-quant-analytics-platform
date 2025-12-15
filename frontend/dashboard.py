"""
Crypto Analytics Platform - Main Dashboard
Real-time cryptocurrency analytics and pair trading visualization
"""
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Crypto Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-signal {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .warning-signal {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ffeeba;
    }
    .danger-signal {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    </style>
    """, unsafe_allow_html=True)


def check_api_health():
    """Check if API is available"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_statistics(symbol, timeframe="1m", limit=100, rolling_window=20):
    """Fetch statistics from API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/stats/{symbol}",
            params={
                "timeframe": timeframe,
                "limit": limit,
                "rolling_window": rolling_window
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching statistics: {e}")
        return None


def get_ohlc_data(symbol, timeframe="1m", limit=100):
    """Fetch OHLC data from API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/ohlc/{symbol}",
            params={"timeframe": timeframe, "limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching OHLC data: {e}")
        return None


def analyze_pair(symbol1, symbol2, timeframe="1m", rolling_window=20, limit=100):
    """Analyze trading pair"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/pairs/analyze",
            json={
                "symbol1": symbol1,
                "symbol2": symbol2,
                "timeframe": timeframe,
                "rolling_window": rolling_window,
                "limit": limit
            },
            timeout=15
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error analyzing pair: {e}")
        return None


def create_candlestick_chart(ohlc_data):
    """Create interactive candlestick chart"""
    if not ohlc_data or not ohlc_data.get('bars'):
        return None

    df = pd.DataFrame(ohlc_data['bars'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    fig = go.Figure(data=[go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name=ohlc_data['symbol']
    )])

    fig.update_layout(
        title=f"{ohlc_data['symbol']} - {ohlc_data['timeframe']} Candlestick Chart",
        xaxis_title="Time",
        yaxis_title="Price (USDT)",
        height=500,
        xaxis_rangeslider_visible=False,
        template="plotly_white"
    )

    return fig


def create_volume_chart(ohlc_data):
    """Create volume bar chart"""
    if not ohlc_data or not ohlc_data.get('bars'):
        return None

    df = pd.DataFrame(ohlc_data['bars'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Color bars based on price movement
    colors = ['red' if row['close'] < row['open'] else 'green'
              for _, row in df.iterrows()]

    fig = go.Figure(data=[go.Bar(
        x=df['timestamp'],
        y=df['volume'],
        marker_color=colors,
        name='Volume'
    )])

    fig.update_layout(
        title="Trading Volume",
        xaxis_title="Time",
        yaxis_title="Volume",
        height=250,
        template="plotly_white"
    )

    return fig


def create_zscore_gauge(zscore_value):
    """Create Z-score gauge chart"""
    if zscore_value is None:
        return None

    # Determine color based on Z-score
    if abs(zscore_value) > 2:
        color = "red"
    elif abs(zscore_value) > 1:
        color = "orange"
    else:
        color = "green"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=zscore_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Z-Score"},
        delta={'reference': 0},
        gauge={
            'axis': {'range': [-3, 3]},
            'bar': {'color': color},
            'steps': [
                {'range': [-3, -2], 'color': "lightcoral"},
                {'range': [-2, -1], 'color': "lightyellow"},
                {'range': [-1, 1], 'color': "lightgreen"},
                {'range': [1, 2], 'color': "lightyellow"},
                {'range': [2, 3], 'color': "lightcoral"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': zscore_value
            }
        }
    ))

    fig.update_layout(height=300)
    return fig


def display_statistics_cards(stats):
    """Display statistics as metric cards"""
    if not stats:
        return

    price_stats = stats.get('price_stats', {})
    volatility = stats.get('volatility', {})
    volume_stats = stats.get('volume_stats', {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Latest Price",
            value=f"${price_stats.get('latest', 0):,.2f}",
            delta=f"{price_stats.get('change_pct', 0):.2f}%"
        )

    with col2:
        st.metric(
            label="Mean Price",
            value=f"${price_stats.get('mean', 0):,.2f}",
            delta=f"±${price_stats.get('std', 0):.2f}"
        )

    with col3:
        vol = volatility.get('current')
        if vol and vol is not None:
            st.metric(
                label="Volatility",
                value=f"{vol*100:.4f}%",
                delta=f"Ann: {volatility.get('annualized', 0)*100:.2f}%"
            )
        else:
            st.metric(label="Volatility", value="N/A")

    with col4:
        latest_vol = volume_stats.get('latest') if volume_stats else None
        if latest_vol:
            st.metric(
                label="Latest Volume",
                value=f"{latest_vol:,.0f}",
                delta=f"Avg: {volume_stats.get('mean', 0):,.0f}"
            )
        else:
            st.metric(label="Latest Volume", value="N/A")


def display_pair_analysis(analysis):
    """Display pair trading analysis"""
    if not analysis:
        return

    st.subheader(f"📊 Pair Analysis: {analysis['symbol1']} vs {analysis['symbol2']}")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    correlation = analysis.get('correlation', {})
    hedge_ratio = analysis.get('hedge_ratio', {})
    cointegration = analysis.get('cointegration', {})
    zscore = analysis.get('zscore', {})

    with col1:
        pearson = correlation.get('pearson')
        if pearson is not None:
            st.metric(
                label="Pearson Correlation",
                value=f"{pearson:.4f}",
                delta=correlation.get('strength', 'N/A')
            )
        else:
            st.metric(label="Pearson Correlation", value="N/A")

    with col2:
        ratio = hedge_ratio.get('ratio')
        if ratio is not None:
            st.metric(
                label="Hedge Ratio",
                value=f"{ratio:.6f}",
                delta=f"R²: {hedge_ratio.get('r_squared', 0):.4f}"
            )
        else:
            st.metric(label="Hedge Ratio", value="N/A")

    with col3:
        if cointegration and cointegration.get('pvalue') is not None:
            st.metric(
                label="Cointegration",
                value=f"p={cointegration.get('pvalue', 0):.4f}",
                delta="✓" if cointegration.get('is_cointegrated_5pct') else "✗"
            )
        else:
            st.metric(label="Cointegration", value="N/A")

    with col4:
        zscore_val = zscore.get('current')
        if zscore_val is not None:
            st.metric(
                label="Z-Score",
                value=f"{zscore_val:.4f}",
                delta=zscore.get('signal', 'neutral')
            )
        else:
            st.metric(label="Z-Score", value="N/A")

    # Trading signal
    if zscore_val is not None:
        signal = zscore.get('signal', 'neutral')

        if 'long' in signal.lower():
            st.markdown(f"""
                <div class="success-signal">
                    <strong>🟢 LONG SIGNAL:</strong> {signal}
                    <br>The spread is below its mean - consider going long the spread.
                </div>
                """, unsafe_allow_html=True)
        elif 'short' in signal.lower():
            st.markdown(f"""
                <div class="danger-signal">
                    <strong>🔴 SHORT SIGNAL:</strong> {signal}
                    <br>The spread is above its mean - consider going short the spread.
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="warning-signal">
                    <strong>🟡 NEUTRAL:</strong> {signal}
                    <br>No strong signal - wait for better opportunity.
                </div>
                """, unsafe_allow_html=True)


def main():
    """Main dashboard application"""

    # Header
    st.markdown('<h1 class="main-header">📊 Crypto Analytics Platform</h1>', unsafe_allow_html=True)

    # Check API health
    if not check_api_health():
        st.error("⚠️ API is not available. Please start the API server:")
        st.code("python -m uvicorn backend.api.app:app --reload")
        return

    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")

    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["📈 Single Symbol Analysis", "🔄 Pair Trading Analysis", "📊 Multi-Symbol Dashboard"]
    )

    # Common settings
    st.sidebar.subheader("Settings")
    timeframe = st.sidebar.selectbox(
        "Timeframe",
        ["1s", "1m", "5m", "15m", "1h", "4h", "1d"],
        index=1
    )

    limit = st.sidebar.slider("Data Points", 10, 500, 100)
    rolling_window = st.sidebar.slider("Rolling Window", 5, 100, 20)

    auto_refresh = st.sidebar.checkbox("Auto Refresh (10s)")

    # Page routing
    if page == "📈 Single Symbol Analysis":
        show_single_symbol_page(timeframe, limit, rolling_window)
    elif page == "🔄 Pair Trading Analysis":
        show_pair_trading_page(timeframe, limit, rolling_window)
    else:
        show_multi_symbol_page(timeframe, limit, rolling_window)

    # Auto refresh
    if auto_refresh:
        time.sleep(10)
        st.rerun()


def show_single_symbol_page(timeframe, limit, rolling_window):
    """Single symbol analysis page"""
    st.header("📈 Single Symbol Analysis")

    # Symbol selection
    symbol = st.selectbox(
        "Select Symbol",
        ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"],
        key="single_symbol"
    )

    if st.button("Analyze", key="analyze_single"):
        with st.spinner("Fetching data..."):
            # Get statistics
            stats = get_statistics(symbol, timeframe, limit, rolling_window)

            if stats:
                # Display metrics
                display_statistics_cards(stats)

                # Get OHLC data for charts
                ohlc_data = get_ohlc_data(symbol, timeframe, limit)

                if ohlc_data:
                    # Candlestick chart
                    st.subheader("Price Chart")
                    fig_candle = create_candlestick_chart(ohlc_data)
                    if fig_candle:
                        st.plotly_chart(fig_candle, use_container_width=True)

                    # Volume chart
                    st.subheader("Volume")
                    fig_volume = create_volume_chart(ohlc_data)
                    if fig_volume:
                        st.plotly_chart(fig_volume, use_container_width=True)

                # Detailed statistics
                with st.expander("📊 Detailed Statistics"):
                    st.json(stats)
            else:
                st.warning("No data available. Run test_phase3.py to generate OHLC data.")


def show_pair_trading_page(timeframe, limit, rolling_window):
    """Pair trading analysis page"""
    st.header("🔄 Pair Trading Analysis")

    col1, col2 = st.columns(2)

    with col1:
        symbol1 = st.selectbox(
            "Symbol 1",
            ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"],
            key="pair_symbol1"
        )

    with col2:
        symbol2 = st.selectbox(
            "Symbol 2",
            ["ETHUSDT", "BTCUSDT", "BNBUSDT", "ADAUSDT"],
            index=0,
            key="pair_symbol2"
        )

    if st.button("Analyze Pair", key="analyze_pair"):
        if symbol1 == symbol2:
            st.error("Please select different symbols!")
            return

        with st.spinner("Analyzing pair..."):
            analysis = analyze_pair(symbol1, symbol2, timeframe, rolling_window, limit)

            if analysis:
                # Display analysis
                display_pair_analysis(analysis)

                # Z-score gauge
                zscore = analysis.get('zscore', {})
                zscore_val = zscore.get('current')

                if zscore_val is not None:
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        st.subheader("Z-Score Gauge")
                        fig_gauge = create_zscore_gauge(zscore_val)
                        if fig_gauge:
                            st.plotly_chart(fig_gauge, use_container_width=True)

                    with col2:
                        st.subheader("Trading Strategy")
                        st.markdown("""
                        **Z-Score Interpretation:**
                        - **Z < -2**: Strong long signal (spread undervalued)
                        - **-2 < Z < -1**: Moderate long signal
                        - **-1 < Z < 1**: Neutral zone (no trade)
                        - **1 < Z < 2**: Moderate short signal
                        - **Z > 2**: Strong short signal (spread overvalued)

                        **Mean Reversion Strategy:**
                        - Long the spread when Z-score is very negative
                        - Short the spread when Z-score is very positive
                        - Exit when Z-score returns to zero
                        """)

                # Detailed results
                with st.expander("📊 Detailed Analysis Results"):
                    st.json(analysis)
            else:
                st.warning("No data available. Run test_phase3.py to generate OHLC data.")


def show_multi_symbol_page(timeframe, limit, rolling_window):
    """Multi-symbol dashboard page"""
    st.header("📊 Multi-Symbol Dashboard")

    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

    if st.button("Refresh All", key="refresh_multi"):
        for symbol in symbols:
            with st.container():
                st.subheader(f"💹 {symbol}")

                stats = get_statistics(symbol, timeframe, min(50, limit), rolling_window)

                if stats:
                    price_stats = stats.get('price_stats', {})

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            f"{symbol} Price",
                            f"${price_stats.get('latest', 0):,.2f}",
                            f"{price_stats.get('change_pct', 0):.2f}%"
                        )

                    with col2:
                        volatility = stats.get('volatility', {})
                        vol = volatility.get('current')
                        if vol:
                            st.metric(
                                "Volatility",
                                f"{vol*100:.4f}%"
                            )

                    with col3:
                        volume_stats = stats.get('volume_stats', {})
                        if volume_stats:
                            st.metric(
                                "Volume",
                                f"{volume_stats.get('latest', 0):,.0f}"
                            )

                st.divider()


if __name__ == "__main__":
    main()
