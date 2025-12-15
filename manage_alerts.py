"""
Manage alert rules - view and delete
"""
import requests
import json

API_BASE_URL = "http://localhost:8000"

print("=" * 70)
print("Alert Rule Management")
print("=" * 70)
print()

# Get all rules
print("Current Alert Rules:")
print("-" * 70)

response = requests.get(f"{API_BASE_URL}/api/alerts/rules")
if response.status_code == 200:
    rules = response.json()

    for rule in rules:
        print(f"ID: {rule['id']}")
        print(f"  Name: {rule['name']}")
        print(f"  Type: {rule['alert_type']}")
        print(f"  Pair: {rule['symbol1']} vs {rule['symbol2']}")
        print(f"  Thresholds: {rule['threshold_lower']} to {rule['threshold_upper']}")
        print(f"  Status: {rule['status']}")
        print(f"  Triggers: {rule['trigger_count']}")
        if rule['last_triggered_at']:
            print(f"  Last triggered: {rule['last_triggered_at']}")
        print()

    print(f"Total rules: {len(rules)}")
    print()

    # Ask if user wants to delete any
    delete = input("Do you want to delete any rules? (y/n): ").strip().lower()

    if delete == 'y':
        rule_id = input("Enter rule ID to delete (or 'all' to delete all): ").strip()

        if rule_id == 'all':
            confirm = input(f"Delete ALL {len(rules)} rules? (yes/no): ").strip().lower()
            if confirm == 'yes':
                for rule in rules:
                    # Note: Delete endpoint needs to be implemented in API
                    print(f"To delete rule {rule['id']}, you can disable it via the database")
                    # In production, you'd implement: DELETE /api/alerts/rules/{id}
                print()
                print("⚠️  Delete endpoint not yet implemented")
                print("   Rules can be disabled by setting enabled=False in database")
        else:
            print()
            print("⚠️  Delete endpoint not yet implemented")
            print("   You can disable rules via the database or API docs")

    print()
    print("📊 View alert history:")
    history_response = requests.get(f"{API_BASE_URL}/api/alerts/history?limit=5")
    if history_response.status_code == 200:
        history = history_response.json()
        if history:
            print(f"\nRecent {len(history)} alerts:")
            for item in history:
                print(f"  - {item['symbol1']} vs {item['symbol2']}")
                print(f"    Z-score: {item['trigger_value']:.4f} crossed {item['threshold_breached']}")
                print(f"    Time: {item['triggered_at']}")
                print()
        else:
            print("\n  No alerts triggered yet")
else:
    print(f"❌ Failed to get rules: {response.status_code}")

print()
print("=" * 70)
print("API Docs: http://localhost:8000/docs")
print("=" * 70)
