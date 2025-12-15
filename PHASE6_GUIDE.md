# Phase 6: Frontend Dashboard - Complete Guide

## Overview

Phase 6 implements a professional web-based dashboard using Streamlit and Plotly for real-time cryptocurrency analytics visualization. The dashboard provides interactive charts, trading signals, and comprehensive analytics in an intuitive interface.

## Architecture

```
Frontend Dashboard
├── Streamlit Web Framework
├── Plotly Interactive Charts
├── REST API Integration
└── Three Main Pages:
    ├── Single Symbol Analysis
    ├── Pair Trading Analysis
    └── Multi-Symbol Dashboard
```

## Features

### 1. Single Symbol Analysis

**Interactive Price Charts:**
- Candlestick (OHLC) charts with zoom and pan
- Volume bar charts color-coded by price movement
- Real-time data updates

**Key Metrics:**
- Latest Price with 24h change percentage
- Mean Price with standard deviation
- Volatility (current and annualized)
- Trading Volume (latest and average)

**Detailed Statistics:**
- Price statistics (mean, median, std, min, max, range)
- Volume analysis (total, mean, median)
- Returns calculation
- VWAP (Volume-Weighted Average Price)

### 2. Pair Trading Analysis

**Correlation Analysis:**
- Pearson correlation coefficient
- Spearman rank correlation
- Correlation strength classification

**Statistical Arbitrage:**
- Hedge ratio calculation (OLS regression)
- R-squared goodness of fit
- Cointegration test (ADF test)
- P-value interpretation

**Z-Score Analysis:**
- Interactive Z-score gauge (range: -3 to +3)
- Color-coded zones:
  - Green: Neutral zone (-1 to +1)
  - Yellow: Caution zones (-2 to -1, +1 to +2)
  - Red: Strong signal zones (< -2, > +2)
- Current Z-score value
- Trading signal generation

**Trading Signals:**
- 🟢 **LONG Signal**: Z-score < -1 (spread undervalued)
- 🟡 **NEUTRAL**: -1 < Z-score < 1 (no strong signal)
- 🔴 **SHORT Signal**: Z-score > 1 (spread overvalued)

### 3. Multi-Symbol Dashboard

**Simultaneous Monitoring:**
- Track multiple cryptocurrency pairs
- Quick overview of price, volatility, and volume
- Percentage change indicators
- Refresh all data with one click

## Installation & Setup

### Prerequisites

1. **Python 3.8+** with virtual environment
2. **Running API server** (Phase 5)
3. **OHLC data** in database (Phase 3)

### Install Dependencies

```bash
pip install streamlit plotly requests pandas
```

Or update your requirements:

```bash
echo "streamlit>=1.28.0" >> requirements.txt
echo "plotly>=5.17.0" >> requirements.txt
pip install -r requirements.txt
```

### Verify Installation

```bash
python test_phase6.py
```

This checks:
- ✅ Dependencies installed
- ✅ Dashboard file exists
- ✅ API server is running
- ✅ Code syntax is valid

## Running the Dashboard

### Method 1: Standard Launch

```bash
streamlit run frontend/dashboard.py
```

### Method 2: Python Module

```bash
python -m streamlit run frontend/dashboard.py
```

### Method 3: With Custom Port

```bash
streamlit run frontend/dashboard.py --server.port 8502
```

The dashboard will automatically open in your browser at:
**http://localhost:8501**

## Using the Dashboard

### Sidebar Configuration

**Navigation:**
- 📈 Single Symbol Analysis
- 🔄 Pair Trading Analysis
- 📊 Multi-Symbol Dashboard

**Settings:**
- **Timeframe**: 1s, 1m, 5m, 15m, 1h, 4h, 1d
- **Data Points**: 10 to 500 (controls history)
- **Rolling Window**: 5 to 100 (for volatility and correlations)
- **Auto Refresh**: Enable for real-time updates every 10 seconds

### Page 1: Single Symbol Analysis

1. **Select Symbol**: Choose from dropdown (BTCUSDT, ETHUSDT, etc.)
2. **Click "Analyze"**: Fetches data and generates charts
3. **View Metrics**: Four key metrics displayed at top
4. **Explore Charts**:
   - Zoom: Click and drag on chart
   - Pan: Shift + click and drag
   - Reset: Double-click
5. **Detailed Stats**: Expand "Detailed Statistics" for raw JSON

### Page 2: Pair Trading Analysis

1. **Select Symbols**: Choose two different crypto pairs
2. **Click "Analyze Pair"**: Runs complete pair analysis
3. **Review Metrics**: Correlation, hedge ratio, cointegration, Z-score
4. **Check Signal**: Color-coded alert shows trading recommendation
5. **Study Z-Score Gauge**: Visual representation of spread deviation
6. **Read Strategy**: Built-in mean reversion strategy explanation
7. **Detailed Results**: Expand for complete analysis JSON

**Example Trading Setup:**
- **Pair**: BTCUSDT vs ETHUSDT
- **Correlation**: 0.95 (very strong)
- **Hedge Ratio**: 29.85 (buy 1 BTC, sell 29.85 ETH)
- **Z-Score**: -2.1 (strong long signal)
- **Action**: Long the spread (expect mean reversion)

### Page 3: Multi-Symbol Dashboard

1. **Click "Refresh All"**: Loads data for all symbols
2. **Compare Metrics**: Side-by-side comparison
3. **Identify Opportunities**: Find high volatility or price changes
4. **Quick Overview**: No need to analyze each symbol individually

## Dashboard Components

### Candlestick Chart

**Features:**
- OHLC bars (Open, High, Low, Close)
- Green candles: Close > Open (bullish)
- Red candles: Close < Open (bearish)
- Interactive timeline
- Hover for exact values

**Controls:**
- Zoom: Select area with mouse
- Pan: Shift + drag
- Home: Double-click to reset
- Download: Camera icon (top-right)

### Volume Chart

**Features:**
- Bar chart synchronized with price chart
- Color-coded bars:
  - Green: Bullish volume (price up)
  - Red: Bearish volume (price down)
- Identify volume spikes
- Correlate with price movements

### Z-Score Gauge

**Interpretation:**
- **Center (0)**: Spread at historical mean
- **Left (-3 to 0)**: Spread below mean (undervalued)
- **Right (0 to +3)**: Spread above mean (overvalued)
- **Threshold Lines**: Mark significant deviations

**Color Zones:**
- 🟢 **Green** (-1 to +1): Normal range
- 🟡 **Yellow** (-2 to -1, +1 to +2): Caution
- 🔴 **Red** (< -2, > +2): Strong signal

### Statistics Cards

**Metric Card Format:**
```
┌─────────────────────┐
│ Latest Price        │
│ $96,250.50          │
│ ▲ +1.23%           │
└─────────────────────┘
```

**Delta Indicators:**
- ▲ Green: Positive change
- ▼ Red: Negative change
- — Gray: No change

## Configuration Options

### Auto-Refresh

Enable in sidebar for automatic updates:
- **Interval**: 10 seconds
- **Use Case**: Monitor live markets
- **Disable**: For detailed analysis (prevents interruption)

### Timeframe Selection

Choose based on trading strategy:
- **1s, 1m**: Scalping, high-frequency trading
- **5m, 15m**: Day trading
- **1h, 4h**: Swing trading
- **1d**: Position trading, long-term analysis

### Data Points (Limit)

Controls historical depth:
- **10-50**: Recent activity, fast loading
- **100**: Default, balanced view
- **200-500**: Long-term patterns, slower loading

### Rolling Window

Affects volatility and correlation calculations:
- **5-10**: More responsive, less smooth
- **20**: Default, balanced
- **50-100**: More stable, less sensitive to outliers

## Customization

### Adding New Symbols

Edit `frontend/dashboard.py`:

```python
# Line ~520 - Single Symbol Analysis
symbol = st.selectbox(
    "Select Symbol",
    ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "YOUR_SYMBOL"],
    key="single_symbol"
)

# Line ~620 - Pair Trading
symbol1 = st.selectbox(
    "Symbol 1",
    ["BTCUSDT", "ETHUSDT", "YOUR_SYMBOL"],
    key="pair_symbol1"
)
```

### Changing Color Theme

Modify CSS in `frontend/dashboard.py` (line ~20):

```python
st.markdown("""
    <style>
    .main-header {
        color: #YOUR_COLOR;  /* Change header color */
    }
    .success-signal {
        background-color: #YOUR_BG;  /* Change signal background */
    }
    </style>
""", unsafe_allow_html=True)
```

### Adjusting Chart Heights

Modify `update_layout` height parameter:

```python
fig.update_layout(
    height=600,  # Change from 500 to 600 for taller charts
    ...
)
```

## API Integration

### Endpoints Used

1. **GET /api/health** - Check API availability
2. **GET /api/stats/{symbol}** - Fetch statistics
3. **GET /api/ohlc/{symbol}** - Get OHLC candlestick data
4. **POST /api/pairs/analyze** - Analyze pair correlations

### Request Flow

```
Dashboard → API Request → Backend Processing → Database Query → Response → Chart Rendering
```

### Error Handling

**API Unavailable:**
- Shows error message
- Displays command to start API server
- Prevents further execution

**No Data Available:**
- Shows warning message
- Suggests running test_phase3.py
- Allows retry

**Network Errors:**
- Timeout after 10-15 seconds
- Error message with details
- Graceful degradation

## Performance Optimization

### Loading Speed

**Fast Loading (< 1 second):**
- Limit: 50 data points
- Rolling window: 10
- Single symbol analysis

**Balanced (1-3 seconds):**
- Limit: 100 data points (default)
- Rolling window: 20
- Pair analysis

**Comprehensive (3-5 seconds):**
- Limit: 500 data points
- Rolling window: 100
- All analytics enabled

### Memory Usage

**Low Memory:**
- Single symbol page
- 10-50 data points
- No auto-refresh

**Medium Memory:**
- Pair trading page (default)
- 100 data points
- Occasional refresh

**High Memory:**
- Multi-symbol dashboard
- 200+ data points per symbol
- Auto-refresh enabled

## Troubleshooting

### Issue: Dashboard won't start

**Solution:**
```bash
# Check Streamlit installation
pip install --upgrade streamlit

# Run from project root
cd /path/to/crypto-quant-analytics-platform
streamlit run frontend/dashboard.py
```

### Issue: "API is not available"

**Solution:**
```bash
# Start API server in separate terminal
python -m uvicorn backend.api.app:app --reload

# Verify it's running
curl http://localhost:8000/api/health
```

### Issue: "No data available"

**Solution:**
```bash
# Generate OHLC data
python test_phase3.py --full

# Verify data exists
python -c "from backend.storage.ohlc_repository import OHLCRepository; print(OHLCRepository.get_recent_ohlc('BTCUSDT', '1m', 10))"
```

### Issue: Charts not displaying

**Solution:**
```bash
# Install/upgrade Plotly
pip install --upgrade plotly

# Clear Streamlit cache
# In dashboard, press 'c' then 'Clear cache'
```

### Issue: "Port already in use"

**Solution:**
```bash
# Use different port
streamlit run frontend/dashboard.py --server.port 8502

# Or kill existing Streamlit process
# Windows: taskkill /F /IM streamlit.exe
# Linux/Mac: pkill -f streamlit
```

## Production Deployment

### Streamlit Cloud (Free)

1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect repository
4. Deploy `frontend/dashboard.py`
5. Configure secrets for API URL

### Docker Container

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "frontend/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Environment Variables

```bash
# .streamlit/config.toml
[server]
port = 8501
enableCORS = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
```

## Best Practices

### Trading Signal Interpretation

1. **Don't rely solely on Z-scores** - Use as one signal among many
2. **Confirm cointegration** - P-value should be < 0.05
3. **Check correlation strength** - Should be > 0.7 for pairs trading
4. **Monitor hedge ratio stability** - Large changes indicate unstable relationship
5. **Use stop-losses** - Protect against correlation breakdown

### Data Refresh Strategy

1. **Manual refresh** for detailed analysis
2. **Auto-refresh** for monitoring only
3. **Reasonable intervals** (10s minimum)
4. **Disable when not watching** to save resources

### Performance Tips

1. **Start with small data sets** (limit: 50)
2. **Increase gradually** as needed
3. **Use appropriate timeframes** for your strategy
4. **Close unused browser tabs** to free memory

## Next Steps

After mastering the dashboard:

### Phase 7: Alert System
- Automated Z-score monitoring
- Email/Telegram notifications
- Webhook integrations
- Custom alert rules

### Enhancements
- Add more indicators (RSI, MACD, Bollinger Bands)
- Implement backtesting module
- Add portfolio tracking
- Create custom strategies

## Files Created in Phase 6

```
frontend/
├── __init__.py
├── dashboard.py (650+ lines) - Main Streamlit application
└── components/ (for future modular components)

test_phase6.py (100+ lines) - Dashboard verification script
PHASE6_GUIDE.md (This file) - Complete documentation
```

## Summary

Phase 6 successfully delivers a production-ready web dashboard with:

- ✅ Interactive candlestick charts with Plotly
- ✅ Real-time statistics and metrics
- ✅ Z-score gauge for trading signals
- ✅ Color-coded trading recommendations
- ✅ Multi-page navigation (3 pages)
- ✅ Auto-refresh capability
- ✅ Comprehensive pair trading analysis
- ✅ Professional UI/UX design
- ✅ API integration with error handling
- ✅ Customizable settings

The dashboard transforms raw analytics data into actionable trading insights through intuitive visualizations and clear signals.

**Ready to visualize your crypto analytics!** 📊🚀
