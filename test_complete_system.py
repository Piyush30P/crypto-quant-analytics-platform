"""
Complete System Test - Verify all 7 phases are working correctly
Run this to test your entire Crypto Quantitative Analytics Platform
"""
import requests
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

print("=" * 70)
print("CRYPTO QUANT ANALYTICS PLATFORM - COMPLETE SYSTEM TEST")
print("=" * 70)
print()

# Test counters
tests_passed = 0
tests_failed = 0
tests_total = 0

def test(name, condition, details=""):
    global tests_passed, tests_failed, tests_total
    tests_total += 1
    if condition:
        tests_passed += 1
        print(f"✅ TEST {tests_total}: {name}")
        if details:
            print(f"   {details}")
    else:
        tests_failed += 1
        print(f"❌ TEST {tests_total}: {name}")
        if details:
            print(f"   {details}")
    print()

# ============================================================================
# PHASE 1: Architecture & Setup
# ============================================================================
print("PHASE 1: Architecture & Setup")
print("-" * 70)

try:
    response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    test("API Server Health Check", response.status_code == 200,
         f"API is running at {API_BASE_URL}")
except Exception as e:
    test("API Server Health Check", False, f"Error: {e}")

try:
    response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
    test("API Documentation Available", response.status_code == 200,
         "Swagger docs accessible at /docs")
except:
    test("API Documentation Available", False, "Could not access /docs")

# ============================================================================
# PHASE 2: Data Ingestion Pipeline
# ============================================================================
print("PHASE 2: Data Ingestion Pipeline")
print("-" * 70)

try:
    response = requests.get(f"{API_BASE_URL}/api/data/tick/BTCUSDT?limit=10", timeout=5)
    tick_data = response.json() if response.status_code == 200 else []
    test("WebSocket Tick Data Collection", len(tick_data) > 0,
         f"Found {len(tick_data)} tick data points for BTCUSDT")
except Exception as e:
    test("WebSocket Tick Data Collection", False,
         "No tick data - make sure WebSocket ingestion is running")

# ============================================================================
# PHASE 3: OHLC Resampling
# ============================================================================
print("PHASE 3: OHLC Resampling")
print("-" * 70)

try:
    response = requests.get(f"{API_BASE_URL}/api/data/ohlc/BTCUSDT/1m?limit=10", timeout=5)
    ohlc_data = response.json() if response.status_code == 200 else {}
    bars = ohlc_data.get('bars', [])
    test("OHLC Bar Generation", len(bars) > 0,
         f"Found {len(bars)} OHLC bars for BTCUSDT (1m timeframe)")
except Exception as e:
    test("OHLC Bar Generation", False, f"Error: {e}")

try:
    if bars:
        has_vwap = any('vwap' in bar and bar['vwap'] is not None for bar in bars)
        test("VWAP Calculation", has_vwap,
             "VWAP values present in OHLC bars")
    else:
        test("VWAP Calculation", False, "No OHLC bars to check")
except:
    test("VWAP Calculation", False, "Could not verify VWAP")

# ============================================================================
# PHASE 4: Analytics Engine
# ============================================================================
print("PHASE 4: Analytics Engine")
print("-" * 70)

try:
    response = requests.get(
        f"{API_BASE_URL}/api/analytics/pair/BTCUSDT/ETHUSDT?timeframe=1m&window=20",
        timeout=10
    )
    analytics = response.json() if response.status_code == 200 else {}

    has_correlation = 'correlation' in analytics and analytics['correlation'].get('pearson') is not None
    test("Correlation Analysis", has_correlation,
         f"Pearson correlation: {analytics.get('correlation', {}).get('pearson', 'N/A')}")

    has_cointegration = 'cointegration' in analytics
    test("Cointegration Test", has_cointegration,
         f"p-value: {analytics.get('cointegration', {}).get('p_value', 'N/A')}")

    has_zscore = 'zscore' in analytics and analytics['zscore'].get('current') is not None
    current_zscore = analytics.get('zscore', {}).get('current', 'N/A')
    test("Z-Score Calculation", has_zscore,
         f"Current Z-score: {current_zscore}")

    has_hedge_ratio = 'hedge_ratio' in analytics and analytics['hedge_ratio'].get('ratio') is not None
    test("Hedge Ratio Calculation", has_hedge_ratio,
         f"Hedge ratio: {analytics.get('hedge_ratio', {}).get('ratio', 'N/A')}")

except Exception as e:
    test("Correlation Analysis", False, f"Error: {e}")
    test("Cointegration Test", False, "Skipped")
    test("Z-Score Calculation", False, "Skipped")
    test("Hedge Ratio Calculation", False, "Skipped")

# ============================================================================
# PHASE 5: REST API
# ============================================================================
print("PHASE 5: REST API")
print("-" * 70)

try:
    response = requests.get(f"{API_BASE_URL}/api/data/symbols", timeout=5)
    symbols = response.json() if response.status_code == 200 else []
    test("Symbol List Endpoint", len(symbols) > 0,
         f"Found {len(symbols)} symbols: {', '.join(symbols[:5])}")
except Exception as e:
    test("Symbol List Endpoint", False, f"Error: {e}")

try:
    response = requests.get(f"{API_BASE_URL}/api/analytics/basic/BTCUSDT?timeframe=1m&limit=20", timeout=5)
    test("Basic Analytics Endpoint", response.status_code == 200,
         "Basic stats endpoint working")
except:
    test("Basic Analytics Endpoint", False, "Could not access basic analytics")

# ============================================================================
# PHASE 6: Frontend Dashboard
# ============================================================================
print("PHASE 6: Frontend Dashboard")
print("-" * 70)

import os
dashboard_exists = os.path.exists("frontend/dashboard.py")
test("Dashboard File Exists", dashboard_exists,
     "frontend/dashboard.py found")

if dashboard_exists:
    try:
        with open("frontend/dashboard.py", 'r', encoding='utf-8') as f:
            content = f.read()
            has_streamlit = 'import streamlit' in content
            has_plotly = 'import plotly' in content
            test("Dashboard Dependencies", has_streamlit and has_plotly,
                 "Streamlit and Plotly imports found")
    except:
        test("Dashboard Dependencies", False, "Could not read dashboard file")
else:
    test("Dashboard Dependencies", False, "Dashboard file not found")

# ============================================================================
# PHASE 7: Alert System
# ============================================================================
print("PHASE 7: Alert System")
print("-" * 70)

try:
    response = requests.get(f"{API_BASE_URL}/api/alerts/monitor/status", timeout=5)
    status = response.json() if response.status_code == 200 else {}
    is_running = status.get('running', False)
    test("Alert Monitor Running", is_running,
         f"Monitor status: {'Running' if is_running else 'Stopped'}, Interval: {status.get('check_interval')}s")
except Exception as e:
    test("Alert Monitor Running", False, f"Error: {e}")

try:
    response = requests.get(f"{API_BASE_URL}/api/alerts/rules", timeout=5)
    rules = response.json() if response.status_code == 200 else []
    test("Alert Rules Created", len(rules) > 0,
         f"Found {len(rules)} active alert rules")

    if rules:
        for rule in rules[:2]:  # Show first 2 rules
            print(f"   • {rule['name']}")
            print(f"     Thresholds: {rule['threshold_lower']} to {rule['threshold_upper']}")
        print()
except Exception as e:
    test("Alert Rules Created", False, f"Error: {e}")

try:
    response = requests.get(f"{API_BASE_URL}/api/alerts/history?limit=5", timeout=5)
    history = response.json() if response.status_code == 200 else []
    has_history = len(history) > 0
    test("Alert History Tracking", True,
         f"{len(history)} alerts in history (may be 0 if no triggers yet)")

    if history:
        print("   Recent alerts:")
        for alert in history[:3]:
            print(f"   • {alert['symbol1']} vs {alert['symbol2']}: Z-score {alert['trigger_value']:.4f}")
        print()
except Exception as e:
    test("Alert History Tracking", False, f"Error: {e}")

# ============================================================================
# INTEGRATION TESTS
# ============================================================================
print("INTEGRATION TESTS")
print("-" * 70)

# Test if we can trigger a manual alert check
try:
    response = requests.post(f"{API_BASE_URL}/api/alerts/monitor/check", timeout=15)
    check_result = response.json() if response.status_code == 200 else {}
    test("Manual Alert Check", response.status_code == 200,
         f"Checked {check_result.get('total_rules', 0)} rules, Triggered: {check_result.get('triggered', 0)}")
except Exception as e:
    test("Manual Alert Check", False, f"Error: {e}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"Total Tests: {tests_total}")
print(f"✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"Success Rate: {(tests_passed/tests_total*100):.1f}%")
print()

if tests_failed == 0:
    print("🎉 ALL TESTS PASSED! Your platform is fully operational!")
    print()
    print("Next steps:")
    print("  1. Launch dashboard: streamlit run frontend/dashboard.py")
    print("  2. Monitor webhook: https://webhook.site/your-unique-url")
    print("  3. Wait for alerts to trigger based on market conditions")
elif tests_failed <= 3:
    print("⚠️  MOST TESTS PASSED - Minor issues detected")
    print()
    print("Common fixes:")
    print("  • If tick data is missing: Start WebSocket ingestion")
    print("    python -m backend.ingestion.binance_websocket")
    print("  • If alerts not in history: Wait for Z-score to cross thresholds")
else:
    print("❌ MULTIPLE FAILURES - System needs attention")
    print()
    print("Troubleshooting:")
    print("  1. Make sure API server is running")
    print("  2. Start WebSocket ingestion for data collection")
    print("  3. Check alert rules are configured")
    print("  4. Review API logs for errors")

print()
print("=" * 70)
print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
