"""
Pydantic schemas for API request/response validation
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== Request Models ====================

class SymbolRequest(BaseModel):
    """Request model for symbol-based queries"""
    symbol: str = Field(..., description="Trading pair symbol (e.g., BTCUSDT)")
    timeframe: Optional[str] = Field("1m", description="Timeframe (1s, 1m, 5m, etc.)")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Number of records to return")


class PairAnalysisRequest(BaseModel):
    """Request model for pair trading analysis"""
    symbol1: str = Field(..., description="First trading pair (e.g., BTCUSDT)")
    symbol2: str = Field(..., description="Second trading pair (e.g., ETHUSDT)")
    timeframe: Optional[str] = Field("1m", description="Timeframe for analysis")
    rolling_window: Optional[int] = Field(20, ge=5, le=100, description="Rolling window size")
    limit: Optional[int] = Field(100, ge=10, le=500, description="Number of bars to analyze")


class TimeRangeRequest(BaseModel):
    """Request model for time range queries"""
    symbol: str = Field(..., description="Trading pair symbol")
    start_time: datetime = Field(..., description="Start time (ISO format)")
    end_time: datetime = Field(..., description="End time (ISO format)")
    timeframe: Optional[str] = Field("1m", description="Timeframe")


class ExportRequest(BaseModel):
    """Request model for data export"""
    data_type: str = Field(..., description="Type of data (ticks, ohlc, analytics)")
    symbol: Optional[str] = Field(None, description="Trading pair symbol")
    timeframe: Optional[str] = Field("1m", description="Timeframe (for OHLC)")
    format: Optional[str] = Field("json", description="Export format (json, csv)")
    limit: Optional[int] = Field(1000, ge=1, le=10000, description="Number of records")


# ==================== Response Models ====================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    database_connected: bool
    components: Dict[str, str]


class PriceStats(BaseModel):
    """Price statistics model"""
    mean: float
    median: float
    std: float
    min: float
    max: float
    range: float
    latest: float
    first: float
    change: float
    change_pct: float


class VolumeStats(BaseModel):
    """Volume statistics model"""
    total: float
    mean: float
    median: float
    std: float
    min: float
    max: float
    latest: float


class ReturnsStats(BaseModel):
    """Returns statistics model"""
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    latest: Optional[float] = None
    cumulative: Optional[float] = None
    error: Optional[str] = None


class VolatilityStats(BaseModel):
    """Volatility statistics model"""
    current: Optional[float] = None
    mean: Optional[float] = None
    max: Optional[float] = None
    min: Optional[float] = None
    annualized: Optional[float] = None
    error: Optional[str] = None


class VWAPStats(BaseModel):
    """VWAP statistics model"""
    value: float
    deviation: float
    deviation_pct: float


class BasicStatsResponse(BaseModel):
    """Response model for basic statistics"""
    symbol: str
    timeframe: str
    timestamp: Optional[datetime] = None
    data_points: int
    price_stats: PriceStats
    volume_stats: Optional[VolumeStats] = None
    returns: Optional[ReturnsStats] = None
    volatility: Optional[VolatilityStats] = None
    vwap: Optional[VWAPStats] = None


class CorrelationStats(BaseModel):
    """Correlation statistics model"""
    pearson: Optional[float] = None
    pearson_pvalue: Optional[float] = None
    spearman: Optional[float] = None
    spearman_pvalue: Optional[float] = None
    strength: Optional[str] = None
    error: Optional[str] = None


class HedgeRatioStats(BaseModel):
    """Hedge ratio statistics model"""
    ratio: Optional[float] = None
    intercept: Optional[float] = None
    r_squared: Optional[float] = None
    residual_std: Optional[float] = None
    error: Optional[str] = None


class CointegrationStats(BaseModel):
    """Cointegration test results model"""
    adf_statistic: Optional[float] = None
    pvalue: Optional[float] = None
    critical_values: Optional[Dict[str, float]] = None
    is_cointegrated_5pct: Optional[bool] = None
    is_cointegrated_1pct: Optional[bool] = None
    interpretation: Optional[str] = None
    error: Optional[str] = None


class SpreadStats(BaseModel):
    """Spread statistics model"""
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    latest: Optional[float] = None
    deviation_from_mean: Optional[float] = None
    error: Optional[str] = None


class ZScoreStats(BaseModel):
    """Z-score statistics model"""
    current: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    signal: Optional[str] = None
    error: Optional[str] = None


class RollingCorrelationStats(BaseModel):
    """Rolling correlation statistics model"""
    current: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    error: Optional[str] = None


class PairAnalysisResponse(BaseModel):
    """Response model for pair trading analysis"""
    symbol1: str
    symbol2: str
    timeframe: str
    timestamp: Optional[datetime] = None
    data_points: int
    correlation: Optional[CorrelationStats] = None
    hedge_ratio: Optional[HedgeRatioStats] = None
    cointegration: Optional[CointegrationStats] = None
    spread: Optional[SpreadStats] = None
    zscore: Optional[ZScoreStats] = None
    rolling_correlation: Optional[RollingCorrelationStats] = None


class OHLCBar(BaseModel):
    """OHLC bar model"""
    timestamp: datetime
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: int
    vwap: Optional[float]


class OHLCResponse(BaseModel):
    """Response model for OHLC data"""
    symbol: str
    timeframe: str
    bars: List[OHLCBar]
    count: int


class TickData(BaseModel):
    """Tick data model"""
    timestamp: datetime
    symbol: str
    price: float
    quantity: float
    volume: float


class TicksResponse(BaseModel):
    """Response model for tick data"""
    symbol: str
    ticks: List[TickData]
    count: int


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
