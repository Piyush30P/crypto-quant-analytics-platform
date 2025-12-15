"""
Diagnostic script to debug why alerts aren't triggering
"""
import pandas as pd
from backend.storage.ohlc_repository import OHLCRepository
from backend.analytics.pairs_analytics import PairsAnalyzer
from loguru import logger

print("=" * 70)
print("Alert System Diagnostics")
print("=" * 70)
print()

# Test parameters
symbol1 = "BTCUSDT"
symbol2 = "ETHUSDT"
timeframe = "1m"
threshold_upper = 0.4

print(f"Testing: {symbol1} vs {symbol2} (timeframe: {timeframe})")
print(f"Threshold: ±{threshold_upper}")
print()

# Step 1: Check OHLC data availability
print("Step 1: Checking OHLC Data Availability")
print("-" * 70)

ohlc_repo = OHLCRepository()

bars1 = ohlc_repo.get_recent_ohlc(symbol1, timeframe, limit=100)
bars2 = ohlc_repo.get_recent_ohlc(symbol2, timeframe, limit=100)

print(f"  {symbol1}: {len(bars1) if bars1 else 0} bars")
print(f"  {symbol2}: {len(bars2) if bars2 else 0} bars")

if not bars1 or not bars2:
    print()
    print("❌ PROBLEM FOUND: No OHLC data available!")
    print()
    print("This is why alerts aren't triggering. Solutions:")
    print()
    print("1. Make sure data ingestion is running:")
    print("   python -m backend.ingestion.binance_websocket")
    print()
    print("2. Wait 2-5 minutes for OHLC data to accumulate")
    print()
    print("3. Check if database has data:")
    print("   python -c \"from backend.storage.ohlc_repository import OHLCRepository; r=OHLCRepository(); print(r.get_available_symbols())\"")
    print()
    exit(1)

print()

# Step 2: Check data alignment
print("Step 2: Checking Data Alignment")
print("-" * 70)

df1 = pd.DataFrame(bars1)[['timestamp', 'close']].rename(columns={'close': 'close_x'})
df2 = pd.DataFrame(bars2)[['timestamp', 'close']].rename(columns={'close': 'close_y'})
merged = pd.merge(df1, df2, on='timestamp', how='inner')

print(f"  Aligned data points: {len(merged)}")

if len(merged) < 20:
    print()
    print(f"❌ PROBLEM FOUND: Only {len(merged)} aligned data points (need 20+)")
    print()
    print("Wait for more data to accumulate (2-5 minutes)")
    print()
    exit(1)

print()

# Step 3: Calculate analytics
print("Step 3: Calculating Pair Analytics")
print("-" * 70)

analyzer = PairsAnalyzer()
rolling_window = min(20, len(merged) // 2)

analysis = analyzer.safe_calculate(
    merged,
    rolling_window=rolling_window,
    symbol1_name=symbol1,
    symbol2_name=symbol2
)

if 'error' in analysis:
    print(f"❌ PROBLEM FOUND: Analysis error: {analysis['error']}")
    print()
    exit(1)

print(f"  ✓ Analysis successful")
print()

# Step 4: Check Z-score
print("Step 4: Checking Z-Score")
print("-" * 70)

zscore_data = analysis.get('zscore', {})

if 'error' in zscore_data:
    print(f"❌ PROBLEM FOUND: Z-score error: {zscore_data['error']}")
    print()
    exit(1)

zscore = zscore_data.get('current')

if zscore is None:
    print("❌ PROBLEM FOUND: Z-score is None")
    print()
    exit(1)

print(f"  Current Z-Score: {zscore:.4f}")
print(f"  Threshold Upper: {threshold_upper}")
print(f"  Threshold Lower: -{threshold_upper}")
print()

# Step 5: Check trigger logic
print("Step 5: Checking Trigger Logic")
print("-" * 70)

should_trigger = False
reason = ""

if zscore >= threshold_upper:
    should_trigger = True
    reason = f"Z-score ({zscore:.4f}) >= threshold_upper ({threshold_upper})"
elif zscore <= -threshold_upper:
    should_trigger = True
    reason = f"Z-score ({zscore:.4f}) <= threshold_lower ({-threshold_upper})"
else:
    reason = f"Z-score ({zscore:.4f}) is within thresholds (±{threshold_upper})"

if should_trigger:
    print(f"  ✅ SHOULD TRIGGER!")
    print(f"  Reason: {reason}")
else:
    print(f"  ℹ️  Should NOT trigger")
    print(f"  Reason: {reason}")

print()

# Step 6: Summary
print("=" * 70)
print("Diagnostic Summary")
print("=" * 70)
print()

if should_trigger:
    print("✅ All checks passed - alert SHOULD be triggering!")
    print()
    print("If alerts still aren't triggering, check:")
    print("  1. API server logs for errors")
    print("  2. Background monitor is running (check http://localhost:8000/api/alerts/monitor/status)")
    print("  3. Rules aren't in cooldown period (check last_triggered_at)")
else:
    print(f"ℹ️  Alert won't trigger yet")
    print(f"   Current Z-score: {zscore:.4f}")
    print(f"   Needs to reach: ±{threshold_upper}")
    print(f"   Gap: {abs(abs(zscore) - threshold_upper):.4f}")
    print()
    print("Options:")
    print(f"  - Wait for Z-score to move beyond ±{threshold_upper}")
    print(f"  - Create rule with higher threshold (current Z-score is {zscore:.4f})")

print()
print("View full analysis:")
print("-" * 70)
print(f"Correlation: {analysis.get('correlation', {}).get('pearson', 'N/A')}")
print(f"Hedge Ratio: {analysis.get('hedge_ratio', {}).get('ratio', 'N/A')}")
print(f"Signal: {zscore_data.get('signal', 'N/A')}")
print()
