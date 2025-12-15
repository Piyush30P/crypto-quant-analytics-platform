"""
Create an ultra-sensitive alert that will trigger with current Z-score
"""
import requests
import json

API_BASE_URL = "http://localhost:8000"

print("Creating ultra-sensitive alert that will trigger immediately...")
print()

# Get your webhook URL
webhook_url = input("Enter your webhook.site URL: ").strip()

# Create alert with very low thresholds (±0.4)
# This will trigger since current Z-score is 0.4873
alert_rule = {
    "name": "IMMEDIATE TEST - Z-Score ±0.4",
    "alert_type": "zscore_threshold",
    "symbol1": "BTCUSDT",
    "symbol2": "ETHUSDT",
    "timeframe": "1m",
    "threshold_upper": 0.4,  # Will trigger immediately!
    "threshold_lower": -0.4,
    "notification_channels": ["webhook"],
    "notification_config": {
        "webhook": {
            "url": webhook_url
        }
    },
    "cooldown_minutes": 1  # Short cooldown for testing
}

# Create the rule
response = requests.post(
    f"{API_BASE_URL}/api/alerts/rules",
    json=alert_rule,
    timeout=10
)

if response.status_code == 200:
    data = response.json()
    print(f"✅ Alert rule created (ID: {data['id']})")
    print(f"   Thresholds: ±0.4 (current Z-score: 0.4873)")
    print()

    # Trigger immediate check
    print("Triggering manual check...")
    check_response = requests.post(
        f"{API_BASE_URL}/api/alerts/monitor/check",
        timeout=15
    )

    if check_response.status_code == 200:
        result = check_response.json()
        print(f"✅ Check complete!")
        print(f"   Triggered: {result['triggered']}")

        if result['triggered'] > 0:
            print()
            print("🎉 ALERT TRIGGERED!")
            print(f"Check your webhook: {webhook_url}")
        else:
            print()
            print("⚠️  No trigger yet - wait 60s for background monitor")

    print()
    print("View alert history:")
    print(f"  curl http://localhost:8000/api/alerts/history")
else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text)
