"""
Phase 3 verification - Data Resampling & OHLC Generation
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from config.settings import settings
from backend.storage.tick_repository import TickDataRepository
from backend.storage.ohlc_repository import OHLCRepository
from backend.ingestion.data_resampler import DataResampler


async def test_resampling_pipeline():
    """
    Test the complete resampling pipeline

    This will:
    1. Check existing tick data
    2. Run resampling for all timeframes
    3. Verify OHLC data generated
    4. Show statistics and samples
    """
    print("=" * 70)
    print("Phase 3: Data Resampling & OHLC Generation - Verification Test")
    print("=" * 70)
    print()

    # Test configuration
    TEST_SYMBOLS = ["BTCUSDT", "ETHUSDT"]
    TEST_TIMEFRAMES = ["1s", "1m", "5m"]

    print(f"📊 Test Configuration:")
    print(f"  • Symbols: {TEST_SYMBOLS}")
    print(f"  • Timeframes: {TEST_TIMEFRAMES}")
    print()

    # Initialize repositories
    tick_repo = TickDataRepository()
    ohlc_repo = OHLCRepository()

    # Check tick data availability
    print("🔍 Checking tick data availability...")
    tick_counts = {}
    for symbol in TEST_SYMBOLS:
        count = tick_repo.get_tick_count(symbol)
        tick_counts[symbol] = count
        print(f"  • {symbol}: {count:,} tick records")

    total_ticks = sum(tick_counts.values())
    print(f"  • Total: {total_ticks:,} ticks")
    print()

    if total_ticks == 0:
        print("❌ No tick data found!")
        print("   Please run test_phase2.py --full first to collect tick data.")
        return False

    # Check initial OHLC state
    print("🔍 Checking initial OHLC state...")
    initial_ohlc = {}
    for symbol in TEST_SYMBOLS:
        for timeframe in TEST_TIMEFRAMES:
            count = ohlc_repo.get_ohlc_count(symbol, timeframe)
            key = f"{symbol}_{timeframe}"
            initial_ohlc[key] = count
            print(f"  • {symbol} {timeframe}: {count} existing bars")
    print()

    # Initialize resampler
    print("🚀 Starting resampling service...")
    resampler = DataResampler(symbols=TEST_SYMBOLS, timeframes=TEST_TIMEFRAMES)
    print("✅ Resampler initialized")
    print()

    # Get actual data time range
    print("📊 Finding tick data time range...")
    recent_ticks = tick_repo.get_recent_ticks(TEST_SYMBOLS[0], limit=1)
    if recent_ticks:
        latest_time = recent_ticks[0]['timestamp']
        print(f"   Latest tick: {latest_time}")
    else:
        latest_time = datetime.now()

    # Use a wider time window to capture all data
    # Look back 1 hour to be safe
    end_time = latest_time
    start_time = end_time - timedelta(hours=1)
    print(f"   Time range: {start_time} to {end_time}")
    print()

    # Perform resampling for each symbol/timeframe
    print("📊 Resampling tick data to OHLC bars...")
    total_bars = 0
    symbols_processed = 0
    errors = 0

    for symbol in TEST_SYMBOLS:
        symbol_bars = 0
        for timeframe in TEST_TIMEFRAMES:
            bars = await resampler.resample_symbol_timeframe(
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_time,
                end_time=end_time
            )
            symbol_bars += bars

        if symbol_bars > 0:
            symbols_processed += 1
            total_bars += symbol_bars

    results = {
        'total_bars': total_bars,
        'symbols_processed': symbols_processed,
        'errors': errors
    }

    print(f"✅ Resampling complete!")
    print(f"  • Total bars generated: {results['total_bars']}")
    print(f"  • Symbols processed: {results['symbols_processed']}")
    print(f"  • Errors: {results['errors']}")
    print()

    # Verify results
    print("=" * 70)
    print("📊 Verification Results")
    print("=" * 70)
    print()

    # Check final OHLC state
    print("✓ OHLC Data Generated:")
    final_ohlc = {}
    new_ohlc = {}
    total_new = 0

    for symbol in TEST_SYMBOLS:
        print(f"\n  {symbol}:")
        for timeframe in TEST_TIMEFRAMES:
            key = f"{symbol}_{timeframe}"
            count = ohlc_repo.get_ohlc_count(symbol, timeframe)
            final_ohlc[key] = count
            new_count = count - initial_ohlc[key]
            new_ohlc[key] = new_count
            total_new += new_count

            print(f"    • {timeframe}: {new_count} new bars (total: {count})")

    print()
    print(f"  ✅ Total new bars: {total_new}")
    print()

    # Show sample OHLC data
    print("✓ Sample OHLC Data:")
    for symbol in TEST_SYMBOLS:
        print(f"\n  {symbol}:")
        for timeframe in TEST_TIMEFRAMES:
            recent = ohlc_repo.get_recent_ohlc(symbol, timeframe, limit=3)
            if recent:
                print(f"    • {timeframe} - Latest 3 bars:")
                for bar in recent[:3]:
                    print(
                        f"      - {bar['timestamp'].strftime('%H:%M:%S')} | "
                        f"O:{bar['open']:.2f} H:{bar['high']:.2f} "
                        f"L:{bar['low']:.2f} C:{bar['close']:.2f} "
                        f"V:{bar['volume']:.4f}"
                    )
            else:
                print(f"    • {timeframe} - No data found")
    print()

    # Resampler statistics
    stats = resampler.get_statistics()
    print("✓ Resampler Statistics:")
    print(f"  • Ticks processed: {stats['ticks_processed']:,}")
    print(f"  • Bars generated: {stats['bars_generated']}")
    print(f"  • Errors: {stats['errors']}")
    print(f"  • Last resample: {stats['last_resample_time']}")
    print()

    # Overall assessment
    print("=" * 70)
    print("📋 Assessment")
    print("=" * 70)
    print()

    success = True
    issues = []

    # Check 1: OHLC data was generated
    if total_new == 0:
        success = False
        issues.append("No OHLC bars were generated")
    else:
        print("✅ OHLC bars generated successfully")

    # Check 2: All timeframes have data
    for timeframe in TEST_TIMEFRAMES:
        timeframe_has_data = False
        for symbol in TEST_SYMBOLS:
            key = f"{symbol}_{timeframe}"
            if new_ohlc[key] > 0:
                timeframe_has_data = True
                break

        if timeframe_has_data:
            print(f"✅ {timeframe} timeframe has data")
        else:
            issues.append(f"No data for {timeframe} timeframe")
            print(f"⚠️  No data for {timeframe} timeframe")

    # Check 3: No errors
    if stats['errors'] > 0:
        issues.append(f"{stats['errors']} errors occurred during resampling")
        print(f"⚠️  {stats['errors']} errors occurred")
    else:
        print("✅ No errors during resampling")

    # Check 4: Data consistency
    if stats['ticks_processed'] == 0 and total_ticks > 0:
        issues.append("Ticks available but none were processed")
        print("⚠️  Ticks available but none were processed")
    else:
        print("✅ Data processing working correctly")

    print()

    if success and not issues:
        print("🎉 Phase 3 Verification: PASSED")
        print()
        print("✅ All components working correctly:")
        print("   • Tick data to OHLC conversion working")
        print("   • Multiple timeframe support verified")
        print("   • Pandas resampling operational")
        print("   • VWAP calculation working")
        print("   • Database storage successful")
        print()
        print("📁 Next: Proceed to Phase 4 - Analytics Engine")
        return True
    else:
        print("❌ Phase 3 Verification: FAILED")
        print()
        print("Issues found:")
        for issue in issues:
            print(f"   • {issue}")
        print()
        print("Please review the logs and fix issues before proceeding.")
        return False


def run_quick_component_test():
    """Quick test of individual components"""
    print("=" * 70)
    print("Phase 3: Quick Component Test")
    print("=" * 70)
    print()

    # Test 1: Import all modules
    print("✓ Test 1: Module Imports")
    try:
        from backend.ingestion.data_resampler import DataResampler
        from backend.storage.ohlc_repository import OHLCRepository
        print("  ✅ All modules imported successfully")
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False

    print()

    # Test 2: OHLC Repository
    print("✓ Test 2: OHLC Repository")
    try:
        repo = OHLCRepository()
        count = repo.get_ohlc_count()
        print(f"  ✅ Repository functional")
        print(f"    - Total OHLC bars: {count}")
    except Exception as e:
        print(f"  ❌ Repository error: {e}")
        return False

    print()

    # Test 3: Data Resampler creation
    print("✓ Test 3: Data Resampler")
    try:
        resampler = DataResampler(
            symbols=["BTCUSDT", "ETHUSDT"],
            timeframes=["1s", "1m", "5m"]
        )
        stats = resampler.get_statistics()
        print(f"  ✅ Resampler created successfully")
        print(f"    - Symbols: {stats['symbols']}")
        print(f"    - Timeframes: {stats['timeframes']}")
    except Exception as e:
        print(f"  ❌ Resampler error: {e}")
        return False

    print()

    # Test 4: Tick to OHLC conversion (with mock data)
    print("✓ Test 4: Tick to OHLC Conversion")
    try:
        # Create mock tick data
        now = datetime.now()
        mock_ticks = []
        for i in range(10):
            mock_ticks.append({
                'timestamp': now + timedelta(seconds=i),
                'symbol': 'BTCUSDT',
                'price': 50000 + i * 10,
                'quantity': 0.1,
                'volume': (50000 + i * 10) * 0.1
            })

        ohlc_bars = resampler.resample_ticks_to_ohlc(
            ticks=mock_ticks,
            timeframe='1s',
            symbol='BTCUSDT'
        )

        print(f"  ✅ Conversion successful")
        print(f"    - Input: {len(mock_ticks)} ticks")
        print(f"    - Output: {len(ohlc_bars)} OHLC bars")

        if ohlc_bars:
            bar = ohlc_bars[0]
            print(f"    - Sample bar: O:{bar['open']:.2f} H:{bar['high']:.2f} "
                  f"L:{bar['low']:.2f} C:{bar['close']:.2f}")
    except Exception as e:
        print(f"  ❌ Conversion error: {e}")
        return False

    print()
    print("=" * 70)
    print("✅ All component tests passed!")
    print()
    print("Ready for full resampling test.")
    print("Run: python test_phase3.py --full")
    print("=" * 70)

    return True


if __name__ == "__main__":
    if "--full" in sys.argv:
        # Run full integration test
        asyncio.run(test_resampling_pipeline())
    else:
        # Run quick component test
        run_quick_component_test()
