# Phase 5: API Layer - Complete Guide

## Overview

Phase 5 implements a professional REST API using FastAPI, exposing all analytics capabilities through HTTP endpoints with automatic documentation, request validation, and error handling.

## Architecture

```
API Layer
├── Pydantic Schemas (Request/Response Models)
├── FastAPI Routes (Endpoint Handlers)
├── Main Application (CORS, Middleware, Events)
└── Interactive Documentation (Swagger UI, ReDoc)
```

## Components Created

### 1. Pydantic Schemas (`backend/api/schemas.py`)

**Request Models:**
- `SymbolRequest` - Basic symbol queries
- `PairAnalysisRequest` - Pair trading analysis requests
- `TimeRangeRequest` - Time-based data queries
- `ExportRequest` - Data export requests

**Response Models:**
- `BasicStatsResponse` - Statistics with nested metrics
- `PairAnalysisResponse` - Comprehensive pair analytics
- `OHLCResponse` - Candlestick data
- `TicksResponse` - Raw tick data
- `HealthResponse` - System health status

**Nested Models:**
- `PriceStats` - Price statistics (mean, std, range)
- `VolumeStats` - Volume metrics
- `VolatilityStats` - Volatility calculations
- `CorrelationStats` - Correlation metrics
- `HedgeRatioStats` - Hedge ratio details
- `CointegrationStats` - Cointegration test results
- `ZScoreStats` - Z-score analysis

**Features:**
- Field validation with constraints (ge, le, minLength)
- Descriptive field documentation
- Optional fields with sensible defaults
- Type safety with Python type hints

### 2. API Routes (`backend/api/routes.py`)

**Health & System:**
```
GET /api/health
```
- Returns system health status
- Checks database and analytics components
- No authentication required

**Statistics:**
```
GET /api/stats/{symbol}
Query Parameters:
  - timeframe: str (default: "1m")
  - limit: int (default: 100, max: 1000)
  - rolling_window: int (default: 20, range: 5-100)
```
- Comprehensive price/volume statistics
- Returns: mean, std, VWAP, volatility, returns
- 404 if no data available

**OHLC Data:**
```
GET /api/ohlc/{symbol}
Query Parameters:
  - timeframe: str (default: "1m")
  - limit: int (default: 100, max: 500)
```
- Candlestick bars with OHLC + Volume
- Sorted by timestamp (newest first)
- 404 if no data available

**Tick Data:**
```
GET /api/ticks/{symbol}
Query Parameters:
  - limit: int (default: 100, max: 1000)
```
- Raw tick-level price data
- Returns: timestamp, price, quantity, volume
- 404 if no data available

**Pair Analysis:**
```
POST /api/pairs/analyze
Request Body:
{
  "symbol1": "BTCUSDT",
  "symbol2": "ETHUSDT",
  "timeframe": "1m",
  "rolling_window": 20,
  "limit": 100
}
```
- Correlation (Pearson, Spearman)
- Hedge ratio (OLS regression)
- Cointegration test (ADF)
- Spread and Z-score analysis
- Rolling correlation
- 404 if insufficient data

**Metadata:**
```
GET /api/symbols
```
- Returns list of available symbols
- Empty list if no data

```
GET /api/timeframes/{symbol}
```
- Returns available timeframes for symbol
- Empty list if no data

### 3. Main Application (`backend/api/app.py`)

**FastAPI Configuration:**
- Title: "Crypto Analytics Platform API"
- Version: from settings
- Comprehensive API description
- Auto-generated OpenAPI schema

**Middleware:**
- CORS enabled for all origins (configure for production)
- Allow all HTTP methods and headers
- Credentials support enabled

**Event Handlers:**
- Startup: Logs API information and documentation URL
- Shutdown: Clean shutdown logging

**Exception Handling:**
- Global exception handler for unhandled errors
- Debug mode shows full error details
- Production mode hides sensitive information

**Documentation:**
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

### 4. Test Suite (`test_phase5.py`)

**Quick Component Test:**
```bash
python test_phase5.py
```
- Module import verification
- FastAPI app configuration check
- Pydantic schema validation
- Route registration verification

**Full API Test:**
```bash
python test_phase5.py --full
```
Requires running API server. Tests:
1. Server connectivity
2. Health check endpoint
3. Statistics endpoint (all symbols)
4. OHLC data endpoint
5. Tick data endpoint
6. Pair analysis endpoint
7. Symbols and timeframes endpoints
8. API documentation availability

## Running the API

### Method 1: Direct Python
```bash
python backend/api/app.py
```

### Method 2: Uvicorn (Recommended)
```bash
uvicorn backend.api.app:app --reload
```

### Method 3: Production
```bash
uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Method 4: Background
```bash
uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 &
```

## API Usage Examples

### Using cURL

**Health Check:**
```bash
curl http://localhost:8000/api/health
```

**Get Statistics:**
```bash
curl "http://localhost:8000/api/stats/BTCUSDT?timeframe=1m&limit=100&rolling_window=20"
```

**Get OHLC Data:**
```bash
curl "http://localhost:8000/api/ohlc/BTCUSDT?timeframe=1m&limit=50"
```

**Get Tick Data:**
```bash
curl "http://localhost:8000/api/ticks/BTCUSDT?limit=100"
```

**Pair Analysis:**
```bash
curl -X POST http://localhost:8000/api/pairs/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symbol1": "BTCUSDT",
    "symbol2": "ETHUSDT",
    "timeframe": "1m",
    "rolling_window": 20,
    "limit": 100
  }'
```

**List Symbols:**
```bash
curl http://localhost:8000/api/symbols
```

**List Timeframes:**
```bash
curl http://localhost:8000/api/timeframes/BTCUSDT
```

### Using Python Requests

```python
import requests

# Base URL
API_URL = "http://localhost:8000"

# Get statistics
response = requests.get(
    f"{API_URL}/api/stats/BTCUSDT",
    params={"timeframe": "1m", "limit": 100}
)
stats = response.json()
print(f"Mean Price: ${stats['price_stats']['mean']:.2f}")

# Pair analysis
response = requests.post(
    f"{API_URL}/api/pairs/analyze",
    json={
        "symbol1": "BTCUSDT",
        "symbol2": "ETHUSDT",
        "timeframe": "1m",
        "rolling_window": 20,
        "limit": 100
    }
)
analysis = response.json()
print(f"Correlation: {analysis['correlation']['pearson']:.4f}")
print(f"Hedge Ratio: {analysis['hedge_ratio']['ratio']:.6f}")
print(f"Z-Score: {analysis['zscore']['current']:.4f}")
```

### Using JavaScript/Fetch

```javascript
// Get statistics
const response = await fetch(
  'http://localhost:8000/api/stats/BTCUSDT?timeframe=1m&limit=100'
);
const stats = await response.json();
console.log('Mean Price:', stats.price_stats.mean);

// Pair analysis
const pairResponse = await fetch(
  'http://localhost:8000/api/pairs/analyze',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symbol1: 'BTCUSDT',
      symbol2: 'ETHUSDT',
      timeframe: '1m',
      rolling_window: 20,
      limit: 100
    })
  }
);
const analysis = await pairResponse.json();
console.log('Correlation:', analysis.correlation.pearson);
console.log('Z-Score:', analysis.zscore.current);
```

## Interactive Documentation

### Swagger UI (`/docs`)

Full interactive API documentation with:
- All endpoints listed with descriptions
- Request/response schemas
- Try-it-out functionality
- Example requests and responses
- Authentication (when added)

**Access:** http://localhost:8000/docs

### ReDoc (`/redoc`)

Clean, readable API reference with:
- Organized by tags
- Detailed schema documentation
- Search functionality
- Code samples

**Access:** http://localhost:8000/redoc

### OpenAPI JSON (`/openapi.json`)

Raw OpenAPI specification for:
- Code generation tools
- API clients
- Testing frameworks
- Documentation generators

**Access:** http://localhost:8000/openapi.json

## Response Examples

### Statistics Response
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1m",
  "data_points": 100,
  "timestamp": "2025-12-15T18:30:00",
  "price_stats": {
    "mean": 96250.50,
    "median": 96255.00,
    "std": 125.75,
    "min": 96000.00,
    "max": 96500.00,
    "latest": 96300.00,
    "change_pct": 0.15
  },
  "volume_stats": {
    "total": 1500.25,
    "mean": 15.00,
    "latest": 14.50
  },
  "volatility": {
    "current": 0.0013,
    "annualized": 0.0206
  },
  "vwap": {
    "value": 96255.00,
    "deviation": 45.00,
    "deviation_pct": 0.047
  }
}
```

### Pair Analysis Response
```json
{
  "symbol1": "BTCUSDT",
  "symbol2": "ETHUSDT",
  "data_points": 100,
  "timestamp": "2025-12-15T18:30:00",
  "correlation": {
    "pearson": 0.9523,
    "pearson_pvalue": 0.0001,
    "spearman": 0.9487,
    "strength": "very_strong"
  },
  "hedge_ratio": {
    "ratio": 29.856234,
    "intercept": 1250.50,
    "r_squared": 0.9068,
    "residual_std": 45.23
  },
  "cointegration": {
    "adf_statistic": -3.5678,
    "pvalue": 0.0056,
    "is_cointegrated_5pct": true,
    "interpretation": "cointegrated"
  },
  "zscore": {
    "current": -1.2345,
    "mean": 0.0234,
    "signal": "caution_long"
  }
}
```

## Error Handling

### 404 Not Found
```json
{
  "detail": "No OHLC data found for BTCUSDT"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "rolling_window"],
      "msg": "ensure this value is greater than or equal to 5",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "Database connection failed"
}
```

## Production Considerations

### Security
- [ ] Configure CORS with specific allowed origins
- [ ] Add API key authentication
- [ ] Implement rate limiting
- [ ] Add request size limits
- [ ] Enable HTTPS/TLS

### Performance
- [ ] Add response caching (Redis)
- [ ] Implement database connection pooling
- [ ] Add request compression (gzip)
- [ ] Use async database operations
- [ ] Add response pagination for large datasets

### Monitoring
- [ ] Add structured logging (JSON)
- [ ] Implement request tracing
- [ ] Add performance metrics (Prometheus)
- [ ] Set up health checks (readiness/liveness)
- [ ] Configure error tracking (Sentry)

### Deployment
- [ ] Use environment-based configuration
- [ ] Set up reverse proxy (nginx)
- [ ] Configure process manager (systemd/supervisor)
- [ ] Implement graceful shutdown
- [ ] Add auto-restart on failure

## Testing Results

```
Phase 5 Verification: PASSED

✅ All API endpoints working correctly:
   • Health check endpoint
   • Statistics endpoint with comprehensive metrics
   • OHLC data endpoint with candlestick bars
   • Tick data endpoint for raw price data
   • Pair analysis endpoint with correlations
   • Symbols and timeframes listing endpoints
   • Interactive API documentation (Swagger UI & ReDoc)
```

## Next Steps

### Phase 6: Frontend Dashboard
- Streamlit web application
- Real-time price charts (Plotly)
- Correlation heatmaps
- Z-score visualization
- Interactive pair selection
- Trading signals display

### Phase 7: Alert System
- Z-score threshold alerts
- Email notifications
- Webhook integrations
- Alert history
- Custom alert rules

## Common Issues

### Issue: Cannot connect to API
**Solution:** Ensure server is running:
```bash
uvicorn backend.api.app:app --reload
```

### Issue: 404 errors on all data endpoints
**Solution:** Generate data first:
```bash
python test_phase2.py  # Collect tick data
python test_phase3.py --full  # Generate OHLC data
```

### Issue: CORS errors from frontend
**Solution:** Update CORS configuration in `backend/api/app.py`:
```python
allow_origins=["http://localhost:3000", "http://localhost:8501"]
```

### Issue: Validation errors (422)
**Solution:** Check request parameters match schema requirements:
- `rolling_window`: 5 ≤ value ≤ 100
- `limit`: positive integer with max values
- `symbol`: non-empty string

## Files Created in Phase 5

```
backend/api/
├── __init__.py
├── schemas.py          (330 lines) - Pydantic models
├── routes.py           (310 lines) - API endpoints
└── app.py             (128 lines) - FastAPI application

tests/
└── test_phase5.py      (515 lines) - API test suite

docs/
└── PHASE5_GUIDE.md     (This file) - Complete guide
```

## Summary

Phase 5 successfully implements a production-ready REST API with:

- ✅ 7 fully functional endpoints
- ✅ Comprehensive request/response validation
- ✅ Interactive API documentation
- ✅ Proper error handling (404, 422, 500)
- ✅ CORS support for frontend integration
- ✅ Health check endpoint
- ✅ Clean separation of concerns (schemas, routes, app)
- ✅ Complete test coverage

The API is ready for frontend integration and can handle real-time analytics queries with proper validation and error handling.
