"""
Configuration settings for the Crypto Analytics Platform
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "Crypto Analytics Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # Frontend Settings
    FRONTEND_HOST: str = "localhost"
    FRONTEND_PORT: int = 8501
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./crypto_analytics.db"
    DATABASE_ECHO: bool = False
    
    # Redis Settings (optional, fallback to in-memory if not available)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_ENABLED: bool = False
    
    # Binance WebSocket
    BINANCE_WS_BASE_URL: str = "wss://stream.binance.com:9443/ws"
    BINANCE_REST_BASE_URL: str = "https://api.binance.com/api/v3"
    
    # Default Trading Pairs
    DEFAULT_SYMBOLS: List[str] = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    
    # Data Resampling
    RESAMPLE_INTERVALS: List[str] = ["1S", "1T", "5T"]  # 1 second, 1 minute, 5 minutes
    RESAMPLE_INTERVAL_NAMES: List[str] = ["1s", "1m", "5m"]
    
    # Analytics Settings
    DEFAULT_ROLLING_WINDOW: int = 20
    MAX_ROLLING_WINDOW: int = 200
    MIN_DATA_POINTS_FOR_ANALYTICS: int = 30
    
    # Alert Settings
    ALERT_CHECK_INTERVAL: int = 5  # seconds
    MAX_ALERTS_PER_USER: int = 10
    
    # Data Retention
    TICK_DATA_RETENTION_DAYS: int = 7
    OHLC_DATA_RETENTION_DAYS: int = 30
    
    # Performance
    TICK_BUFFER_SIZE: int = 1000
    BATCH_INSERT_SIZE: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Export
    EXPORT_DIR: Path = BASE_DIR / "exports"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Create necessary directories
os.makedirs(settings.EXPORT_DIR, exist_ok=True)
os.makedirs(BASE_DIR / "logs", exist_ok=True)
os.makedirs(BASE_DIR / "data", exist_ok=True)
