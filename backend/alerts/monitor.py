"""
Background monitoring task for checking alerts
"""
import asyncio
import threading
from datetime import datetime
from typing import Optional
from loguru import logger

from backend.alerts.alert_manager import get_alert_manager


class AlertMonitor:
    """Background monitor for checking alerts"""

    def __init__(self, check_interval_seconds: int = 60):
        """
        Initialize alert monitor

        Args:
            check_interval_seconds: How often to check alerts (default: 60 seconds)
        """
        self.check_interval = check_interval_seconds
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.alert_manager = get_alert_manager()

    def start(self):
        """Start the monitoring thread"""
        if self.running:
            logger.warning("Alert monitor is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info(f"Alert monitor started (check interval: {self.check_interval}s)")

    def stop(self):
        """Stop the monitoring thread"""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Alert monitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Alert monitor loop starting...")

        while self.running:
            try:
                # Check all rules
                summary = self.alert_manager.check_all_rules()

                logger.debug(
                    f"Alert check: {summary['triggered']} triggered, "
                    f"{summary['skipped']} skipped, {summary['errors']} errors"
                )

            except Exception as e:
                logger.error(f"Error in alert monitor loop: {e}")

            # Sleep for interval
            for _ in range(self.check_interval):
                if not self.running:
                    break
                import time
                time.sleep(1)

        logger.info("Alert monitor loop stopped")

    def check_now(self) -> dict:
        """
        Manually trigger an alert check

        Returns:
            Summary of the check
        """
        logger.info("Manual alert check triggered")
        return self.alert_manager.check_all_rules()


# Global monitor instance
_monitor = None


def get_monitor(check_interval_seconds: int = 60) -> AlertMonitor:
    """Get or create the global alert monitor"""
    global _monitor
    if _monitor is None:
        _monitor = AlertMonitor(check_interval_seconds=check_interval_seconds)
    return _monitor


def start_alert_monitoring(check_interval_seconds: int = 60):
    """Start the alert monitoring service"""
    monitor = get_monitor(check_interval_seconds)
    monitor.start()


def stop_alert_monitoring():
    """Stop the alert monitoring service"""
    global _monitor
    if _monitor:
        _monitor.stop()
