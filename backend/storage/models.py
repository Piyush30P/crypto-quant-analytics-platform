"""
Database models for the Crypto Analytics Platform
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, 
    Boolean, Text, Index, BigInteger, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class TickData(Base):
    """Raw tick data from WebSocket streams"""
    __tablename__ = "tick_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<TickData(symbol={self.symbol}, price={self.price}, timestamp={self.timestamp})>"


class OHLC(Base):
    """OHLC candlestick data at different timeframes"""
    __tablename__ = "ohlc_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)  # 1s, 1m, 5m
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    trade_count = Column(Integer, default=0)
    vwap = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index('idx_ohlc_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<OHLC(symbol={self.symbol}, timeframe={self.timeframe}, close={self.close})>"


class AnalyticsCache(Base):
    """Cache for computed analytics to avoid recalculation"""
    __tablename__ = "analytics_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(200), unique=True, nullable=False, index=True)
    symbol_pair = Column(String(50), nullable=True, index=True)
    timeframe = Column(String(10), nullable=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(JSON, nullable=True)  # Can store dict, list, or single value
    computed_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<AnalyticsCache(key={self.cache_key}, metric={self.metric_name})>"


# NOTE: Alert and AlertHistory models moved to backend/alerts/alert_storage.py (Phase 7)
# Old models removed to prevent schema conflicts with Phase 7 alert system


class UploadedData(Base):
    """Track uploaded OHLC CSV files"""
    __tablename__ = "uploaded_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    row_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, server_default=func.now())
    uploaded_by = Column(String(100), default="system")
    
    def __repr__(self):
        return f"<UploadedData(filename={self.filename}, symbol={self.symbol})>"
