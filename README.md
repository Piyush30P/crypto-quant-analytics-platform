# Crypto Analytics Platform 📊

A real-time quantitative analytics platform for cryptocurrency pairs trading, featuring live WebSocket data ingestion, statistical analysis, and interactive visualization.

## 🎯 Features

- **Real-time Data Ingestion**: Live tick data from Binance WebSocket streams
- **Multi-Timeframe Analysis**: 1-second, 1-minute, and 5-minute OHLC resampling
- **Quantitative Analytics**:
  - Price statistics and VWAP
  - OLS regression for hedge ratios
  - Spread calculation and z-score analysis
  - ADF test for cointegration
  - Rolling correlation metrics
- **Interactive Dashboard**: Streamlit-based UI with Plotly charts
- **Alert System**: Custom rule-based alerts for trading signals
- **Data Export**: CSV export functionality for processed data
- **Historical Data Upload**: Support for OHLC CSV uploads

## 🏗️ Architecture

```
┌─────────────────┐
│  Binance WSS    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  WebSocket      │
│  Ingestion      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Database       │◄────┤  Resampling     │
│  (SQLite/       │     │  Engine         │
│   PostgreSQL)   │     └─────────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Analytics      │◄────┤  Cache Layer    │
│  Engine         │     │  (Redis/Memory) │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI        │
│  REST API       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Streamlit      │◄────┤  Alert Manager  │
│  Dashboard      │     └─────────────────┘
└─────────────────┘
```

## 📋 Prerequisites

- Python 3.9 or higher
- pip package manager
- (Optional) PostgreSQL/TimescaleDB for production deployment
- (Optional) Redis for caching

## 🚀 Quick Start

### 1. Clone and Navigate

```bash
cd "c:\Users\pisep\OneDrive\Desktop\6th sem main\Projects\Gemscap"
```

### 2. Create Virtual Environment

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
copy .env.example .env
# Edit .env with your configuration (optional)
```

### 5. Run the Application

```bash
python run.py
```

This will:

- Initialize the database
- Start the FastAPI backend (http://localhost:8000)
- Launch the Streamlit dashboard (http://localhost:8501)
- Begin ingesting live data from Binance

## 📁 Project Structure

```
Gemscap/
├── backend/
│   ├── ingestion/          # WebSocket clients and data sampling
│   ├── storage/            # Database models and connections
│   ├── analytics/          # Quantitative analysis modules
│   ├── api/                # FastAPI routes and endpoints
│   └── alerts/             # Alert management system
├── frontend/
│   ├── components/         # Streamlit UI components
│   └── utils/              # Frontend utilities
├── config/
│   └── settings.py         # Configuration management
├── docs/
│   ├── architecture.drawio # System architecture diagram
│   └── chatgpt_usage.md    # AI assistance documentation
├── tests/                  # Unit and integration tests
├── logs/                   # Application logs
├── exports/                # Exported data files
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── run.py                  # Application launcher
└── README.md               # This file
```

## 🔧 Configuration

Key configuration options in `.env`:

| Variable                 | Default                           | Description                  |
| ------------------------ | --------------------------------- | ---------------------------- |
| `DEBUG`                  | `True`                            | Enable debug mode            |
| `API_PORT`               | `8000`                            | FastAPI port                 |
| `FRONTEND_PORT`          | `8501`                            | Streamlit port               |
| `DATABASE_URL`           | `sqlite:///./crypto_analytics.db` | Database connection          |
| `REDIS_ENABLED`          | `False`                           | Enable Redis caching         |
| `DEFAULT_SYMBOLS`        | `["BTCUSDT","ETHUSDT"]`           | Trading pairs to monitor     |
| `DEFAULT_ROLLING_WINDOW` | `20`                              | Rolling window for analytics |

## 📊 Analytics Methodology

### Pairs Trading Analytics

1. **Hedge Ratio Calculation**: OLS regression between two assets

   - `Y = α + β*X + ε`
   - Hedge ratio = β (slope coefficient)

2. **Spread Construction**: `Spread = Price_A - (HedgeRatio × Price_B)`

3. **Z-Score Normalization**:

   - `Z = (Spread - μ) / σ`
   - Rolling mean (μ) and std (σ) over configurable window

4. **Cointegration Test**: Augmented Dickey-Fuller (ADF) test

   - H0: Spread has unit root (not cointegrated)
   - p-value < 0.05 suggests cointegration

5. **Rolling Correlation**: Pearson correlation coefficient over rolling window

## 🎨 Dashboard Usage

### Main Controls

- **Symbol Selection**: Choose trading pairs for analysis
- **Timeframe**: Select data granularity (1s, 1m, 5m)
- **Rolling Window**: Adjust window for moving statistics
- **Analytics Options**: Enable/disable specific calculations

### Visualizations

- **Price Charts**: Interactive candlestick/line charts with zoom/pan
- **Spread & Z-Score**: Pairs trading signals
- **Correlation Heatmap**: Cross-asset relationships
- **Volume Analysis**: Trading activity metrics
- **Statistics Table**: Real-time summary metrics

### Alerts

Configure custom alerts:

- Z-score thresholds
- Price level breakouts
- Correlation breakdowns
- Volume spikes

## 📤 Data Export

Export processed data and analytics:

1. Navigate to Export section in dashboard
2. Select date range and metrics
3. Click "Download CSV"
4. Files saved to `exports/` directory

## 🧪 Testing

Run tests:

```bash
pytest tests/
```

Run specific test:

```bash
pytest tests/test_analytics.py
```

## 🐛 Troubleshooting

### Database Issues

```bash
# Reset database
python -c "from backend.storage.database import init_db, engine; from backend.storage.models import Base; Base.metadata.drop_all(engine); init_db()"
```

### Port Already in Use

- Change `API_PORT` or `FRONTEND_PORT` in `.env`

### WebSocket Connection Fails

- Check internet connection
- Verify Binance API is accessible
- Review logs in `logs/app.log`

## 📝 Development Notes

### Adding New Analytics

1. Create module in `backend/analytics/`
2. Inherit from `BaseAnalyzer` class
3. Implement `calculate()` method
4. Register in analytics engine

### Adding New Alerts

1. Define alert type in `backend/alerts/rules.py`
2. Implement condition logic
3. Update frontend alert configuration

## 🤖 AI Assistance

This project utilized ChatGPT/Claude for:

- Code structure and boilerplate generation
- Analytics algorithm implementation
- Documentation writing
- Debugging assistance

See `docs/chatgpt_usage.md` for detailed prompt logs.

## 📄 License

This project is for educational and evaluation purposes.

## 👤 Author

**Anagh**  
Quant Developer Evaluation Assignment

## 🙏 Acknowledgments

- Binance for WebSocket API
- Streamlit for rapid dashboard development
- FastAPI for modern API framework
- Open-source Python scientific computing stack

---

**Note**: This is a prototype system designed for demonstration purposes. For production deployment, consider:

- Horizontal scaling with message queues (Kafka/RabbitMQ)
- TimescaleDB for time-series optimization
- Kubernetes for container orchestration
- Monitoring and alerting (Prometheus/Grafana)
- Authentication and authorization
- Rate limiting and API security
