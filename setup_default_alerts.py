"""
Setup default alert rules for the system
Run this after database schema reset to create pre-configured alerts
"""
import requests
import json

API_BASE_URL = "http://localhost:8000"

print("=" * 70)
print("Setting Up Default Alert Rules")
print("=" * 70)
print()

# Default webhook URL (change this to your actual webhook)
DEFAULT_WEBHOOK = "https://webhook.site/4ea88d84-2acf-4d7c-b5d5-1061ca70a1e0"

webhook_url = input(f"Enter webhook URL (or press Enter for default): ").strip()
if not webhook_url:
    webhook_url = DEFAULT_WEBHOOK
    print(f"Using default webhook: {DEFAULT_WEBHOOK}")

print()

# Alert Rule 1: Moderate Z-Score Alert (±1.5)
print("Creating Alert Rule 1: Moderate Z-Score Alert...")

rule1 = {
    "name": "BTC-ETH Moderate Z-Score Alert (±1.5)",
    "alert_type": "zscore_threshold",
    "symbol1": "BTCUSDT",
    "symbol2": "ETHUSDT",
    "timeframe": "1m",
    "threshold_upper": 1.5,
    "threshold_lower": -1.5,
    "notification_channels": ["webhook"],
    "notification_config": {
        "webhook": {
            "url": webhook_url
        }
    },
    "cooldown_minutes": 15,
    "enabled": True
}

try:
    response = requests.post(
        f"{API_BASE_URL}/api/alerts/rules",
        json=rule1,
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Created: {data['name']}")
        print(f"     ID: {data['id']}")
        print(f"     Thresholds: {data['threshold_lower']} to {data['threshold_upper']}")
        print(f"     Cooldown: {data['cooldown_minutes']} minutes")
    else:
        print(f"  ❌ Failed: {response.status_code} - {response.text}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print()

# Alert Rule 2: Sensitive Z-Score Alert (±0.8)
print("Creating Alert Rule 2: Sensitive Z-Score Alert...")

rule2 = {
    "name": "BTC-ETH Sensitive Z-Score Alert (±0.8)",
    "alert_type": "zscore_threshold",
    "symbol1": "BTCUSDT",
    "symbol2": "ETHUSDT",
    "timeframe": "1m",
    "threshold_upper": 0.8,
    "threshold_lower": -0.8,
    "notification_channels": ["webhook"],
    "notification_config": {
        "webhook": {
            "url": webhook_url
        }
    },
    "cooldown_minutes": 5,
    "enabled": True
}

try:
    response = requests.post(
        f"{API_BASE_URL}/api/alerts/rules",
        json=rule2,
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Created: {data['name']}")
        print(f"     ID: {data['id']}")
        print(f"     Thresholds: {data['threshold_lower']} to {data['threshold_upper']}")
        print(f"     Cooldown: {data['cooldown_minutes']} minutes")
    else:
        print(f"  ❌ Failed: {response.status_code} - {response.text}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print()

# Verify rules were created
print("Verifying created rules...")
try:
    response = requests.get(f"{API_BASE_URL}/api/alerts/rules", timeout=5)

    if response.status_code == 200:
        rules = response.json()
        print(f"  ✅ Total active rules: {len(rules)}")
        print()

        for rule in rules:
            print(f"  • {rule['name']}")
            print(f"    Pair: {rule['symbol1']} vs {rule['symbol2']}")
            print(f"    Thresholds: {rule['threshold_lower']} to {rule['threshold_upper']}")
            print(f"    Status: {rule['status']}")
            print()
    else:
        print(f"  ❌ Failed to verify: {response.status_code}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("=" * 70)
print("✅ Setup Complete!")
print("=" * 70)
print()
print("The alert monitor will check these rules every 60 seconds.")
print("Webhook notifications will be sent when thresholds are breached.")
print()
print("To view rules anytime:")
print("  python manage_alerts.py")
print()
print("To modify webhook URL, edit this script and re-run it.")
print()
