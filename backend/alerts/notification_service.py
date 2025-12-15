"""
Notification service for sending alerts via email, Telegram, and webhooks
"""
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from config.settings import settings


class NotificationService:
    """Service for sending notifications through various channels"""

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body: str,
        smtp_config: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Send email notification

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (HTML supported)
            smtp_config: SMTP configuration (server, port, username, password)

        Returns:
            (success: bool, error_message: Optional[str])
        """
        try:
            # Use provided config or default from settings
            if smtp_config is None:
                smtp_config = {
                    'server': getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com'),
                    'port': getattr(settings, 'SMTP_PORT', 587),
                    'username': getattr(settings, 'SMTP_USERNAME', ''),
                    'password': getattr(settings, 'SMTP_PASSWORD', ''),
                    'from_email': getattr(settings, 'SMTP_FROM_EMAIL', '')
                }

            # Skip if no SMTP config
            if not smtp_config.get('username') or not smtp_config.get('password'):
                logger.warning("Email notification skipped: No SMTP credentials configured")
                return False, "No SMTP credentials configured"

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_config.get('from_email', smtp_config.get('username'))
            msg['To'] = to_email

            # Add body
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)

            # Connect and send
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True, None

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    @staticmethod
    def send_telegram(
        message: str,
        telegram_config: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Send Telegram notification

        Args:
            message: Message to send
            telegram_config: Telegram configuration (bot_token, chat_id)

        Returns:
            (success: bool, error_message: Optional[str])
        """
        try:
            # Use provided config or default from settings
            if telegram_config is None:
                telegram_config = {
                    'bot_token': getattr(settings, 'TELEGRAM_BOT_TOKEN', ''),
                    'chat_id': getattr(settings, 'TELEGRAM_CHAT_ID', '')
                }

            # Skip if no Telegram config
            if not telegram_config.get('bot_token') or not telegram_config.get('chat_id'):
                logger.warning("Telegram notification skipped: No bot token or chat ID configured")
                return False, "No Telegram configuration"

            # Send message via Telegram API
            url = f"https://api.telegram.org/bot{telegram_config['bot_token']}/sendMessage"
            payload = {
                'chat_id': telegram_config['chat_id'],
                'text': message,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info(f"Telegram message sent successfully")
                return True, None
            else:
                error_msg = f"Telegram API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"Failed to send Telegram message: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    @staticmethod
    def send_webhook(
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Send webhook notification

        Args:
            url: Webhook URL
            payload: JSON payload to send
            headers: Optional HTTP headers

        Returns:
            (success: bool, error_message: Optional[str])
        """
        try:
            if not url:
                return False, "No webhook URL provided"

            default_headers = {'Content-Type': 'application/json'}
            if headers:
                default_headers.update(headers)

            response = requests.post(
                url,
                json=payload,
                headers=default_headers,
                timeout=10
            )

            if 200 <= response.status_code < 300:
                logger.info(f"Webhook sent successfully to {url}")
                return True, None
            else:
                error_msg = f"Webhook error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"Failed to send webhook: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    @staticmethod
    def format_zscore_alert_email(
        symbol1: str,
        symbol2: str,
        zscore: float,
        threshold: float,
        signal: str,
        correlation: Optional[float] = None,
        hedge_ratio: Optional[float] = None
    ) -> str:
        """Format HTML email for Z-score alert"""
        signal_emoji = "🟢" if "long" in signal.lower() else "🔴" if "short" in signal.lower() else "🟡"
        signal_color = "#28a745" if "long" in signal.lower() else "#dc3545" if "short" in signal.lower() else "#ffc107"

        html = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; }}
              .header {{ background-color: {signal_color}; color: white; padding: 20px; text-align: center; }}
              .content {{ padding: 20px; }}
              .metric {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid {signal_color}; }}
              .footer {{ padding: 20px; text-align: center; color: #6c757d; font-size: 12px; }}
            </style>
          </head>
          <body>
            <div class="header">
              <h1>{signal_emoji} CRYPTO ALERT: {signal.upper()}</h1>
            </div>
            <div class="content">
              <h2>Pair: {symbol1} vs {symbol2}</h2>

              <div class="metric">
                <strong>Z-Score:</strong> {zscore:.4f}
              </div>

              <div class="metric">
                <strong>Threshold Breached:</strong> {threshold:.2f}
              </div>

              <div class="metric">
                <strong>Signal:</strong> {signal}
              </div>

              {f'<div class="metric"><strong>Correlation:</strong> {correlation:.4f}</div>' if correlation else ''}

              {f'<div class="metric"><strong>Hedge Ratio:</strong> {hedge_ratio:.6f}</div>' if hedge_ratio else ''}

              <div class="metric">
                <strong>Triggered At:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
              </div>

              <h3>Recommended Action:</h3>
              <p>
                {'Consider going LONG the spread (buy spread)' if 'long' in signal.lower() else
                 'Consider going SHORT the spread (sell spread)' if 'short' in signal.lower() else
                 'No strong signal - wait for better opportunity'}
              </p>
            </div>
            <div class="footer">
              <p>Crypto Analytics Platform - Automated Alert System</p>
              <p>This is an automated message. Do not reply.</p>
            </div>
          </body>
        </html>
        """
        return html

    @staticmethod
    def format_zscore_alert_telegram(
        symbol1: str,
        symbol2: str,
        zscore: float,
        threshold: float,
        signal: str,
        correlation: Optional[float] = None
    ) -> str:
        """Format Telegram message for Z-score alert"""
        signal_emoji = "🟢" if "long" in signal.lower() else "🔴" if "short" in signal.lower() else "🟡"

        message = f"""
{signal_emoji} <b>CRYPTO ALERT</b>

<b>Pair:</b> {symbol1} vs {symbol2}
<b>Z-Score:</b> {zscore:.4f}
<b>Threshold:</b> {threshold:.2f}
<b>Signal:</b> {signal}
{f'<b>Correlation:</b> {correlation:.4f}' if correlation else ''}

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'📈 Consider LONG the spread' if 'long' in signal.lower() else
 '📉 Consider SHORT the spread' if 'short' in signal.lower() else
 '⏸ No strong signal'}
        """
        return message.strip()

    @staticmethod
    def format_zscore_alert_webhook(
        symbol1: str,
        symbol2: str,
        zscore: float,
        threshold: float,
        signal: str,
        correlation: Optional[float] = None,
        hedge_ratio: Optional[float] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format webhook payload for Z-score alert"""
        return {
            'alert_type': 'zscore_threshold',
            'pair': {
                'symbol1': symbol1,
                'symbol2': symbol2
            },
            'metrics': {
                'zscore': zscore,
                'threshold': threshold,
                'correlation': correlation,
                'hedge_ratio': hedge_ratio
            },
            'signal': signal,
            'timestamp': datetime.now().isoformat(),
            'context': context_data or {}
        }


def send_alert_notifications(
    alert_data: Dict[str, Any],
    notification_channels: List[str],
    notification_config: Dict[str, Any]
) -> tuple[List[str], List[str]]:
    """
    Send notifications through configured channels

    Args:
        alert_data: Alert information
        notification_channels: List of channels to use (email, telegram, webhook)
        notification_config: Configuration for each channel

    Returns:
        (notifications_sent: List[str], errors: List[str])
    """
    sent = []
    errors = []

    service = NotificationService()

    # Extract alert data
    symbol1 = alert_data.get('symbol1', '')
    symbol2 = alert_data.get('symbol2', '')
    zscore = alert_data.get('zscore', 0.0)
    threshold = alert_data.get('threshold', 0.0)
    signal = alert_data.get('signal', 'neutral')
    correlation = alert_data.get('correlation')
    hedge_ratio = alert_data.get('hedge_ratio')
    context_data = alert_data.get('context_data', {})

    # Email notification
    if 'email' in notification_channels:
        email_config = notification_config.get('email', {})
        to_email = email_config.get('to_email', '')

        if to_email:
            subject = f"Crypto Alert: {signal.upper()} - {symbol1}/{symbol2}"
            body = service.format_zscore_alert_email(
                symbol1, symbol2, zscore, threshold, signal, correlation, hedge_ratio
            )

            success, error = service.send_email(to_email, subject, body, email_config.get('smtp'))

            if success:
                sent.append('email')
            else:
                errors.append(f"email: {error}")

    # Telegram notification
    if 'telegram' in notification_channels:
        telegram_config = notification_config.get('telegram', {})
        message = service.format_zscore_alert_telegram(
            symbol1, symbol2, zscore, threshold, signal, correlation
        )

        success, error = service.send_telegram(message, telegram_config)

        if success:
            sent.append('telegram')
        else:
            errors.append(f"telegram: {error}")

    # Webhook notification
    if 'webhook' in notification_channels:
        webhook_config = notification_config.get('webhook', {})
        webhook_url = webhook_config.get('url', '')

        if webhook_url:
            payload = service.format_zscore_alert_webhook(
                symbol1, symbol2, zscore, threshold, signal,
                correlation, hedge_ratio, context_data
            )

            success, error = service.send_webhook(
                webhook_url,
                payload,
                webhook_config.get('headers')
            )

            if success:
                sent.append('webhook')
            else:
                errors.append(f"webhook: {error}")

    return sent, errors
