"""
Simple script to test alert system with webhook
Run: python test_alert_simple.py
"""
import requests
import json

API_BASE_URL = "http://localhost:8000"

print("=" * 70)
print("Testing Alert System with Webhook")
print("=" * 70)
print()

# Step 1: Get webhook URL
print("Step 1: Get a Webhook URL")
print("  1. Open https://webhook.site in your browser")
print("  2. Copy your unique webhook URL")
print("  3. Paste it below")
print()

webhook_url = input("Enter your webhook.site URL (or press Enter to skip): ").strip()

if not webhook_url:
    webhook_url = "https://webhook.site/test-placeholder"
    print("  Using placeholder URL (notifications won't be sent)")

print()

# Step 2: Create alert rule
print("Step 2: Creating Alert Rule")

alert_rule = {
    "name": "BTC-ETH Z-Score Alert (Sensitive)",
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
    "cooldown_minutes": 5
}

try:
    response = requests.post(
        f"{API_BASE_URL}/api/alerts/rules",
        json=alert_rule,
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        print("  ✅ Alert rule created successfully!")
        print(f"    - ID: {data['id']}")
        print(f"    - Name: {data['name']}")
        print(f"    - Type: {data['alert_type']}")
        print(f"    - Pair: {data['symbol1']} vs {data['symbol2']}")
        print(f"    - Thresholds: {data['threshold_lower']} < Z-score < {data['threshold_upper']}")
        print(f"    - Status: {data['status']}")
        rule_id = data['id']
    else:
        print(f"  ❌ Failed to create alert rule: {response.status_code}")
        print(f"  Response: {response.text}")
        exit(1)
except Exception as e:
    print(f"  ❌ Error: {e}")
    exit(1)

print()

# Step 3: Trigger manual check
print("Step 3: Triggering Manual Alert Check")

try:
    response = requests.post(
        f"{API_BASE_URL}/api/alerts/monitor/check",
        timeout=15
    )

    if response.status_code == 200:
        data = response.json()
        print("  ✅ Manual check completed!")
        print(f"    - Total rules: {data['total_rules']}")
        print(f"    - Triggered: {data['triggered']}")
        print(f"    - Skipped: {data['skipped']}")
        print(f"    - Errors: {data['errors']}")
        print(f"    - Timestamp: {data['timestamp']}")

        if data['triggered'] > 0:
            print()
            print(f"  🎉 {data['triggered']} alert(s) were triggered!")
            print("  Check your webhook.site URL to see the notification!")
        else:
            print()
            print("  ℹ️  No alerts triggered yet (Z-score hasn't crossed ±1.5)")
            print("  The background monitor will check every 60 seconds")
    else:
        print(f"  ❌ Failed to trigger manual check: {response.status_code}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print()

# Step 4: View all active rules
print("Step 4: Viewing All Active Rules")

try:
    response = requests.get(f"{API_BASE_URL}/api/alerts/rules", timeout=5)

    if response.status_code == 200:
        rules = response.json()
        print(f"  ✅ Retrieved {len(rules)} alert rule(s)")
        for rule in rules:
            print(f"    - {rule['name']} (ID: {rule['id']}, Status: {rule['status']})")
    else:
        print(f"  ❌ Failed to get rules: {response.status_code}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print()

# Step 5: View alert history
print("Step 5: Viewing Alert History")

try:
    response = requests.get(f"{API_BASE_URL}/api/alerts/history?limit=10", timeout=5)

    if response.status_code == 200:
        history = response.json()
        print(f"  ✅ Retrieved {len(history)} alert history item(s)")

        if history:
            print("\n  Recent alerts:")
            for item in history[:5]:
                print(f"    - [{item['alert_type']}] {item['symbol1']} vs {item['symbol2']}")
                print(f"      Triggered: {item['triggered_at']}")
                print(f"      Z-Score: {item['trigger_value']:.4f} (threshold: {item['threshold_breached']:.2f})")
                if item['notifications_sent']:
                    print(f"      Notifications: {', '.join(item['notifications_sent'])}")
                if item['notification_errors']:
                    print(f"      Errors: {', '.join(item['notification_errors'])}")
                print()
        else:
            print("    No alerts triggered yet - monitor is checking every 60s")
    else:
        print(f"  ❌ Failed to get alert history: {response.status_code}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print()
print("=" * 70)
print("✅ Alert System Test Complete!")
print("=" * 70)
print()
print("💡 What's happening now:")
print("  • Background monitor checks all rules every 60 seconds")
print("  • When BTCUSDT/ETHUSDT Z-score crosses ±1.5, alert triggers")
print("  • Notification will be sent to your webhook URL")
print("  • 5-minute cooldown prevents spam")
print()
print("📊 Monitor the dashboard:")
print("  streamlit run frontend/dashboard.py")
print()
print("🔍 View API docs:")
print("  http://localhost:8000/docs")
print()
