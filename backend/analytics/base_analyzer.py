"""
Base class for analytics calculators
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
from loguru import logger


class BaseAnalyzer(ABC):
    """
    Abstract base class for all analytics calculators

    Provides common functionality:
    - Data validation
    - Result caching
    - Error handling
    - Logging
    """

    def __init__(self, name: str):
        """
        Initialize the analyzer

        Args:
            name: Name of the analyzer (for logging/caching)
        """
        self.name = name
        self.last_calculation_time: Optional[datetime] = None
        self.cache: Dict[str, Any] = {}

        logger.debug(f"Initialized {self.name} analyzer")

    @abstractmethod
    def calculate(self, data: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Perform the calculation

        Args:
            data: DataFrame with price/volume data
            **kwargs: Additional parameters specific to the analyzer

        Returns:
            Dictionary with calculation results
        """
        pass

    def validate_data(self, data: pd.DataFrame, required_columns: list) -> bool:
        """
        Validate input data

        Args:
            data: DataFrame to validate
            required_columns: List of required column names

        Returns:
            True if valid, raises ValueError if not
        """
        if data is None or data.empty:
            raise ValueError(f"{self.name}: Data is empty")

        missing_cols = set(required_columns) - set(data.columns)
        if missing_cols:
            raise ValueError(
                f"{self.name}: Missing required columns: {missing_cols}"
            )

        if len(data) < 2:
            raise ValueError(
                f"{self.name}: Need at least 2 data points, got {len(data)}"
            )

        return True

    def safe_calculate(self, data: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Wrapper for calculate() with error handling

        Args:
            data: Input data
            **kwargs: Additional parameters

        Returns:
            Results dictionary or error dict
        """
        try:
            result = self.calculate(data, **kwargs)
            self.last_calculation_time = datetime.now()
            return result

        except Exception as e:
            logger.error(f"{self.name} calculation error: {e}")
            return {
                'error': str(e),
                'analyzer': self.name,
                'timestamp': datetime.now()
            }

    def get_cache_key(self, **kwargs) -> str:
        """
        Generate cache key from parameters

        Args:
            **kwargs: Parameters to hash

        Returns:
            Cache key string
        """
        params = '_'.join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"{self.name}_{params}"

    def clear_cache(self):
        """Clear the cache"""
        self.cache.clear()
        logger.debug(f"Cleared cache for {self.name}")
