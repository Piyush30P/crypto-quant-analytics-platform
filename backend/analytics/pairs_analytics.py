"""
Pair trading analytics - correlation, cointegration, hedge ratios, spreads
"""
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from sklearn.linear_model import LinearRegression
from loguru import logger

from backend.analytics.base_analyzer import BaseAnalyzer


class PairsAnalyzer(BaseAnalyzer):
    """
    Analyze relationships between two trading pairs

    Calculations:
    - Correlation (Pearson, Spearman)
    - Cointegration (ADF test)
    - Hedge ratio (OLS regression)
    - Spread calculation
    - Z-score of spread
    - Rolling correlation
    """

    def __init__(self):
        super().__init__(name="PairsAnalyzer")

    def calculate(self, data: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Calculate pair trading metrics

        Args:
            data: DataFrame with columns ['timestamp', 'symbol1_close', 'symbol2_close']
                  OR ['close_x', 'close_y'] for two symbols
            **kwargs: Optional parameters
                - rolling_window: Window for rolling calculations (default: 20)
                - symbol1_name: Name of first symbol
                - symbol2_name: Name of second symbol

        Returns:
            Dictionary with pair analytics
        """
        # Detect column names
        if 'close_x' in data.columns and 'close_y' in data.columns:
            price1_col, price2_col = 'close_x', 'close_y'
        elif len(data.columns) >= 2:
            # Assume first two non-timestamp columns are prices
            price_cols = [c for c in data.columns if c != 'timestamp']
            if len(price_cols) < 2:
                raise ValueError("Need at least 2 price columns")
            price1_col, price2_col = price_cols[0], price_cols[1]
        else:
            raise ValueError("Cannot identify price columns")

        self.validate_data(data, [price1_col, price2_col])

        rolling_window = kwargs.get('rolling_window', 20)
        symbol1_name = kwargs.get('symbol1_name', 'Symbol1')
        symbol2_name = kwargs.get('symbol2_name', 'Symbol2')

        price1 = data[price1_col]
        price2 = data[price2_col]

        results = {
            'timestamp': data['timestamp'].iloc[-1] if 'timestamp' in data.columns else None,
            'symbol1': symbol1_name,
            'symbol2': symbol2_name,
            'data_points': len(data),
            'correlation': self._calculate_correlation(price1, price2),
            'hedge_ratio': self._calculate_hedge_ratio(price1, price2),
            'cointegration': self._test_cointegration(price1, price2),
        }

        # Calculate spread using hedge ratio
        hedge_ratio = results['hedge_ratio']['ratio']
        spread = price1 - (hedge_ratio * price2)

        results['spread'] = self._calculate_spread_stats(spread)
        results['zscore'] = self._calculate_zscore(spread, rolling_window)
        results['rolling_correlation'] = self._calculate_rolling_correlation(
            price1, price2, rolling_window
        )

        return results

    def _calculate_correlation(
        self,
        price1: pd.Series,
        price2: pd.Series
    ) -> Dict[str, float]:
        """Calculate correlation between two price series"""
        pearson_corr, pearson_p = stats.pearsonr(price1, price2)
        spearman_corr, spearman_p = stats.spearmanr(price1, price2)

        return {
            'pearson': float(pearson_corr),
            'pearson_pvalue': float(pearson_p),
            'spearman': float(spearman_corr),
            'spearman_pvalue': float(spearman_p),
            'strength': self._interpret_correlation(pearson_corr)
        }

    def _interpret_correlation(self, corr: float) -> str:
        """Interpret correlation strength"""
        abs_corr = abs(corr)
        if abs_corr >= 0.9:
            return 'very_strong'
        elif abs_corr >= 0.7:
            return 'strong'
        elif abs_corr >= 0.5:
            return 'moderate'
        elif abs_corr >= 0.3:
            return 'weak'
        else:
            return 'very_weak'

    def _calculate_hedge_ratio(
        self,
        price1: pd.Series,
        price2: pd.Series
    ) -> Dict[str, float]:
        """
        Calculate hedge ratio using OLS regression

        Model: price1 = alpha + beta * price2
        Hedge ratio = beta
        """
        # Reshape for sklearn
        X = price2.values.reshape(-1, 1)
        y = price1.values

        # Fit linear regression
        model = LinearRegression()
        model.fit(X, y)

        # Calculate residuals
        predicted = model.predict(X)
        residuals = y - predicted
        residual_std = np.std(residuals)

        # R-squared
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        return {
            'ratio': float(model.coef_[0]),
            'intercept': float(model.intercept_),
            'r_squared': float(r_squared),
            'residual_std': float(residual_std)
        }

    def _test_cointegration(
        self,
        price1: pd.Series,
        price2: pd.Series
    ) -> Dict[str, Any]:
        """
        Test for cointegration using Augmented Dickey-Fuller test

        Tests if spread is stationary (mean-reverting)
        """
        # Calculate spread using simple hedge ratio
        hedge_ratio = price1.mean() / price2.mean()
        spread = price1 - (hedge_ratio * price2)

        # Perform ADF test on spread
        try:
            adf_result = adfuller(spread, autolag='AIC')

            return {
                'adf_statistic': float(adf_result[0]),
                'pvalue': float(adf_result[1]),
                'critical_values': {
                    '1%': float(adf_result[4]['1%']),
                    '5%': float(adf_result[4]['5%']),
                    '10%': float(adf_result[4]['10%'])
                },
                'is_cointegrated_5pct': bool(adf_result[1] < 0.05),
                'is_cointegrated_1pct': bool(adf_result[1] < 0.01),
                'interpretation': self._interpret_adf(adf_result[1])
            }
        except Exception as e:
            logger.error(f"ADF test failed: {e}")
            return {'error': str(e)}

    def _interpret_adf(self, pvalue: float) -> str:
        """Interpret ADF test result"""
        if pvalue < 0.01:
            return 'strongly_cointegrated'
        elif pvalue < 0.05:
            return 'cointegrated'
        elif pvalue < 0.10:
            return 'weakly_cointegrated'
        else:
            return 'not_cointegrated'

    def _calculate_spread_stats(self, spread: pd.Series) -> Dict[str, float]:
        """Calculate statistics for the spread"""
        return {
            'mean': float(spread.mean()),
            'std': float(spread.std()),
            'min': float(spread.min()),
            'max': float(spread.max()),
            'latest': float(spread.iloc[-1]),
            'deviation_from_mean': float(spread.iloc[-1] - spread.mean())
        }

    def _calculate_zscore(
        self,
        spread: pd.Series,
        window: int
    ) -> Dict[str, float]:
        """
        Calculate Z-score of spread

        Z-score = (spread - rolling_mean) / rolling_std
        """
        if len(spread) < window:
            return {'error': f'Need at least {window} data points'}

        rolling_mean = spread.rolling(window=window).mean()
        rolling_std = spread.rolling(window=window).std()

        zscore = (spread - rolling_mean) / rolling_std

        latest_zscore = zscore.iloc[-1]

        return {
            'current': float(latest_zscore) if not np.isnan(latest_zscore) else None,
            'mean': float(zscore.mean()),
            'std': float(zscore.std()),
            'min': float(zscore.min()),
            'max': float(zscore.max()),
            'signal': self._interpret_zscore(latest_zscore)
        }

    def _interpret_zscore(self, zscore: float) -> str:
        """Interpret Z-score for trading signals"""
        if np.isnan(zscore):
            return 'unknown'
        elif zscore > 2.0:
            return 'short_signal'  # Spread too high, mean reversion expected
        elif zscore > 1.0:
            return 'caution_short'
        elif zscore < -2.0:
            return 'long_signal'  # Spread too low, mean reversion expected
        elif zscore < -1.0:
            return 'caution_long'
        else:
            return 'neutral'

    def _calculate_rolling_correlation(
        self,
        price1: pd.Series,
        price2: pd.Series,
        window: int
    ) -> Dict[str, Any]:
        """Calculate rolling correlation"""
        if len(price1) < window:
            return {'error': f'Need at least {window} data points'}

        rolling_corr = price1.rolling(window=window).corr(price2)

        return {
            'current': float(rolling_corr.iloc[-1]) if not np.isnan(rolling_corr.iloc[-1]) else None,
            'mean': float(rolling_corr.mean()),
            'std': float(rolling_corr.std()),
            'min': float(rolling_corr.min()),
            'max': float(rolling_corr.max())
        }

    def calculate_optimal_hedge_ratio_kalman(
        self,
        price1: pd.Series,
        price2: pd.Series
    ) -> Dict[str, Any]:
        """
        Calculate dynamic hedge ratio using Kalman filter

        (Advanced feature - for future implementation)
        """
        # Placeholder for Kalman filter implementation
        logger.warning("Kalman filter not yet implemented, using OLS instead")
        return self._calculate_hedge_ratio(price1, price2)
