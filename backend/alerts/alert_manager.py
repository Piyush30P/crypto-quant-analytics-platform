"""
Alert Manager - Coordinates alert checking and triggering
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import json

from backend.alerts.alert_storage import (
    AlertRule, AlertType, AlertRuleRepository, AlertHistoryRepository
)
from backend.alerts.notification_service import send_alert_notifications
from backend.storage.ohlc_repository import OHLCRepository
from backend.analytics.pairs_analytics import PairsAnalyzer
import pandas as pd


def make_json_serializable(obj):
    """Convert non-JSON-serializable objects to serializable formats"""
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj)


class AlertManager:
    """Manages alert checking and triggering"""

    def __init__(self):
        self.rule_repo = AlertRuleRepository()
        self.history_repo = AlertHistoryRepository()
        self.ohlc_repo = OHLCRepository()
        self.pairs_analyzer = PairsAnalyzer()

    def check_all_rules(self) -> Dict[str, Any]:
        """
        Check all active alert rules

        Returns:
            Summary of checks performed
        """
        logger.info("Checking all active alert rules...")

        rules = self.rule_repo.get_active_rules()

        summary = {
            'total_rules': len(rules),
            'triggered': 0,
            'skipped': 0,
            'errors': 0,
            'timestamp': datetime.now().isoformat()
        }

        for rule in rules:
            try:
                # Check if rule is in cooldown period
                if self._is_in_cooldown(rule):
                    summary['skipped'] += 1
                    continue

                # Check rule based on type
                triggered = False

                if rule['alert_type'] == AlertType.ZSCORE_THRESHOLD.value:
                    triggered = self._check_zscore_rule(rule)

                # Add more alert types here in the future
                # elif rule['alert_type'] == AlertType.CORRELATION_CHANGE.value:
                #     triggered = self._check_correlation_rule(rule)

                if triggered:
                    summary['triggered'] += 1

            except Exception as e:
                logger.error(f"Error checking rule {rule['id']}: {e}")
                summary['errors'] += 1

        logger.info(f"Alert check complete: {summary}")
        return summary

    def _is_in_cooldown(self, rule: Dict[str, Any]) -> bool:
        """Check if rule is in cooldown period"""
        last_triggered = rule.get('last_triggered_at')
        if not last_triggered:
            return False

        last_triggered_dt = datetime.fromisoformat(last_triggered)
        cooldown_minutes = rule.get('cooldown_minutes', 15)
        cooldown_period = timedelta(minutes=cooldown_minutes)

        return datetime.now() - last_triggered_dt < cooldown_period

    def _check_zscore_rule(self, rule: Dict[str, Any]) -> bool:
        """
        Check Z-score threshold rule

        Returns:
            True if alert was triggered, False otherwise
        """
        try:
            symbol1 = rule['symbol1']
            symbol2 = rule['symbol2']
            timeframe = rule['timeframe']
            threshold_upper = rule.get('threshold_upper')
            threshold_lower = rule.get('threshold_lower')

            if not symbol2:
                logger.warning(f"Z-score rule {rule['id']} missing symbol2")
                return False

            # Fetch OHLC data for both symbols
            bars1 = self.ohlc_repo.get_recent_ohlc(symbol1, timeframe, limit=100)
            bars2 = self.ohlc_repo.get_recent_ohlc(symbol2, timeframe, limit=100)

            if not bars1 or not bars2:
                logger.debug(f"Insufficient data for {symbol1}/{symbol2}")
                return False

            # Prepare data for analysis
            df1 = pd.DataFrame(bars1)[['timestamp', 'close']].rename(columns={'close': 'close_x'})
            df2 = pd.DataFrame(bars2)[['timestamp', 'close']].rename(columns={'close': 'close_y'})
            merged = pd.merge(df1, df2, on='timestamp', how='inner')

            if len(merged) < 20:
                logger.debug(f"Not enough aligned data: {len(merged)} points")
                return False

            # Calculate pair analytics
            rolling_window = min(20, len(merged) // 2)
            analysis = self.pairs_analyzer.safe_calculate(
                merged,
                rolling_window=rolling_window,
                symbol1_name=symbol1,
                symbol2_name=symbol2
            )

            if 'error' in analysis:
                logger.debug(f"Analysis error: {analysis['error']}")
                return False

            # Get Z-score
            zscore_data = analysis.get('zscore', {})
            if 'error' in zscore_data:
                return False

            zscore = zscore_data.get('current')
            if zscore is None:
                return False

            # Check thresholds
            triggered = False
            threshold_breached = None
            signal = zscore_data.get('signal', 'neutral')

            if threshold_upper is not None and zscore >= threshold_upper:
                triggered = True
                threshold_breached = threshold_upper
                logger.info(f"Z-score alert triggered: {symbol1}/{symbol2} Z={zscore:.4f} >= {threshold_upper}")

            elif threshold_lower is not None and zscore <= threshold_lower:
                triggered = True
                threshold_breached = threshold_lower
                logger.info(f"Z-score alert triggered: {symbol1}/{symbol2} Z={zscore:.4f} <= {threshold_lower}")

            if triggered:
                # Prepare alert data
                correlation = analysis.get('correlation', {})
                hedge_ratio = analysis.get('hedge_ratio', {})

                # Convert analysis to JSON-serializable format
                serializable_analysis = make_json_serializable(analysis)

                alert_data = {
                    'symbol1': symbol1,
                    'symbol2': symbol2,
                    'zscore': zscore,
                    'threshold': threshold_breached,
                    'signal': signal,
                    'correlation': correlation.get('pearson'),
                    'hedge_ratio': hedge_ratio.get('ratio'),
                    'context_data': {
                        'analysis': serializable_analysis,
                        'data_points': len(merged)
                    }
                }

                # Send notifications
                notifications_sent, notification_errors = send_alert_notifications(
                    alert_data,
                    rule['notification_channels'],
                    rule['notification_config']
                )

                # Record in history
                self.history_repo.create_history(
                    rule_id=rule['id'],
                    alert_type=AlertType.ZSCORE_THRESHOLD,
                    symbol1=symbol1,
                    symbol2=symbol2,
                    trigger_value=zscore,
                    threshold_breached=threshold_breached,
                    context_data=alert_data['context_data'],
                    notifications_sent=notifications_sent,
                    notification_errors=notification_errors
                )

                # Update rule
                self.rule_repo.update_rule_triggered(rule['id'])

                return True

            return False

        except Exception as e:
            logger.error(f"Error checking Z-score rule: {e}")
            return False

    def get_rule_status(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """Get status of a specific rule"""
        try:
            rules = self.rule_repo.get_active_rules()
            for rule in rules:
                if rule['id'] == rule_id:
                    return rule
            return None
        except Exception as e:
            logger.error(f"Error getting rule status: {e}")
            return None

    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alert history"""
        try:
            return self.history_repo.get_recent_history(limit=limit)
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []


# Singleton instance
_alert_manager = None


def get_alert_manager() -> AlertManager:
    """Get or create alert manager singleton"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
