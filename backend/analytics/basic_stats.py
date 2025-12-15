"""
Basic statistical calculations for price and volume data
"""
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from loguru import logger

from backend.analytics.base_analyzer import BaseAnalyzer


class BasicStatsCalculator(BaseAnalyzer):
    """
    Calculate basic statistical metrics for price/volume data

    Metrics:
    - Mean, median, mode
    - Standard deviation, variance
    - Min, max, range
    - VWAP (Volume Weighted Average Price)
    - Volume profiles
    - Returns and volatility
    """

    def __init__(self):
        super().__init__(name="BasicStats")

    def calculate(self, data: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Calculate basic statistics

        Args:
            data: DataFrame with columns ['timestamp', 'close', 'volume', 'high', 'low']
            **kwargs: Optional parameters
                - rolling_window: Window size for rolling stats

        Returns:
            Dictionary with statistics
        """
        self.validate_data(data, ['close', 'volume'])

        rolling_window = kwargs.get('rolling_window', 20)

        results = {
            'timestamp': data['timestamp'].iloc[-1] if 'timestamp' in data.columns else None,
            'data_points': len(data),
            'price_stats': self._calculate_price_stats(data),
            'volume_stats': self._calculate_volume_stats(data),
            'returns': self._calculate_returns(data),
            'volatility': self._calculate_volatility(data, rolling_window),
        }

        # Add VWAP if we have volume data
        if 'volume' in data.columns:
            results['vwap'] = self._calculate_vwap(data)

        # Add range stats if we have high/low
        if 'high' in data.columns and 'low' in data.columns:
            results['range_stats'] = self._calculate_range_stats(data)

        return results

    def _calculate_price_stats(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate price statistics"""
        prices = data['close']

        return {
            'mean': float(prices.mean()),
            'median': float(prices.median()),
            'std': float(prices.std()),
            'variance': float(prices.var()),
            'min': float(prices.min()),
            'max': float(prices.max()),
            'range': float(prices.max() - prices.min()),
            'latest': float(prices.iloc[-1]),
            'first': float(prices.iloc[0]),
            'change': float(prices.iloc[-1] - prices.iloc[0]),
            'change_pct': float(((prices.iloc[-1] / prices.iloc[0]) - 1) * 100)
        }

    def _calculate_volume_stats(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate volume statistics"""
        if 'volume' not in data.columns:
            return {}

        volume = data['volume']

        return {
            'total': float(volume.sum()),
            'mean': float(volume.mean()),
            'median': float(volume.median()),
            'std': float(volume.std()),
            'min': float(volume.min()),
            'max': float(volume.max()),
            'latest': float(volume.iloc[-1])
        }

    def _calculate_returns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate returns"""
        prices = data['close']
        returns = prices.pct_change().dropna()

        if len(returns) == 0:
            return {'error': 'Not enough data for returns'}

        return {
            'mean': float(returns.mean()),
            'std': float(returns.std()),
            'min': float(returns.min()),
            'max': float(returns.max()),
            'latest': float(returns.iloc[-1]) if len(returns) > 0 else None,
            'cumulative': float((prices.iloc[-1] / prices.iloc[0]) - 1)
        }

    def _calculate_volatility(self, data: pd.DataFrame, window: int) -> Dict[str, float]:
        """Calculate volatility metrics"""
        prices = data['close']
        returns = prices.pct_change().dropna()

        if len(returns) < window:
            return {'error': f'Need at least {window} data points'}

        rolling_std = returns.rolling(window=window).std()

        return {
            'current': float(rolling_std.iloc[-1]) if len(rolling_std) > 0 else None,
            'mean': float(rolling_std.mean()),
            'max': float(rolling_std.max()),
            'min': float(rolling_std.min()),
            'annualized': float(returns.std() * np.sqrt(252))  # Assuming daily data
        }

    def _calculate_vwap(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate VWAP"""
        if 'volume' not in data.columns:
            return {}

        # Use close price if no explicit price column
        price = data['close']
        volume = data['volume']

        vwap = (price * volume).sum() / volume.sum()

        return {
            'value': float(vwap),
            'deviation': float(price.iloc[-1] - vwap),
            'deviation_pct': float(((price.iloc[-1] / vwap) - 1) * 100)
        }

    def _calculate_range_stats(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate high/low range statistics"""
        highs = data['high']
        lows = data['low']
        closes = data['close']

        ranges = highs - lows
        range_pct = (ranges / closes) * 100

        return {
            'avg_range': float(ranges.mean()),
            'avg_range_pct': float(range_pct.mean()),
            'max_range': float(ranges.max()),
            'latest_range': float(ranges.iloc[-1]),
            'latest_range_pct': float(range_pct.iloc[-1])
        }

    def calculate_rolling_stats(
        self,
        data: pd.DataFrame,
        window: int = 20,
        metric: str = 'mean'
    ) -> pd.Series:
        """
        Calculate rolling statistics

        Args:
            data: DataFrame with price data
            window: Rolling window size
            metric: Statistic to calculate ('mean', 'std', 'min', 'max')

        Returns:
            Series with rolling statistic
        """
        self.validate_data(data, ['close'])

        prices = data['close']

        if metric == 'mean':
            return prices.rolling(window=window).mean()
        elif metric == 'std':
            return prices.rolling(window=window).std()
        elif metric == 'min':
            return prices.rolling(window=window).min()
        elif metric == 'max':
            return prices.rolling(window=window).max()
        else:
            raise ValueError(f"Unknown metric: {metric}")
