"""
API routes for alert management
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

from backend.alerts.alert_storage import (
    AlertType, AlertRuleRepository, AlertHistoryRepository
)
from backend.alerts.alert_manager import get_alert_manager
from backend.alerts.monitor import get_monitor
from loguru import logger


# Pydantic models
class CreateAlertRuleRequest(BaseModel):
    """Request model for creating an alert rule"""
    name: str = Field(..., description="Alert rule name")
    alert_type: str = Field("zscore_threshold", description="Type of alert")
    symbol1: str = Field(..., description="First symbol (e.g., BTCUSDT)")
    symbol2: Optional[str] = Field(None, description="Second symbol for pair alerts")
    timeframe: str = Field("1m", description="Timeframe")
    threshold_upper: Optional[float] = Field(None, description="Upper threshold (e.g., Z-score > 2.0)")
    threshold_lower: Optional[float] = Field(None, description="Lower threshold (e.g., Z-score < -2.0)")
    notification_channels: List[str] = Field(..., description="List of channels: email, telegram, webhook")
    notification_config: dict = Field(default_factory=dict, description="Notification configuration")
    cooldown_minutes: int = Field(15, ge=1, le=1440, description="Cooldown period in minutes")


class AlertRuleResponse(BaseModel):
    """Response model for alert rule"""
    id: int
    name: str
    alert_type: str
    symbol1: str
    symbol2: Optional[str]
    timeframe: str
    threshold_upper: Optional[float]
    threshold_lower: Optional[float]
    notification_channels: List[str]
    status: str
    cooldown_minutes: int
    last_triggered_at: Optional[str]
    trigger_count: int
    created_at: Optional[str]


class AlertHistoryResponse(BaseModel):
    """Response model for alert history"""
    id: int
    rule_id: int
    alert_type: str
    symbol1: str
    symbol2: Optional[str]
    trigger_value: Optional[float]
    threshold_breached: Optional[float]
    triggered_at: Optional[str]
    acknowledged: bool
    notifications_sent: List[str]
    notification_errors: List[str]


class AlertMonitorStatus(BaseModel):
    """Alert monitor status"""
    running: bool
    check_interval_seconds: int
    active_rules_count: int


class ManualCheckResponse(BaseModel):
    """Response for manual alert check"""
    total_rules: int
    triggered: int
    skipped: int
    errors: int
    timestamp: str


# Create router
router = APIRouter(prefix="/api/alerts", tags=["alerts"])

# Initialize repositories
rule_repo = AlertRuleRepository()
history_repo = AlertHistoryRepository()


@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(request: CreateAlertRuleRequest):
    """
    Create a new alert rule

    Creates a monitoring rule that will trigger notifications when conditions are met.
    """
    try:
        # Validate alert type
        try:
            alert_type = AlertType(request.alert_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid alert type: {request.alert_type}"
            )

        # Validate symbols
        if alert_type == AlertType.ZSCORE_THRESHOLD and not request.symbol2:
            raise HTTPException(
                status_code=400,
                detail="Z-score alerts require both symbol1 and symbol2"
            )

        # Validate thresholds
        if not request.threshold_upper and not request.threshold_lower:
            raise HTTPException(
                status_code=400,
                detail="At least one threshold (upper or lower) must be specified"
            )

        # Create rule
        rule = rule_repo.create_rule(
            name=request.name,
            alert_type=alert_type,
            symbol1=request.symbol1,
            symbol2=request.symbol2,
            timeframe=request.timeframe,
            threshold_upper=request.threshold_upper,
            threshold_lower=request.threshold_lower,
            notification_channels=request.notification_channels,
            notification_config=request.notification_config,
            cooldown_minutes=request.cooldown_minutes
        )

        # Convert to response
        return AlertRuleResponse(
            id=rule.id,
            name=rule.name,
            alert_type=rule.alert_type.value,
            symbol1=rule.symbol1,
            symbol2=rule.symbol2,
            timeframe=rule.timeframe,
            threshold_upper=rule.threshold_upper,
            threshold_lower=rule.threshold_lower,
            notification_channels=request.notification_channels,
            status=rule.status.value,
            cooldown_minutes=rule.cooldown_minutes,
            last_triggered_at=rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
            trigger_count=rule.trigger_count,
            created_at=rule.created_at.isoformat() if rule.created_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules", response_model=List[AlertRuleResponse])
async def get_alert_rules():
    """
    Get all active alert rules

    Returns a list of all configured alert rules.
    """
    try:
        rules = rule_repo.get_active_rules()

        return [
            AlertRuleResponse(
                id=rule['id'],
                name=rule['name'],
                alert_type=rule['alert_type'],
                symbol1=rule['symbol1'],
                symbol2=rule['symbol2'],
                timeframe=rule['timeframe'],
                threshold_upper=rule['threshold_upper'],
                threshold_lower=rule['threshold_lower'],
                notification_channels=rule['notification_channels'],
                status=rule['status'],
                cooldown_minutes=rule['cooldown_minutes'],
                last_triggered_at=rule['last_triggered_at'],
                trigger_count=rule['trigger_count'],
                created_at=rule['created_at']
            )
            for rule in rules
        ]

    except Exception as e:
        logger.error(f"Error getting alert rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[AlertHistoryResponse])
async def get_alert_history(limit: int = 50):
    """
    Get alert history

    Returns recent alert triggers with notification status.
    """
    try:
        history = history_repo.get_recent_history(limit=limit)

        return [
            AlertHistoryResponse(
                id=item['id'],
                rule_id=item['rule_id'],
                alert_type=item['alert_type'],
                symbol1=item['symbol1'],
                symbol2=item['symbol2'],
                trigger_value=item['trigger_value'],
                threshold_breached=item['threshold_breached'],
                triggered_at=item['triggered_at'],
                acknowledged=item['acknowledged'],
                notifications_sent=item['notifications_sent'],
                notification_errors=item['notification_errors']
            )
            for item in history
        ]

    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/status", response_model=AlertMonitorStatus)
async def get_monitor_status():
    """
    Get alert monitor status

    Returns the current status of the background monitoring service.
    """
    try:
        monitor = get_monitor()
        rules = rule_repo.get_active_rules()

        return AlertMonitorStatus(
            running=monitor.running,
            check_interval_seconds=monitor.check_interval,
            active_rules_count=len(rules)
        )

    except Exception as e:
        logger.error(f"Error getting monitor status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/check", response_model=ManualCheckResponse)
async def manual_check():
    """
    Manually trigger alert check

    Forces an immediate check of all alert rules, bypassing the normal schedule.
    """
    try:
        monitor = get_monitor()
        summary = monitor.check_now()

        return ManualCheckResponse(
            total_rules=summary['total_rules'],
            triggered=summary['triggered'],
            skipped=summary['skipped'],
            errors=summary['errors'],
            timestamp=summary['timestamp']
        )

    except Exception as e:
        logger.error(f"Error performing manual check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/start")
async def start_monitor():
    """
    Start the alert monitoring service

    Begins background monitoring of all active alert rules.
    """
    try:
        monitor = get_monitor()
        monitor.start()

        return {
            "status": "started",
            "message": "Alert monitoring service started",
            "check_interval_seconds": monitor.check_interval
        }

    except Exception as e:
        logger.error(f"Error starting monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/stop")
async def stop_monitor():
    """
    Stop the alert monitoring service

    Stops background monitoring of alert rules.
    """
    try:
        monitor = get_monitor()
        monitor.stop()

        return {
            "status": "stopped",
            "message": "Alert monitoring service stopped"
        }

    except Exception as e:
        logger.error(f"Error stopping monitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))
