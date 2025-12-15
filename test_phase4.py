"""
Phase 4 verification - Analytics Engine
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
from loguru import logger
from config.settings import settings
from backend.storage.ohlc_repository import OHLCRepository
from backend.analytics.basic_stats import BasicStatsCalculator
from backend.analytics.pairs_analytics import PairsAnalyzer


def test_analytics_engine():
    """
    Test the complete analytics engine

    This will:
    1. Load OHLC data for both symbols
    2. Run basic statistics
    3. Run pair analytics
    4. Show all calculated metrics
    """
    print("=" * 70)
    print("Phase 4: Analytics Engine - Verification Test")
    print("=" * 70)
    print()

    # Test configuration
    TEST_SYMBOLS = ["BTCUSDT", "ETHUSDT"]
    TEST_TIMEFRAME = "1m"  # Use 1-minute bars
    ROLLING_WINDOW = 20

    print(f"📊 Test Configuration:")
    print(f"  • Symbols: {TEST_SYMBOLS}")
    print(f"  • Timeframe: {TEST_TIMEFRAME}")
    print(f"  • Rolling window: {ROLLING_WINDOW}")
    print()

    # Initialize components
    ohlc_repo = OHLCRepository()
    basic_stats = BasicStatsCalculator()
    pairs_analyzer = PairsAnalyzer()

    # Check OHLC data availability
    print("🔍 Checking OHLC data availability...")
    data_available = {}
    for symbol in TEST_SYMBOLS:
        count = ohlc_repo.get_ohlc_count(symbol, TEST_TIMEFRAME)
        data_available[symbol] = count
        print(f"  • {symbol}: {count} {TEST_TIMEFRAME} bars")

    if all(count == 0 for count in data_available.values()):
        print()
        print("❌ No OHLC data found!")
        print("   Please run test_phase3.py --full first to generate OHLC data.")
        return False

    print()

    # Load data
    print("📥 Loading OHLC data...")
    data = {}
    for symbol in TEST_SYMBOLS:
        bars = ohlc_repo.get_recent_ohlc(symbol, TEST_TIMEFRAME, limit=100)
        if bars:
            df = pd.DataFrame(bars)
            data[symbol] = df
            print(f"  • {symbol}: Loaded {len(df)} bars")
        else:
            print(f"  • {symbol}: No data")

    if len(data) < 2:
        print()
        print("❌ Need data for both symbols!")
        return False

    print()

    # Test 1: Basic Statistics
    print("=" * 70)
    print("Test 1: Basic Statistics")
    print("=" * 70)
    print()

    for symbol, df in data.items():
        print(f"📊 {symbol} Statistics:")
        try:
            stats = basic_stats.safe_calculate(df, rolling_window=ROLLING_WINDOW)

            if 'error' in stats:
                print(f"  ❌ Error: {stats['error']}")
                continue

            print(f"\n  Price Statistics:")
            print(f"    • Latest: ${stats['price_stats']['latest']:,.2f}")
            print(f"    • Mean: ${stats['price_stats']['mean']:,.2f}")
            print(f"    • Std Dev: ${stats['price_stats']['std']:,.2f}")
            print(f"    • Range: ${stats['price_stats']['range']:,.2f}")
            print(f"    • Change: {stats['price_stats']['change_pct']:.2f}%")

            print(f"\n  Volume Statistics:")
            if stats['volume_stats']:
                print(f"    • Total: {stats['volume_stats']['total']:,.2f}")
                print(f"    • Average: {stats['volume_stats']['mean']:,.2f}")
                print(f"    • Latest: {stats['volume_stats']['latest']:,.2f}")

            print(f"\n  Returns:")
            if 'error' not in stats['returns']:
                print(f"    • Mean: {stats['returns']['mean']*100:.4f}%")
                print(f"    • Std Dev: {stats['returns']['std']*100:.4f}%")
                print(f"    • Latest: {stats['returns']['latest']*100:.4f}%")

            print(f"\n  Volatility:")
            if 'error' not in stats['volatility']:
                print(f"    • Current: {stats['volatility']['current']*100:.4f}%")
                print(f"    • Annualized: {stats['volatility']['annualized']*100:.2f}%")

            if stats.get('vwap'):
                print(f"\n  VWAP:")
                print(f"    • Value: ${stats['vwap']['value']:,.2f}")
                print(f"    • Deviation: ${stats['vwap']['deviation']:,.2f} ({stats['vwap']['deviation_pct']:.2f}%)")

            print()

        except Exception as e:
            print(f"  ❌ Error calculating stats: {e}")
            print()

    # Test 2: Pair Analytics
    print("=" * 70)
    print("Test 2: Pair Analytics (BTC vs ETH)")
    print("=" * 70)
    print()

    try:
        # Merge data for pair analysis
        btc_data = data['BTCUSDT'].copy()
        eth_data = data['ETHUSDT'].copy()

        # Align by timestamp
        btc_data = btc_data.rename(columns={'close': 'btc_close'})
        eth_data = eth_data.rename(columns={'close': 'eth_close'})

        merged = pd.merge(
            btc_data[['timestamp', 'btc_close']],
            eth_data[['timestamp', 'eth_close']],
            on='timestamp',
            how='inner'
        )

        if len(merged) < ROLLING_WINDOW:
            print(f"❌ Not enough aligned data points: {len(merged)} (need {ROLLING_WINDOW})")
            return False

        print(f"✅ Aligned {len(merged)} data points")
        print()

        # Rename for pair analyzer
        merged = merged.rename(columns={'btc_close': 'close_x', 'eth_close': 'close_y'})

        # Calculate pair analytics
        pair_stats = pairs_analyzer.safe_calculate(
            merged,
            rolling_window=ROLLING_WINDOW,
            symbol1_name='BTCUSDT',
            symbol2_name='ETHUSDT'
        )

        if 'error' in pair_stats:
            print(f"❌ Error: {pair_stats['error']}")
            return False

        print(f"📈 Correlation Analysis:")
        corr = pair_stats['correlation']
        print(f"  • Pearson: {corr['pearson']:.4f} (p={corr['pearson_pvalue']:.4f})")
        print(f"  • Spearman: {corr['spearman']:.4f} (p={corr['spearman_pvalue']:.4f})")
        print(f"  • Strength: {corr['strength']}")
        print()

        print(f"🔧 Hedge Ratio (OLS Regression):")
        hedge = pair_stats['hedge_ratio']
        print(f"  • Ratio: {hedge['ratio']:.6f}")
        print(f"  • Intercept: {hedge['intercept']:.2f}")
        print(f"  • R²: {hedge['r_squared']:.4f}")
        print(f"  • Residual Std: {hedge['residual_std']:.2f}")
        print()

        print(f"🔬 Cointegration Test (ADF):")
        coint = pair_stats['cointegration']
        if 'error' not in coint:
            print(f"  • ADF Statistic: {coint['adf_statistic']:.4f}")
            print(f"  • P-value: {coint['pvalue']:.4f}")
            print(f"  • Critical Values:")
            print(f"    - 1%: {coint['critical_values']['1%']:.4f}")
            print(f"    - 5%: {coint['critical_values']['5%']:.4f}")
            print(f"    - 10%: {coint['critical_values']['10%']:.4f}")
            print(f"  • Cointegrated (5%): {'✅ Yes' if coint['is_cointegrated_5pct'] else '❌ No'}")
            print(f"  • Interpretation: {coint['interpretation']}")
        else:
            print(f"  ❌ Error: {coint['error']}")
        print()

        print(f"📊 Spread Statistics:")
        spread = pair_stats['spread']
        print(f"  • Mean: {spread['mean']:.2f}")
        print(f"  • Std Dev: {spread['std']:.2f}")
        print(f"  • Current: {spread['latest']:.2f}")
        print(f"  • Deviation from mean: {spread['deviation_from_mean']:.2f}")
        print()

        print(f"📉 Z-Score Analysis:")
        zscore = pair_stats['zscore']
        if 'error' not in zscore:
            print(f"  • Current: {zscore['current']:.4f}")
            print(f"  • Mean: {zscore['mean']:.4f}")
            print(f"  • Range: [{zscore['min']:.4f}, {zscore['max']:.4f}]")
            print(f"  • Signal: {zscore['signal']}")

            # Trading signal interpretation
            if zscore['current']:
                if abs(zscore['current']) > 2:
                    print(f"  ⚠️  STRONG MEAN REVERSION SIGNAL!")
                elif abs(zscore['current']) > 1:
                    print(f"  ⚡ Moderate mean reversion signal")
                else:
                    print(f"  ✅ Spread within normal range")
        else:
            print(f"  ❌ Error: {zscore['error']}")
        print()

        print(f"🔄 Rolling Correlation:")
        roll_corr = pair_stats['rolling_correlation']
        if 'error' not in roll_corr:
            print(f"  • Current: {roll_corr['current']:.4f}")
            print(f"  • Mean: {roll_corr['mean']:.4f}")
            print(f"  • Range: [{roll_corr['min']:.4f}, {roll_corr['max']:.4f}]")
        else:
            print(f"  ❌ Error: {roll_corr['error']}")
        print()

    except Exception as e:
        print(f"❌ Error in pair analytics: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Assessment
    print("=" * 70)
    print("📋 Assessment")
    print("=" * 70)
    print()

    success = True
    issues = []

    # Check basic stats
    try:
        if all('error' not in basic_stats.safe_calculate(df) for df in data.values()):
            print("✅ Basic statistics calculated successfully")
        else:
            issues.append("Some basic statistics failed")
            success = False
    except:
        issues.append("Basic statistics calculation failed")
        success = False

    # Check pair analytics
    if 'error' not in pair_stats:
        print("✅ Pair analytics calculated successfully")
    else:
        issues.append("Pair analytics failed")
        success = False

    # Check correlation
    if 'correlation' in pair_stats and abs(pair_stats['correlation']['pearson']) > 0:
        print("✅ Correlation analysis working")
    else:
        issues.append("Correlation analysis failed")

    # Check hedge ratio
    if 'hedge_ratio' in pair_stats and pair_stats['hedge_ratio']['ratio'] != 0:
        print("✅ Hedge ratio calculation working")
    else:
        issues.append("Hedge ratio calculation failed")

    # Check cointegration
    if 'cointegration' in pair_stats and 'error' not in pair_stats['cointegration']:
        print("✅ Cointegration test working")
    else:
        issues.append("Cointegration test failed")

    # Check z-score
    if 'zscore' in pair_stats and 'error' not in pair_stats['zscore']:
        print("✅ Z-score calculation working")
    else:
        issues.append("Z-score calculation failed")

    print()

    if success and not issues:
        print("🎉 Phase 4 Verification: PASSED")
        print()
        print("✅ All analytics working correctly:")
        print("   • Basic statistics (mean, std, VWAP, volatility)")
        print("   • Correlation analysis (Pearson, Spearman)")
        print("   • Hedge ratio calculation (OLS regression)")
        print("   • Cointegration testing (ADF test)")
        print("   • Spread and Z-score analysis")
        print("   • Rolling statistics")
        print()
        print("📁 Next: Proceed to Phase 5 - API Layer or Frontend")
        return True
    else:
        print("❌ Phase 4 Verification: FAILED")
        print()
        if issues:
            print("Issues found:")
            for issue in issues:
                print(f"   • {issue}")
        print()
        return False


def run_quick_component_test():
    """Quick test of analytics components"""
    print("=" * 70)
    print("Phase 4: Quick Component Test")
    print("=" * 70)
    print()

    # Test 1: Import all modules
    print("✓ Test 1: Module Imports")
    try:
        from backend.analytics.base_analyzer import BaseAnalyzer
        from backend.analytics.basic_stats import BasicStatsCalculator
        from backend.analytics.pairs_analytics import PairsAnalyzer
        print("  ✅ All modules imported successfully")
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False

    print()

    # Test 2: Create analyzers
    print("✓ Test 2: Analyzer Creation")
    try:
        basic_stats = BasicStatsCalculator()
        pairs_analyzer = PairsAnalyzer()
        print("  ✅ Analyzers created successfully")
        print(f"    - BasicStats: {basic_stats.name}")
        print(f"    - PairsAnalyzer: {pairs_analyzer.name}")
    except Exception as e:
        print(f"  ❌ Creation error: {e}")
        return False

    print()

    # Test 3: Basic stats with mock data
    print("✓ Test 3: Basic Statistics (Mock Data)")
    try:
        # Create mock OHLC data
        mock_data = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=30, freq='1min'),
            'open': [100 + i for i in range(30)],
            'high': [101 + i for i in range(30)],
            'low': [99 + i for i in range(30)],
            'close': [100 + i + (i % 3) for i in range(30)],
            'volume': [1000 + i * 10 for i in range(30)]
        })

        stats = basic_stats.safe_calculate(mock_data, rolling_window=10)

        if 'error' in stats:
            print(f"  ❌ Error: {stats['error']}")
            return False

        print("  ✅ Statistics calculated")
        print(f"    - Mean price: ${stats['price_stats']['mean']:.2f}")
        print(f"    - Volatility: {stats['volatility']['current']*100:.4f}%")
        print(f"    - VWAP: ${stats['vwap']['value']:.2f}")
    except Exception as e:
        print(f"  ❌ Calculation error: {e}")
        return False

    print()

    # Test 4: Pair analytics with mock data
    print("✓ Test 4: Pair Analytics (Mock Data)")
    try:
        # Create correlated mock data
        mock_btc = [50000 + i * 100 for i in range(30)]
        mock_eth = [3000 + i * 6 for i in range(30)]  # Roughly correlated

        mock_pair_data = pd.DataFrame({
            'timestamp': pd.date_range('2025-01-01', periods=30, freq='1min'),
            'close_x': mock_btc,
            'close_y': mock_eth
        })

        pair_stats = pairs_analyzer.safe_calculate(mock_pair_data, rolling_window=10)

        if 'error' in pair_stats:
            print(f"  ❌ Error: {pair_stats['error']}")
            return False

        print("  ✅ Pair analytics calculated")
        print(f"    - Correlation: {pair_stats['correlation']['pearson']:.4f}")
        print(f"    - Hedge ratio: {pair_stats['hedge_ratio']['ratio']:.6f}")
        if 'error' not in pair_stats['zscore'] and pair_stats['zscore']['current'] is not None:
            print(f"    - Z-score: {pair_stats['zscore']['current']:.4f}")
    except Exception as e:
        print(f"  ❌ Calculation error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()
    print("=" * 70)
    print("✅ All component tests passed!")
    print()
    print("Ready for full analytics test.")
    print("Run: python test_phase4.py --full")
    print("=" * 70)

    return True


if __name__ == "__main__":
    if "--full" in sys.argv:
        # Run full integration test
        test_analytics_engine()
    else:
        # Run quick component test
        run_quick_component_test()
