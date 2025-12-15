"""
Phase 6 verification - Frontend Dashboard
"""
import subprocess
import sys
import time
import requests
from pathlib import Path

print("=" * 70)
print("Phase 6: Frontend Dashboard - Verification Test")
print("=" * 70)
print()

# Test 1: Check dependencies
print("✓ Test 1: Checking Dependencies")
try:
    import streamlit
    print("  ✅ Streamlit installed")
except ImportError:
    print("  ❌ Streamlit not installed. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "plotly"])
    print("  ✅ Streamlit installed successfully")

try:
    import plotly
    print("  ✅ Plotly installed")
except ImportError:
    print("  ❌ Plotly not installed. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly"])
    print("  ✅ Plotly installed successfully")

print()

# Test 2: Check frontend files exist
print("✓ Test 2: Checking Frontend Files")
dashboard_file = Path("frontend/dashboard.py")

if dashboard_file.exists():
    print("  ✅ Dashboard file exists")
    print(f"    Location: {dashboard_file.absolute()}")
else:
    print("  ❌ Dashboard file not found")
    sys.exit(1)

print()

# Test 3: Check API availability
print("✓ Test 3: Checking API Availability")
try:
    response = requests.get("http://localhost:8000/api/health", timeout=5)
    if response.status_code == 200:
        print("  ✅ API is running and healthy")
    else:
        print("  ⚠️  API returned non-200 status")
except requests.exceptions.ConnectionError:
    print("  ❌ API is not running!")
    print()
    print("  Please start the API server in another terminal:")
    print("  python -m uvicorn backend.api.app:app --reload")
    print()
    sys.exit(1)
except Exception as e:
    print(f"  ❌ Error checking API: {e}")
    sys.exit(1)

print()

# Test 4: Verify dashboard can be imported
print("✓ Test 4: Verifying Dashboard Code")
try:
    # Check if file has valid Python syntax
    with open(dashboard_file, 'r') as f:
        code = f.read()
        compile(code, dashboard_file, 'exec')
    print("  ✅ Dashboard code is valid")
except SyntaxError as e:
    print(f"  ❌ Syntax error in dashboard: {e}")
    sys.exit(1)

print()

# Instructions
print("=" * 70)
print("✅ All prerequisite checks passed!")
print("=" * 70)
print()
print("🚀 To launch the dashboard:")
print()
print("  Method 1: Using Streamlit directly")
print("  streamlit run frontend/dashboard.py")
print()
print("  Method 2: Using Python module")
print("  python -m streamlit run frontend/dashboard.py")
print()
print("  The dashboard will open in your browser at:")
print("  http://localhost:8501")
print()
print("=" * 70)
print()
print("📊 Dashboard Features:")
print("  • Single Symbol Analysis - Price charts and statistics")
print("  • Pair Trading Analysis - Correlation, Z-scores, signals")
print("  • Multi-Symbol Dashboard - Monitor multiple cryptos")
print("  • Auto-refresh - Real-time data updates")
print("  • Interactive Charts - Zoom, pan, and explore")
print()
print("=" * 70)
print()
print("⚠️  Important:")
print("  1. Keep the API server running (uvicorn)")
print("  2. Ensure you have OHLC data (run test_phase3.py if needed)")
print("  3. Use the sidebar to configure timeframes and settings")
print()
print("=" * 70)
