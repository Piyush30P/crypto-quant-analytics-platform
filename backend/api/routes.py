"""
Main API routes for the Crypto Analytics Platform
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from loguru import logger
import pandas as pd
import math
import io

from backend.api.schemas import (
    HealthResponse,
    BasicStatsResponse,
    PairAnalysisResponse,
    OHLCResponse,
    TicksResponse,
    ErrorResponse,
    SymbolRequest,
    PairAnalysisRequest,
    OHLCBar,
    TickData,
    PriceStats,
    VolumeStats,
    ReturnsStats,
    VolatilityStats,
    VWAPStats,
    CorrelationStats,
    HedgeRatioStats,
    CointegrationStats,
    SpreadStats,
    ZScoreStats,
    RollingCorrelationStats
)
from backend.storage.ohlc_repository import OHLCRepository
from backend.storage.tick_repository import TickDataRepository
from backend.analytics.basic_stats import BasicStatsCalculator
from backend.analytics.pairs_analytics import PairsAnalyzer
from config.settings import settings

# Helper function to sanitize NaN/Inf values for JSON serialization
def sanitize_float_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively replace NaN and Inf values with None for JSON serialization
    """
    if isinstance(data, dict):
        return {k: sanitize_float_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_float_values(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    else:
        return data


# Create router
router = APIRouter(prefix="/api", tags=["analytics"])

# Initialize repositories and analyzers
ohlc_repo = OHLCRepository()
tick_repo = TickDataRepository()
basic_stats_calc = BasicStatsCalculator()
pairs_analyzer = PairsAnalyzer()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns system status and component health
    """
    try:
        # Test database connection
        db_connected = True
        try:
            tick_repo.get_tick_count()
        except Exception:
            db_connected = False

        return HealthResponse(
            status="healthy" if db_connected else "degraded",
            version=settings.APP_VERSION,
            timestamp=datetime.now(),
            database_connected=db_connected,
            components={
                "database": "operational" if db_connected else "error",
                "analytics": "operational",
                "api": "operational"
            }
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{symbol}", response_model=BasicStatsResponse)
async def get_statistics(
    symbol: str,
    timeframe: str = Query("1m", description="Timeframe (1s, 1m, 5m)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of bars"),
    rolling_window: int = Query(20, ge=5, le=100, description="Rolling window size")
):
    """
    Get basic statistics for a symbol

    Calculates comprehensive statistics including:
    - Price stats (mean, std, range)
    - Volume analysis
    - Returns and volatility
    - VWAP
    """
    try:
        # Fetch OHLC data
        bars = ohlc_repo.get_recent_ohlc(symbol.upper(), timeframe, limit)

        if not bars:
            raise HTTPException(
                status_code=404,
                detail=f"No OHLC data found for {symbol} ({timeframe})"
            )

        # Convert to DataFrame
        df = pd.DataFrame(bars)

        # Calculate statistics
        stats = basic_stats_calc.safe_calculate(df, rolling_window=rolling_window)

        if 'error' in stats:
            raise HTTPException(status_code=500, detail=stats['error'])

        # Build response, handling error cases in nested stats
        volatility_data = stats.get('volatility', {})
        if 'error' in volatility_data:
            volatility = VolatilityStats(error=volatility_data['error'])
        else:
            volatility = VolatilityStats(**volatility_data)

        returns_data = stats.get('returns', {})
        if 'error' in returns_data:
            returns = ReturnsStats(error=returns_data['error'])
        else:
            returns = ReturnsStats(**returns_data)

        return BasicStatsResponse(
            symbol=symbol.upper(),
            timeframe=timeframe,
            timestamp=stats.get('timestamp'),
            data_points=stats['data_points'],
            price_stats=PriceStats(**stats['price_stats']),
            volume_stats=VolumeStats(**stats['volume_stats']) if stats.get('volume_stats') and 'error' not in stats.get('volume_stats', {}) else None,
            returns=returns,
            volatility=volatility,
            vwap=VWAPStats(**stats['vwap']) if stats.get('vwap') and 'error' not in stats.get('vwap', {}) else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting statistics for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ohlc/{symbol}", response_model=OHLCResponse)
async def get_ohlc(
    symbol: str,
    timeframe: str = Query("1m", description="Timeframe"),
    limit: int = Query(100, ge=1, le=1000, description="Number of bars")
):
    """
    Get OHLC (candlestick) data for a symbol

    Returns historical OHLC bars with volume and VWAP
    """
    try:
        bars = ohlc_repo.get_recent_ohlc(symbol.upper(), timeframe, limit)

        if not bars:
            raise HTTPException(
                status_code=404,
                detail=f"No OHLC data found for {symbol} ({timeframe})"
            )

        ohlc_bars = [OHLCBar(**bar) for bar in bars]

        return OHLCResponse(
            symbol=symbol.upper(),
            timeframe=timeframe,
            bars=ohlc_bars,
            count=len(ohlc_bars)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting OHLC for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticks/{symbol}", response_model=TicksResponse)
async def get_ticks(
    symbol: str,
    limit: int = Query(100, ge=1, le=5000, description="Number of ticks")
):
    """
    Get raw tick data for a symbol

    Returns recent tick-level price data
    """
    try:
        ticks = tick_repo.get_recent_ticks(symbol.upper(), limit)

        if not ticks:
            raise HTTPException(
                status_code=404,
                detail=f"No tick data found for {symbol}"
            )

        tick_data = [TickData(**tick) for tick in ticks]

        return TicksResponse(
            symbol=symbol.upper(),
            ticks=tick_data,
            count=len(tick_data)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ticks for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pairs/analyze", response_model=PairAnalysisResponse)
async def analyze_pair(request: PairAnalysisRequest):
    """
    Analyze a trading pair for statistical arbitrage

    Calculates:
    - Correlation (Pearson & Spearman)
    - Hedge ratio (OLS regression)
    - Cointegration (ADF test)
    - Spread and Z-score
    - Trading signals
    """
    try:
        symbol1 = request.symbol1.upper()
        symbol2 = request.symbol2.upper()

        # Fetch OHLC data for both symbols
        bars1 = ohlc_repo.get_recent_ohlc(symbol1, request.timeframe, request.limit)
        bars2 = ohlc_repo.get_recent_ohlc(symbol2, request.timeframe, request.limit)

        if not bars1 or not bars2:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient OHLC data for {symbol1} or {symbol2}"
            )

        # Convert to DataFrames
        df1 = pd.DataFrame(bars1)[['timestamp', 'close']].rename(columns={'close': 'close_x'})
        df2 = pd.DataFrame(bars2)[['timestamp', 'close']].rename(columns={'close': 'close_y'})

        # Merge on timestamp
        merged = pd.merge(df1, df2, on='timestamp', how='inner')

        if len(merged) < 5:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough aligned data points: {len(merged)} (need at least 5)"
            )

        # Adjust rolling window
        actual_window = min(request.rolling_window, max(len(merged) // 2, 5))

        # Calculate pair analytics
        analysis = pairs_analyzer.safe_calculate(
            merged,
            rolling_window=actual_window,
            symbol1_name=symbol1,
            symbol2_name=symbol2
        )

        if 'error' in analysis:
            raise HTTPException(status_code=500, detail=analysis['error'])

        # Sanitize NaN/Inf values before creating response
        analysis = sanitize_float_values(analysis)

        # Build response
        return PairAnalysisResponse(
            symbol1=symbol1,
            symbol2=symbol2,
            timeframe=request.timeframe,
            timestamp=analysis.get('timestamp'),
            data_points=analysis['data_points'],
            correlation=CorrelationStats(**analysis['correlation']) if analysis.get('correlation') else None,
            hedge_ratio=HedgeRatioStats(**analysis['hedge_ratio']) if analysis.get('hedge_ratio') else None,
            cointegration=CointegrationStats(**analysis['cointegration']) if analysis.get('cointegration') and 'error' not in analysis['cointegration'] else None,
            spread=SpreadStats(**analysis['spread']) if analysis.get('spread') else None,
            zscore=ZScoreStats(**analysis['zscore']) if analysis.get('zscore') and 'error' not in analysis['zscore'] else None,
            rolling_correlation=RollingCorrelationStats(**analysis['rolling_correlation']) if analysis.get('rolling_correlation') and 'error' not in analysis['rolling_correlation'] else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing pair {request.symbol1}/{request.symbol2}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbols", response_model=List[str])
async def get_available_symbols():
    """
    Get list of available trading symbols

    Returns all symbols with tick or OHLC data
    """
    try:
        symbols = tick_repo.get_available_symbols()
        return sorted(symbols) if symbols else []

    except Exception as e:
        logger.error(f"Error getting available symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeframes/{symbol}", response_model=List[str])
async def get_available_timeframes(symbol: str):
    """
    Get available timeframes for a symbol

    Returns list of timeframes with OHLC data
    """
    try:
        timeframes = ohlc_repo.get_available_timeframes(symbol.upper())
        return sorted(timeframes) if timeframes else []

    except Exception as e:
        logger.error(f"Error getting timeframes for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/ohlc")
async def upload_ohlc_csv(
    file: UploadFile = File(...),
    symbol: str = Form(...),
    timeframe: str = Form(...)
):
    """
    Upload historical OHLC data from CSV file

    CSV should contain columns: timestamp, open, high, low, close, volume (optional)

    Example:
    ```
    timestamp,open,high,low,close,volume
    2024-01-01 00:00:00,42000.50,42100.00,41900.00,42050.75,1234.56
    ```
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")

        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        # Validate required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}"
            )

        # Parse timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Add volume if missing
        if 'volume' not in df.columns:
            df['volume'] = 0.0

        # Calculate VWAP if volume exists
        if df['volume'].sum() > 0:
            df['vwap'] = ((df['high'] + df['low'] + df['close']) / 3 * df['volume']).cumsum() / df['volume'].cumsum()
        else:
            df['vwap'] = (df['high'] + df['low'] + df['close']) / 3

        # Insert into database
        rows_inserted = 0
        for _, row in df.iterrows():
            try:
                ohlc_repo.insert_ohlc(
                    symbol=symbol.upper(),
                    timeframe=timeframe,
                    timestamp=row['timestamp'],
                    open_price=float(row['open']),
                    high_price=float(row['high']),
                    low_price=float(row['low']),
                    close_price=float(row['close']),
                    volume=float(row.get('volume', 0)),
                    vwap=float(row.get('vwap', (row['high'] + row['low'] + row['close']) / 3))
                )
                rows_inserted += 1
            except Exception as e:
                logger.warning(f"Error inserting row: {e}")
                continue

        logger.info(f"Uploaded {rows_inserted}/{len(df)} OHLC rows for {symbol} ({timeframe})")

        return {
            "success": True,
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "rows_total": len(df),
            "rows_inserted": rows_inserted,
            "message": f"Successfully uploaded {rows_inserted} rows"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading OHLC CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))
