"""
Alert storage and database models for the alert system
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import Session
import enum
import json

from backend.storage.database import Base, get_db_sync
from loguru import logger


class AlertType(enum.Enum):
    """Alert type enumeration"""
    ZSCORE_THRESHOLD = "zscore_threshold"
    CORRELATION_CHANGE = "correlation_change"
    PRICE_THRESHOLD = "price_threshold"
    VOLATILITY_SPIKE = "volatility_spike"


class AlertStatus(enum.Enum):
    """Alert status enumeration"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    DISABLED = "disabled"


class NotificationChannel(enum.Enum):
    """Notification channel enumeration"""
    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"


class AlertRule(Base):
    """Alert rule model"""
    __tablename__ = 'alert_rules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    symbol1 = Column(String(50), nullable=False)
    symbol2 = Column(String(50), nullable=True)  # For pair alerts
    timeframe = Column(String(10), default='1m')

    # Alert conditions
    threshold_upper = Column(Float, nullable=True)  # e.g., Z-score > 2.0
    threshold_lower = Column(Float, nullable=True)  # e.g., Z-score < -2.0

    # Notification settings
    notification_channels = Column(Text, nullable=False)  # JSON list of channels
    notification_config = Column(Text, nullable=True)  # JSON config (email, webhook URL, etc.)

    # Status and metadata
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_triggered_at = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)

    # Settings
    cooldown_minutes = Column(Integer, default=15)  # Min time between triggers
    enabled = Column(Boolean, default=True)


class AlertHistory(Base):
    """Alert history model - records of triggered alerts"""
    __tablename__ = 'alert_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, nullable=False)  # Foreign key to alert_rules

    # Alert details
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    symbol1 = Column(String(50), nullable=False)
    symbol2 = Column(String(50), nullable=True)

    # Trigger values
    trigger_value = Column(Float, nullable=True)  # The value that triggered (e.g., Z-score)
    threshold_breached = Column(Float, nullable=True)  # The threshold that was breached

    # Context data (JSON)
    context_data = Column(Text, nullable=True)  # Additional data (correlation, prices, etc.)

    # Notification status
    notifications_sent = Column(Text, nullable=True)  # JSON list of sent notifications
    notification_errors = Column(Text, nullable=True)  # JSON list of errors

    # Timestamps
    triggered_at = Column(DateTime, default=datetime.now)
    acknowledged_at = Column(DateTime, nullable=True)

    # Status
    acknowledged = Column(Boolean, default=False)


class AlertRuleRepository:
    """Repository for alert rule operations"""

    @staticmethod
    def create_rule(
        name: str,
        alert_type: AlertType,
        symbol1: str,
        notification_channels: List[str],
        symbol2: Optional[str] = None,
        timeframe: str = '1m',
        threshold_upper: Optional[float] = None,
        threshold_lower: Optional[float] = None,
        notification_config: Optional[Dict[str, Any]] = None,
        cooldown_minutes: int = 15,
        session: Optional[Session] = None
    ) -> AlertRule:
        """Create a new alert rule"""
        try:
            close_session = session is None
            if session is None:
                session = get_db_sync()

            rule = AlertRule(
                name=name,
                alert_type=alert_type,
                symbol1=symbol1,
                symbol2=symbol2,
                timeframe=timeframe,
                threshold_upper=threshold_upper,
                threshold_lower=threshold_lower,
                notification_channels=json.dumps(notification_channels),
                notification_config=json.dumps(notification_config) if notification_config else None,
                cooldown_minutes=cooldown_minutes,
                status=AlertStatus.ACTIVE,
                enabled=True
            )

            session.add(rule)
            session.commit()

            rule_id = rule.id

            if close_session:
                session.close()

            logger.info(f"Created alert rule: {name} (ID: {rule_id})")
            return rule

        except Exception as e:
            logger.error(f"Error creating alert rule: {e}")
            if session:
                session.rollback()
            raise

    @staticmethod
    def get_active_rules(session: Optional[Session] = None) -> List[Dict[str, Any]]:
        """Get all active alert rules"""
        try:
            close_session = session is None
            if session is None:
                session = get_db_sync()

            rules = session.query(AlertRule).filter(
                AlertRule.enabled == True,
                AlertRule.status == AlertStatus.ACTIVE
            ).all()

            # Convert to dictionaries
            rule_dicts = []
            for rule in rules:
                rule_dict = {
                    'id': rule.id,
                    'name': rule.name,
                    'alert_type': rule.alert_type.value,
                    'symbol1': rule.symbol1,
                    'symbol2': rule.symbol2,
                    'timeframe': rule.timeframe,
                    'threshold_upper': rule.threshold_upper,
                    'threshold_lower': rule.threshold_lower,
                    'notification_channels': json.loads(rule.notification_channels),
                    'notification_config': json.loads(rule.notification_config) if rule.notification_config else {},
                    'status': rule.status.value,
                    'cooldown_minutes': rule.cooldown_minutes,
                    'last_triggered_at': rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
                    'trigger_count': rule.trigger_count,
                    'created_at': rule.created_at.isoformat() if rule.created_at else None
                }
                rule_dicts.append(rule_dict)

            if close_session:
                session.close()

            return rule_dicts

        except Exception as e:
            logger.error(f"Error getting active rules: {e}")
            return []

    @staticmethod
    def update_rule_triggered(rule_id: int, session: Optional[Session] = None):
        """Update rule when triggered"""
        try:
            close_session = session is None
            if session is None:
                session = get_db_sync()

            rule = session.query(AlertRule).filter(AlertRule.id == rule_id).first()
            if rule:
                rule.last_triggered_at = datetime.now()
                rule.trigger_count += 1
                session.commit()

            if close_session:
                session.close()

        except Exception as e:
            logger.error(f"Error updating triggered rule: {e}")
            if session:
                session.rollback()


class AlertHistoryRepository:
    """Repository for alert history operations"""

    @staticmethod
    def create_history(
        rule_id: int,
        alert_type: AlertType,
        symbol1: str,
        trigger_value: float,
        threshold_breached: float,
        symbol2: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        notifications_sent: Optional[List[str]] = None,
        notification_errors: Optional[List[str]] = None,
        session: Optional[Session] = None
    ) -> AlertHistory:
        """Create alert history record"""
        try:
            close_session = session is None
            if session is None:
                session = get_db_sync()

            history = AlertHistory(
                rule_id=rule_id,
                alert_type=alert_type,
                symbol1=symbol1,
                symbol2=symbol2,
                trigger_value=trigger_value,
                threshold_breached=threshold_breached,
                context_data=json.dumps(context_data) if context_data else None,
                notifications_sent=json.dumps(notifications_sent) if notifications_sent else None,
                notification_errors=json.dumps(notification_errors) if notification_errors else None,
                triggered_at=datetime.now()
            )

            session.add(history)
            session.commit()

            history_id = history.id

            if close_session:
                session.close()

            logger.info(f"Created alert history record (ID: {history_id})")
            return history

        except Exception as e:
            logger.error(f"Error creating alert history: {e}")
            if session:
                session.rollback()
            raise

    @staticmethod
    def get_recent_history(limit: int = 100, session: Optional[Session] = None) -> List[Dict[str, Any]]:
        """Get recent alert history"""
        try:
            close_session = session is None
            if session is None:
                session = get_db_sync()

            history = session.query(AlertHistory).order_by(
                AlertHistory.triggered_at.desc()
            ).limit(limit).all()

            # Convert to dictionaries
            history_dicts = []
            for item in history:
                history_dict = {
                    'id': item.id,
                    'rule_id': item.rule_id,
                    'alert_type': item.alert_type.value,
                    'symbol1': item.symbol1,
                    'symbol2': item.symbol2,
                    'trigger_value': item.trigger_value,
                    'threshold_breached': item.threshold_breached,
                    'context_data': json.loads(item.context_data) if item.context_data else {},
                    'notifications_sent': json.loads(item.notifications_sent) if item.notifications_sent else [],
                    'notification_errors': json.loads(item.notification_errors) if item.notification_errors else [],
                    'triggered_at': item.triggered_at.isoformat() if item.triggered_at else None,
                    'acknowledged': item.acknowledged,
                    'acknowledged_at': item.acknowledged_at.isoformat() if item.acknowledged_at else None
                }
                history_dicts.append(history_dict)

            if close_session:
                session.close()

            return history_dicts

        except Exception as e:
            logger.error(f"Error getting alert history: {e}")
            return []


# Create tables on import
try:
    from backend.storage.database import engine
    Base.metadata.create_all(engine)
    logger.info("Alert tables created successfully")
except Exception as e:
    logger.warning(f"Could not create alert tables: {e}")
