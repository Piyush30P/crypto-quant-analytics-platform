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
import io

# Page configuration
st.set_page_config(
    page_title="Crypto Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Enhanced Custom CSS for professional styling
st.markdown("""
    <style>
    /* Main Header Styling */
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem 0;
    }

    /* Enhanced Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* Trading Signal Cards */
    .success-signal {
        background: linear-gradient(135deg, #d4edda 0%, #a8e6cf 100%);
        color: #155724;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #28a745;
        box-shadow: 0 4px 12px rgba(40, 167, 69, 0.2);
        font-size: 1.1rem;
        font-weight: 600;
    }

    .warning-signal {
        background: linear-gradient(135deg, #fff3cd 0%, #ffe599 100%);
        color: #856404;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #ffc107;
        box-shadow: 0 4px 12px rgba(255, 193, 7, 0.2);
        font-size: 1.1rem;
        font-weight: 600;
    }

    .danger-signal {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        color: #721c24;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #dc3545;
        box-shadow: 0 4px 12px rgba(220, 53, 69, 0.2);
        font-size: 1.1rem;
        font-weight: 600;
    }

    /* Section Headers */
    .section-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2c3e50;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
    }

    /* Stats Box */
    .stats-box {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }

    /* Price Display */
    .price-display {
        font-size: 2.5rem;
        font-weight: 800;
        color: #2c3e50;
    }

    .price-change-positive {
        color: #28a745;
        font-size: 1.2rem;
        font-weight: 600;
    }

    .price-change-negative {
        color: #dc3545;
        font-size: 1.2rem;
        font-weight: 600;
    }

    /* Custom Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        transition: all 0.3s;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
    }

    /* Download Button Styling */
    .stDownloadButton>button {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
    }

    /* Info Cards */
    .info-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }

    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }

    /* Divider Enhancement */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
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


def get_alert_history(limit=100):
    """Fetch alert history from API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/alerts/history",
            params={"limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching alert history: {e}")
        return []


def upload_ohlc_csv(symbol, timeframe, csv_file):
    """Upload OHLC CSV data to API"""
    try:
        files = {'file': csv_file}
        data = {
            'symbol': symbol,
            'timeframe': timeframe
        }
        response = requests.post(
            f"{API_BASE_URL}/api/upload/ohlc",
            files=files,
            data=data,
            timeout=30
        )
        return response.status_code == 200, response.json() if response.status_code == 200 else {"error": response.text}
    except Exception as e:
        return False, {"error": str(e)}


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


def create_candlestick_chart(ohlc_data, show_indicators=True):
    """Create enhanced interactive candlestick chart with volume subplot (following reference design)"""
    if not ohlc_data or not ohlc_data.get('bars'):
        return None

    df = pd.DataFrame(ohlc_data['bars'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Sort by timestamp to ensure chronological order
    df = df.sort_values('timestamp')

    # Calculate technical indicators
    if show_indicators and len(df) >= 20:
        # Simple Moving Average (SMA) - 20 periods
        df['SMA_20'] = df['close'].rolling(window=20).mean()

        # Exponential Moving Average (EMA) - 20 periods
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()

    # Create subplots: candlestick chart (row 1, 70%) and volume chart (row 2, 30%)
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(f"{ohlc_data['symbol']} - {ohlc_data['timeframe']} Price Chart", "Trading Volume")
    )

    # Add candlestick to row 1
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=ohlc_data['symbol'],
            increasing=dict(line=dict(color='#26a69a', width=1.5), fillcolor='#26a69a'),
            decreasing=dict(line=dict(color='#ef5350', width=1.5), fillcolor='#ef5350'),
            showlegend=True
        ),
        row=1, col=1
    )

    # Add SMA line to row 1
    if show_indicators and 'SMA_20' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['SMA_20'],
                mode='lines',
                name='SMA (20)',
                line=dict(color='#2196F3', width=2),
                hovertemplate='<b>SMA (20):</b> $%{y:.2f}<extra></extra>',
                showlegend=True
            ),
            row=1, col=1
        )

    # Add EMA line to row 1
    if show_indicators and 'EMA_20' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['EMA_20'],
                mode='lines',
                name='EMA (20)',
                line=dict(color='#FF9800', width=2, dash='dash'),
                hovertemplate='<b>EMA (20):</b> $%{y:.2f}<extra></extra>',
                showlegend=True
            ),
            row=1, col=1
        )

    # Add volume bars to row 2 (colored based on price direction)
    colors = ['#ef5350' if row['close'] < row['open'] else '#26a69a'
              for _, row in df.iterrows()]

    fig.add_trace(
        go.Bar(
            x=df['timestamp'],
            y=df['volume'],
            marker_color=colors,
            name='Volume',
            showlegend=False,
            hovertemplate='<b>Volume:</b> %{y:,.2f}<extra></extra>'
        ),
        row=2, col=1
    )

    # Update layout
    fig.update_layout(
        height=800,
        template="plotly_white",
        hovermode='x unified',
        plot_bgcolor='rgba(240, 242, 246, 0.5)',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12),
        margin=dict(l=60, r=30, t=80, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1
        ),
        xaxis_rangeslider_visible=False
    )

    # Update x-axis and y-axis styling
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',
        showline=True,
        linewidth=2,
        linecolor='rgba(128, 128, 128, 0.3)',
        row=2, col=1
    )

    fig.update_yaxes(
        title_text="Price (USDT)",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',
        showline=True,
        linewidth=2,
        linecolor='rgba(128, 128, 128, 0.3)',
        row=1, col=1
    )

    fig.update_yaxes(
        title_text="Volume",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',
        showline=True,
        linewidth=2,
        linecolor='rgba(128, 128, 128, 0.3)',
        row=2, col=1
    )

    return fig


def create_volume_chart(ohlc_data):
    """Create enhanced volume bar chart"""
    if not ohlc_data or not ohlc_data.get('bars'):
        return None

    df = pd.DataFrame(ohlc_data['bars'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Color bars based on price movement (green for up, red for down)
    colors = ['#ef5350' if row['close'] < row['open'] else '#26a69a'
              for _, row in df.iterrows()]

    fig = go.Figure(data=[go.Bar(
        x=df['timestamp'],
        y=df['volume'],
        marker_color=colors,
        name='Volume',
        hovertemplate='<b>Time:</b> %{x}<br><b>Volume:</b> %{y:,.2f}<extra></extra>'
    )])

    fig.update_layout(
        title={
            'text': "<b>Trading Volume</b>",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=18, color='#2c3e50')
        },
        xaxis_title="Time",
        yaxis_title="Volume",
        height=280,
        template="plotly_white",
        hovermode='x unified',
        plot_bgcolor='rgba(240, 242, 246, 0.5)',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showline=True,
            linewidth=2,
            linecolor='rgba(128, 128, 128, 0.3)'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)',
            showline=True,
            linewidth=2,
            linecolor='rgba(128, 128, 128, 0.3)'
        ),
        margin=dict(l=60, r=60, t=60, b=60),
        showlegend=False
    )

    return fig


def create_zscore_gauge(zscore_value):
    """Create enhanced Z-score gauge chart"""
    if zscore_value is None:
        return None

    # Determine color based on Z-score
    if abs(zscore_value) > 2:
        color = "#ef5350"  # Strong signal - red
    elif abs(zscore_value) > 1:
        color = "#ffa726"  # Moderate signal - orange
    else:
        color = "#26a69a"  # Neutral - green

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=zscore_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={
            'text': "<b>Z-Score Analysis</b>",
            'font': {'size': 22, 'color': '#2c3e50'}
        },
        delta={'reference': 0, 'font': {'size': 16}},
        number={'font': {'size': 48, 'color': color}},
        gauge={
            'axis': {
                'range': [-3, 3],
                'tickwidth': 2,
                'tickcolor': "#2c3e50",
                'tickfont': {'size': 14}
            },
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#e0e0e0",
            'steps': [
                {'range': [-3, -2], 'color': "rgba(239, 83, 80, 0.2)"},
                {'range': [-2, -1], 'color': "rgba(255, 193, 7, 0.2)"},
                {'range': [-1, 1], 'color': "rgba(38, 166, 154, 0.2)"},
                {'range': [1, 2], 'color': "rgba(255, 193, 7, 0.2)"},
                {'range': [2, 3], 'color': "rgba(239, 83, 80, 0.2)"}
            ],
            'threshold': {
                'line': {'color': color, 'width': 5},
                'thickness': 0.85,
                'value': zscore_value
            }
        }
    ))

    fig.update_layout(
        height=350,
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif"),
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return fig


def calculate_market_sentiment(df):
    """Calculate market sentiment based on technical indicators"""
    if len(df) < 20:
        return "Insufficient Data", "gray"

    # Calculate indicators
    sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
    ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
    current_price = df['close'].iloc[-1]

    # Volume trend
    recent_volume = df['volume'].tail(5).mean()
    avg_volume = df['volume'].mean()

    # Price momentum
    price_change_pct = ((current_price - df['close'].iloc[0]) / df['close'].iloc[0]) * 100

    # Sentiment logic
    bullish_signals = 0
    bearish_signals = 0

    if current_price > sma_20:
        bullish_signals += 1
    else:
        bearish_signals += 1

    if current_price > ema_20:
        bullish_signals += 1
    else:
        bearish_signals += 1

    if price_change_pct > 2:
        bullish_signals += 1
    elif price_change_pct < -2:
        bearish_signals += 1

    if recent_volume > avg_volume * 1.2:
        bullish_signals += 1

    # Determine sentiment
    if bullish_signals > bearish_signals + 1:
        return "🟢 Bullish", "#28a745"
    elif bearish_signals > bullish_signals + 1:
        return "🔴 Bearish", "#dc3545"
    else:
        return "🟡 Neutral", "#ffc107"


def simple_price_forecast(df, periods=5):
    """Simple price forecast using EMA trend"""
    if len(df) < 20:
        return None

    # Calculate EMA
    ema_20 = df['close'].ewm(span=20, adjust=False).mean()

    # Calculate trend (slope of recent EMA)
    recent_ema = ema_20.tail(10).values
    x = list(range(len(recent_ema)))

    # Simple linear trend
    if len(recent_ema) >= 2:
        slope = (recent_ema[-1] - recent_ema[0]) / len(recent_ema)

        # Forecast future prices
        last_price = df['close'].iloc[-1]
        forecast = []
        for i in range(1, periods + 1):
            predicted_price = last_price + (slope * i)
            forecast.append(predicted_price)

        return forecast
    return None


def display_statistics_cards(stats):
    """Display enhanced statistics as professional metric cards"""
    if not stats:
        return

    price_stats = stats.get('price_stats', {})
    volatility = stats.get('volatility', {})
    volume_stats = stats.get('volume_stats', {})
    returns = stats.get('returns', {})

    # Row 1: Price and Volume Metrics
    st.markdown("### 💰 Price & Volume Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        latest_price = price_stats.get('latest', 0)
        change_pct = price_stats.get('change_pct', 0)
        st.metric(
            label="💵 Current Price",
            value=f"${latest_price:,.2f}",
            delta=f"{change_pct:.2f}%",
            delta_color="normal"
        )

    with col2:
        mean_price = price_stats.get('mean', 0)
        std_price = price_stats.get('std', 0)
        st.metric(
            label="📊 Mean Price",
            value=f"${mean_price:,.2f}",
            delta=f"Std: ${std_price:.2f}",
            delta_color="off"
        )

    with col3:
        high_price = price_stats.get('high', 0)
        low_price = price_stats.get('low', 0)
        st.metric(
            label="📈 24h High",
            value=f"${high_price:,.2f}",
            delta=f"Low: ${low_price:,.2f}",
            delta_color="off"
        )

    with col4:
        latest_vol = volume_stats.get('latest', 0) if volume_stats else 0
        mean_vol = volume_stats.get('mean', 0) if volume_stats else 0
        vol_change = ((latest_vol / mean_vol - 1) * 100) if mean_vol > 0 else 0
        st.metric(
            label="📦 Volume",
            value=f"{latest_vol:,.0f}",
            delta=f"{vol_change:+.1f}% vs avg"
        )

    st.markdown("---")

    # Row 2: Technical Indicators
    st.markdown("### 📉 Technical & Historical Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        vol = volatility.get('current')
        ann_vol = volatility.get('annualized', 0)
        if vol and vol is not None:
            st.metric(
                label="📊 Volatility",
                value=f"{vol*100:.3f}%",
                delta=f"Ann: {ann_vol*100:.2f}%",
                delta_color="off"
            )
        else:
            st.metric(label="📊 Volatility", value="N/A")

    with col2:
        mean_return = returns.get('mean', 0) if returns and 'error' not in returns else 0
        st.metric(
            label="💹 Mean Return",
            value=f"{mean_return*100:.4f}%",
            delta_color="normal"
        )

    with col3:
        sharpe = returns.get('sharpe_ratio') if returns and 'error' not in returns else None
        if sharpe is not None:
            st.metric(
                label="📈 Sharpe Ratio",
                value=f"{sharpe:.3f}",
                delta="Higher is better",
                delta_color="off"
            )
        else:
            st.metric(label="📈 Sharpe Ratio", value="N/A")

    with col4:
        vwap_val = stats.get('vwap', {}).get('value', 0) if stats.get('vwap') else 0
        if vwap_val > 0:
            vwap_diff_pct = ((latest_price / vwap_val - 1) * 100) if vwap_val > 0 else 0
            st.metric(
                label="⚖️ VWAP",
                value=f"${vwap_val:,.2f}",
                delta=f"{vwap_diff_pct:+.2f}% from price"
            )
        else:
            st.metric(label="⚖️ VWAP", value="N/A")


def display_pair_analysis(analysis):
    """Display enhanced pair trading analysis"""
    if not analysis:
        return

    st.markdown(f"## 🔄 Pair Trading Analysis: {analysis['symbol1']} vs {analysis['symbol2']}")

    correlation = analysis.get('correlation', {})
    hedge_ratio = analysis.get('hedge_ratio', {})
    cointegration = analysis.get('cointegration', {})
    zscore = analysis.get('zscore', {})
    spread = analysis.get('spread', {})

    # Row 1: Correlation & Regression Metrics
    st.markdown("### 📊 Correlation & Regression Analysis")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        pearson = correlation.get('pearson')
        strength = correlation.get('strength', 'N/A')
        if pearson is not None:
            # Color based on correlation strength
            correlation_emoji = "🟢" if abs(pearson) > 0.7 else "🟡" if abs(pearson) > 0.4 else "🔴"
            st.metric(
                label=f"{correlation_emoji} Pearson Correlation",
                value=f"{pearson:.4f}",
                delta=f"Strength: {strength}",
                delta_color="off"
            )
        else:
            st.metric(label="Pearson Correlation", value="N/A")

    with col2:
        spearman = correlation.get('spearman')
        if spearman is not None:
            st.metric(
                label="📊 Spearman Correlation",
                value=f"{spearman:.4f}",
                delta=f"Rank-based",
                delta_color="off"
            )
        else:
            st.metric(label="Spearman Correlation", value="N/A")

    with col3:
        ratio = hedge_ratio.get('ratio')
        r_squared = hedge_ratio.get('r_squared', 0)
        if ratio is not None:
            ratio_emoji = "🟢" if r_squared > 0.7 else "🟡" if r_squared > 0.4 else "🔴"
            st.metric(
                label=f"{ratio_emoji} Hedge Ratio (β)",
                value=f"{ratio:.6f}",
                delta=f"R²: {r_squared:.4f}",
                delta_color="off"
            )
        else:
            st.metric(label="Hedge Ratio", value="N/A")

    with col4:
        if cointegration and cointegration.get('pvalue') is not None:
            pvalue = cointegration.get('pvalue', 1.0)
            is_coint = cointegration.get('is_cointegrated_5pct', False)
            coint_emoji = "✅" if is_coint else "❌"
            st.metric(
                label=f"{coint_emoji} Cointegration Test",
                value=f"p-value: {pvalue:.4f}",
                delta="Cointegrated" if is_coint else "Not cointegrated",
                delta_color="normal" if is_coint else "inverse"
            )
        else:
            st.metric(label="Cointegration", value="N/A")

    st.markdown("---")

    # Row 2: Spread & Trading Signal Metrics
    st.markdown("### 📈 Spread & Trading Signals")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        zscore_val = zscore.get('current')
        if zscore_val is not None:
            # Determine emoji and color based on Z-score
            if abs(zscore_val) > 2:
                zscore_emoji = "🔴"
                zscore_desc = "Strong Signal"
            elif abs(zscore_val) > 1:
                zscore_emoji = "🟡"
                zscore_desc = "Moderate Signal"
            else:
                zscore_emoji = "🟢"
                zscore_desc = "Neutral"

            st.metric(
                label=f"{zscore_emoji} Z-Score",
                value=f"{zscore_val:.4f}",
                delta=zscore_desc,
                delta_color="off"
            )
        else:
            st.metric(label="Z-Score", value="N/A")

    with col2:
        signal = zscore.get('signal', 'neutral')
        st.metric(
            label="📡 Trading Signal",
            value=signal.title(),
            delta_color="normal"
        )

    with col3:
        spread_current = spread.get('current')
        spread_mean = spread.get('mean')
        if spread_current is not None and spread_mean is not None:
            spread_diff_pct = ((spread_current / spread_mean - 1) * 100) if spread_mean != 0 else 0
            st.metric(
                label="💹 Current Spread",
                value=f"{spread_current:.4f}",
                delta=f"{spread_diff_pct:+.2f}% vs mean"
            )
        else:
            st.metric(label="Current Spread", value="N/A")

    with col4:
        spread_std = spread.get('std')
        if spread_std is not None:
            st.metric(
                label="📊 Spread Volatility",
                value=f"{spread_std:.4f}",
                delta="Standard Deviation",
                delta_color="off"
            )
        else:
            st.metric(label="Spread Volatility", value="N/A")

    st.markdown("---")

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
        ["📈 Single Symbol Analysis", "🔄 Pair Trading Analysis", "📊 Multi-Symbol Dashboard", "📤 Data Management"]
    )

    # Common settings
    st.sidebar.subheader("Settings")
    timeframe = st.sidebar.selectbox(
        "Timeframe",
        ["1s", "1m", "5m", "15m", "1h", "4h", "1d"],
        index=1,
        help="Select timeframe for OHLC data"
    )

    limit = st.sidebar.slider(
        "Data Points",
        min_value=50,
        max_value=1000,
        value=500,
        step=50,
        help="More data points = denser chart"
    )
    rolling_window = st.sidebar.slider(
        "Rolling Window",
        min_value=5,
        max_value=100,
        value=20,
        help="Window size for moving averages"
    )

    auto_refresh = st.sidebar.checkbox("Auto Refresh (10s)")

    # Page routing
    if page == "📈 Single Symbol Analysis":
        show_single_symbol_page(timeframe, limit, rolling_window)
    elif page == "🔄 Pair Trading Analysis":
        show_pair_trading_page(timeframe, limit, rolling_window)
    elif page == "📤 Data Management":
        show_data_management_page(timeframe)
    else:
        show_multi_symbol_page(timeframe, limit, rolling_window)

    # Auto refresh
    if auto_refresh:
        time.sleep(10)
        st.rerun()


def show_single_symbol_page(timeframe, limit, rolling_window):
    """Enhanced single symbol analysis page"""
    st.markdown("# 📈 Single Symbol Analysis")
    st.markdown("*Comprehensive price action and technical analysis for individual cryptocurrency pairs*")
    st.markdown("---")

    # Enhanced Symbol Selection Row
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        symbol = st.selectbox(
            "🔍 Select Trading Pair",
            ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"],
            key="single_symbol",
            help="Choose the cryptocurrency trading pair to analyze"
        )

    with col2:
        st.markdown("###")  # Spacing
        analyze_btn = st.button("🚀 Analyze", key="analyze_single", use_container_width=True)

    with col3:
        st.markdown("###")  # Spacing
        if st.button("🔄 Refresh", key="refresh_single", use_container_width=True):
            st.rerun()

    if analyze_btn:
        with st.spinner(f"📊 Fetching {symbol} data..."):
            # Get statistics
            stats = get_statistics(symbol, timeframe, limit, rolling_window)

            if stats:
                # Display metrics
                display_statistics_cards(stats)

                st.markdown("---")

                # Get OHLC data for charts
                ohlc_data = get_ohlc_data(symbol, timeframe, limit)

                if ohlc_data:
                    # Market Sentiment & Prediction Section
                    df_ohlc = pd.DataFrame(ohlc_data['bars'])
                    df_ohlc['timestamp'] = pd.to_datetime(df_ohlc['timestamp'])

                    st.markdown("---")
                    st.markdown("## 🎯 Market Sentiment & Forecast")

                    col1, col2 = st.columns(2)

                    with col1:
                        # Market Sentiment
                        sentiment, sentiment_color = calculate_market_sentiment(df_ohlc)
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, {sentiment_color}20 0%, {sentiment_color}10 100%);
                                    padding: 1.5rem; border-radius: 12px; border-left: 4px solid {sentiment_color};
                                    text-align: center;">
                            <h3 style="margin: 0; color: #2c3e50;">📊 Market Sentiment</h3>
                            <h2 style="margin: 0.5rem 0; color: {sentiment_color}; font-size: 2rem;">{sentiment}</h2>
                            <p style="margin: 0; color: #666; font-size: 0.9rem;">Based on SMA, EMA, Price & Volume</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        # Price Forecast
                        forecast = simple_price_forecast(df_ohlc, periods=5)
                        if forecast:
                            current_price = df_ohlc['close'].iloc[-1]
                            predicted_price = forecast[-1]
                            price_diff = ((predicted_price - current_price) / current_price) * 100
                            forecast_color = "#28a745" if price_diff > 0 else "#dc3545"

                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, {forecast_color}20 0%, {forecast_color}10 100%);
                                        padding: 1.5rem; border-radius: 12px; border-left: 4px solid {forecast_color};
                                        text-align: center;">
                                <h3 style="margin: 0; color: #2c3e50;">🔮 5-Period Forecast</h3>
                                <h2 style="margin: 0.5rem 0; color: {forecast_color}; font-size: 2rem;">
                                    ${predicted_price:,.2f} ({price_diff:+.2f}%)
                                </h2>
                                <p style="margin: 0; color: #666; font-size: 0.9rem;">Based on EMA trend analysis</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("Insufficient data for forecast (need 20+ data points)")

                    st.markdown("---")

                    # Charts Section
                    st.markdown("## 📊 Price & Volume Analysis")

                    # Candlestick chart with indicators
                    fig_candle = create_candlestick_chart(ohlc_data, show_indicators=True)
                    if fig_candle:
                        st.plotly_chart(fig_candle, use_container_width=True)

                    # Technical Indicators Summary
                    if len(df_ohlc) >= 20:
                        st.markdown("### 📈 Technical Indicators Summary")
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            sma_20 = df_ohlc['close'].rolling(window=20).mean().iloc[-1]
                            current_price = df_ohlc['close'].iloc[-1]
                            sma_signal = "Above" if current_price > sma_20 else "Below"
                            sma_color = "normal" if current_price > sma_20 else "inverse"
                            st.metric(
                                label="📊 SMA (20)",
                                value=f"${sma_20:,.2f}",
                                delta=f"Price {sma_signal}",
                                delta_color=sma_color
                            )

                        with col2:
                            ema_20 = df_ohlc['close'].ewm(span=20, adjust=False).mean().iloc[-1]
                            ema_signal = "Above" if current_price > ema_20 else "Below"
                            ema_color = "normal" if current_price > ema_20 else "inverse"
                            st.metric(
                                label="📉 EMA (20)",
                                value=f"${ema_20:,.2f}",
                                delta=f"Price {ema_signal}",
                                delta_color=ema_color
                            )

                        with col3:
                            # Calculate RSI (simplified)
                            delta = df_ohlc['close'].diff()
                            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                            rs = gain / loss
                            rsi = 100 - (100 / (1 + rs))
                            rsi_val = rsi.iloc[-1] if not rsi.empty and not pd.isna(rsi.iloc[-1]) else 50

                            rsi_signal = "Overbought" if rsi_val > 70 else "Oversold" if rsi_val < 30 else "Normal"
                            st.metric(
                                label="⚡ RSI (14)",
                                value=f"{rsi_val:.1f}",
                                delta=rsi_signal,
                                delta_color="off"
                            )

                        with col4:
                            # Volume trend
                            recent_volume = df_ohlc['volume'].tail(5).mean()
                            avg_volume = df_ohlc['volume'].mean()
                            volume_change = ((recent_volume / avg_volume - 1) * 100) if avg_volume > 0 else 0
                            st.metric(
                                label="📦 Volume Trend",
                                value=f"{recent_volume:,.0f}",
                                delta=f"{volume_change:+.1f}% vs avg"
                            )

                    st.markdown("---")

                    # Data Export Section
                    st.markdown("## 📥 Data Export")
                    st.markdown("Download the analyzed data for further processing or record-keeping")

                    col1, col2, col3 = st.columns([2, 2, 2])

                    with col1:
                        df_ohlc = pd.DataFrame(ohlc_data['bars'])
                        csv_data = df_ohlc.to_csv(index=False)
                        st.download_button(
                            label="📥 Download OHLC Data (CSV)",
                            data=csv_data,
                            file_name=f"{symbol}_{timeframe}_ohlc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key="download_ohlc_single",
                            use_container_width=True
                        )

                    with col2:
                        st.info(f"**{len(df_ohlc)}** data points ready for download")

                    with col3:
                        st.success(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")

                st.markdown("---")

                # Detailed statistics expander
                with st.expander("🔬 View Detailed Statistics JSON"):
                    st.json(stats)
            else:
                st.error("❌ No data available for this symbol.")
                st.info("💡 **Tip:** Make sure the backend ingestion service is running to collect data.")
                st.code("python backend/ingestion/ingestion_service.py", language="bash")


def show_pair_trading_page(timeframe, limit, rolling_window):
    """Enhanced pair trading analysis page"""
    st.markdown("# 🔄 Pair Trading Analysis")
    st.markdown("*Statistical arbitrage and mean reversion analysis for cryptocurrency pairs*")
    st.markdown("---")

    # Enhanced Pair Selection
    st.markdown("### 🎯 Select Trading Pair")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        symbol1 = st.selectbox(
            "📊 Primary Symbol (X)",
            ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"],
            key="pair_symbol1",
            help="First symbol in the pairs trading analysis"
        )

    with col2:
        symbol2 = st.selectbox(
            "📈 Secondary Symbol (Y)",
            ["ETHUSDT", "BTCUSDT", "BNBUSDT", "ADAUSDT"],
            index=0,
            key="pair_symbol2",
            help="Second symbol in the pairs trading analysis"
        )

    with col3:
        st.markdown("###")  # Spacing
        analyze_btn = st.button("🚀 Analyze Pair", key="analyze_pair", use_container_width=True)

    if analyze_btn:
        if symbol1 == symbol2:
            st.error("⚠️ Please select different symbols for pair trading analysis!")
            st.info("💡 **Tip:** Pair trading requires two different cryptocurrency pairs to analyze their relationship.")
            return

        with st.spinner(f"📊 Analyzing {symbol1} vs {symbol2}..."):
            analysis = analyze_pair(symbol1, symbol2, timeframe, rolling_window, limit)

            if analysis:
                st.markdown("---")

                # Display analysis
                display_pair_analysis(analysis)

                # Z-score gauge and strategy
                zscore = analysis.get('zscore', {})
                zscore_val = zscore.get('current')

                if zscore_val is not None:
                    st.markdown("## 📊 Z-Score Analysis & Trading Strategy")

                    col1, col2 = st.columns([1, 2])

                    with col1:
                        fig_gauge = create_zscore_gauge(zscore_val)
                        if fig_gauge:
                            st.plotly_chart(fig_gauge, use_container_width=True)

                    with col2:
                        st.markdown("### 📚 Mean Reversion Trading Strategy")
                        st.markdown("""
                        <div class="info-card">
                        <h4>🎯 Z-Score Interpretation Guide</h4>

                        **Signal Zones:**
                        - 🔴 **Z < -2**: Strong long signal (spread significantly undervalued)
                        - 🟡 **-2 < Z < -1**: Moderate long signal (spread moderately undervalued)
                        - 🟢 **-1 < Z < 1**: Neutral zone (no clear trading opportunity)
                        - 🟡 **1 < Z < 2**: Moderate short signal (spread moderately overvalued)
                        - 🔴 **Z > 2**: Strong short signal (spread significantly overvalued)

                        **Trading Actions:**
                        1. **Enter Long**: When Z-score drops below -2 (spread undervalued)
                        2. **Enter Short**: When Z-score rises above +2 (spread overvalued)
                        3. **Exit Position**: When Z-score returns to zero (mean reversion)

                        **Risk Management:**
                        - Set stop-loss if Z-score moves further in the opposite direction
                        - Use hedge ratio (β) to determine position sizes
                        - Monitor cointegration to ensure relationship holds
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")

                # Data Export Section
                st.markdown("## 📥 Data Export")
                st.markdown("Download comprehensive analysis results for further processing")

                col1, col2, col3 = st.columns([2, 2, 2])

                with col1:
                    # Prepare analytics data for export
                    export_data = {
                        'Symbol1': symbol1,
                        'Symbol2': symbol2,
                        'Timeframe': timeframe,
                        'Timestamp': analysis.get('timestamp'),
                        'Correlation_Pearson': analysis.get('correlation', {}).get('pearson'),
                        'Correlation_Spearman': analysis.get('correlation', {}).get('spearman'),
                        'Hedge_Ratio': analysis.get('hedge_ratio', {}).get('ratio'),
                        'Hedge_Ratio_R2': analysis.get('hedge_ratio', {}).get('r_squared'),
                        'Cointegration_Statistic': analysis.get('cointegration', {}).get('statistic'),
                        'Cointegration_PValue': analysis.get('cointegration', {}).get('pvalue'),
                        'Cointegrated_5pct': analysis.get('cointegration', {}).get('is_cointegrated_5pct'),
                        'ZScore_Current': analysis.get('zscore', {}).get('current'),
                        'ZScore_Signal': analysis.get('zscore', {}).get('signal'),
                        'Spread_Current': analysis.get('spread', {}).get('current'),
                        'Spread_Mean': analysis.get('spread', {}).get('mean'),
                        'Spread_Std': analysis.get('spread', {}).get('std')
                    }

                    df_analytics = pd.DataFrame([export_data])
                    csv_analytics = df_analytics.to_csv(index=False)

                    st.download_button(
                        label="📥 Download Analysis Results (CSV)",
                        data=csv_analytics,
                        file_name=f"{symbol1}_{symbol2}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_analytics_pair",
                        use_container_width=True
                    )

                with col2:
                    data_points = analysis.get('data_points', 0)
                    st.info(f"**{data_points}** aligned data points analyzed")

                with col3:
                    st.success(f"**Analysis Complete:** {datetime.now().strftime('%H:%M:%S')}")

                st.markdown("---")

                # Detailed results expander
                with st.expander("🔬 View Detailed Analysis JSON"):
                    st.json(analysis)
            else:
                st.error("❌ No data available for this pair.")
                st.info("💡 **Tip:** Ensure both symbols have sufficient OHLC data in the database.")
                st.code("python backend/ingestion/ingestion_service.py", language="bash")


def show_multi_symbol_page(timeframe, limit, rolling_window):
    """Enhanced multi-symbol dashboard page"""
    st.markdown("# 📊 Multi-Symbol Dashboard")
    st.markdown("*Real-time overview of multiple cryptocurrency pairs at a glance*")
    st.markdown("---")

    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 💹 Market Overview")
    with col2:
        if st.button("🔄 Refresh All", key="refresh_multi", use_container_width=True):
            st.rerun()

    st.markdown("---")

    if st.button("📊 Load Market Data", key="load_multi", use_container_width=False):
        for idx, symbol in enumerate(symbols):
            with st.container():
                # Symbol header
                st.markdown(f"### {['🥇', '🥈', '🥉', '🏅'][idx]} {symbol}")

                stats = get_statistics(symbol, timeframe, min(50, limit), rolling_window)

                if stats:
                    price_stats = stats.get('price_stats', {})
                    volatility = stats.get('volatility', {})
                    volume_stats = stats.get('volume_stats', {})

                    # Create 4-column layout
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        latest_price = price_stats.get('latest', 0)
                        change_pct = price_stats.get('change_pct', 0)
                        st.metric(
                            label="💵 Price",
                            value=f"${latest_price:,.2f}",
                            delta=f"{change_pct:.2f}%"
                        )

                    with col2:
                        vol = volatility.get('current')
                        ann_vol = volatility.get('annualized', 0)
                        if vol:
                            st.metric(
                                label="📊 Volatility",
                                value=f"{vol*100:.3f}%",
                                delta=f"Ann: {ann_vol*100:.1f}%",
                                delta_color="off"
                            )
                        else:
                            st.metric(label="📊 Volatility", value="N/A")

                    with col3:
                        if volume_stats:
                            latest_vol = volume_stats.get('latest', 0)
                            mean_vol = volume_stats.get('mean', 0)
                            vol_change = ((latest_vol / mean_vol - 1) * 100) if mean_vol > 0 else 0
                            st.metric(
                                label="📦 Volume",
                                value=f"{latest_vol:,.0f}",
                                delta=f"{vol_change:+.1f}% vs avg"
                            )
                        else:
                            st.metric(label="📦 Volume", value="N/A")

                    with col4:
                        high_price = price_stats.get('high', 0)
                        low_price = price_stats.get('low', 0)
                        daily_range = high_price - low_price
                        st.metric(
                            label="📈 24h Range",
                            value=f"${daily_range:,.2f}",
                            delta=f"H: ${high_price:,.2f} L: ${low_price:,.2f}",
                            delta_color="off"
                        )
                else:
                    st.warning(f"No data available for {symbol}")

                # Add divider between symbols
                if idx < len(symbols) - 1:
                    st.divider()


def show_data_management_page(timeframe):
    """Data management page for uploads and exports"""
    st.header("📤 Data Management")

    # Create tabs for Upload and Export
    tab1, tab2 = st.tabs(["📤 Upload OHLC Data", "📥 Export Alert History"])

    with tab1:
        st.subheader("Upload Historical OHLC CSV Data")

        st.markdown("""
        Upload historical OHLC (Open-High-Low-Close) data in CSV format.

        **Required CSV Format:**
        ```
        timestamp,open,high,low,close,volume
        2024-01-01 00:00:00,42000.50,42100.00,41900.00,42050.75,1234.56
        ```

        **Column Requirements:**
        - `timestamp`: Date and time (YYYY-MM-DD HH:MM:SS or ISO format)
        - `open`: Opening price (float)
        - `high`: Highest price (float)
        - `low`: Lowest price (float)
        - `close`: Closing price (float)
        - `volume`: Trading volume (float, optional)
        """)

        # Upload form
        col1, col2 = st.columns(2)

        with col1:
            upload_symbol = st.selectbox(
                "Symbol",
                ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "CUSTOM"],
                key="upload_symbol"
            )

            if upload_symbol == "CUSTOM":
                upload_symbol = st.text_input("Enter custom symbol:", "")

        with col2:
            upload_timeframe = st.selectbox(
                "Timeframe",
                ["1s", "1m", "5m", "15m", "1h", "4h", "1d"],
                index=1,
                key="upload_timeframe"
            )

        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type=['csv'],
            key="csv_uploader"
        )

        if uploaded_file is not None:
            try:
                # Preview the uploaded data
                df = pd.read_csv(uploaded_file)
                st.write("**Preview of uploaded data:**")
                st.dataframe(df.head(10))

                # Validate columns
                required_cols = ['timestamp', 'open', 'high', 'low', 'close']
                missing_cols = [col for col in required_cols if col not in df.columns]

                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                else:
                    st.success(f"✅ Valid format! Found {len(df)} rows")

                    # Upload button
                    if st.button("Upload to Database", key="upload_btn"):
                        if not upload_symbol or upload_symbol == "CUSTOM":
                            st.error("Please enter a valid symbol")
                        else:
                            with st.spinner("Uploading data..."):
                                # Reset file pointer
                                uploaded_file.seek(0)
                                success, result = upload_ohlc_csv(
                                    upload_symbol.upper(),
                                    upload_timeframe,
                                    uploaded_file
                                )

                                if success:
                                    st.success(f"✅ Successfully uploaded {result.get('rows_inserted', 0)} rows!")
                                    st.balloons()
                                else:
                                    st.error(f"❌ Upload failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                st.error(f"❌ Error reading CSV file: {e}")

    with tab2:
        st.subheader("Export Alert History")

        st.markdown("""
        Download the complete alert history including all triggered alerts,
        Z-scores, symbols, and timestamps.
        """)

        export_limit = st.slider(
            "Number of alerts to export",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            key="alert_export_limit"
        )

        if st.button("Fetch Alert History", key="fetch_alerts"):
            with st.spinner("Fetching alert history..."):
                alerts = get_alert_history(limit=export_limit)

                if alerts and len(alerts) > 0:
                    st.success(f"✅ Found {len(alerts)} alerts")

                    # Convert to DataFrame
                    df_alerts = pd.DataFrame(alerts)

                    # Preview
                    st.write("**Preview:**")
                    st.dataframe(df_alerts.head(10))

                    # Download button
                    csv_alerts = df_alerts.to_csv(index=False)

                    st.download_button(
                        label="📥 Download Alert History (CSV)",
                        data=csv_alerts,
                        file_name=f"alert_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key="download_alerts"
                    )
                else:
                    st.warning("No alert history found. Alerts will appear here once triggered.")


if __name__ == "__main__":
    main()
