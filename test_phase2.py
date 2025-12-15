"""
Phase 2 verification - Data Ingestion Pipeline
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
from backend.ingestion.ingestion_service import IngestionService
from backend.storage.tick_repository import TickDataRepository


async def test_ingestion_pipeline():
    """
    Test the complete ingestion pipeline
    
    This will:
    1. Start ingestion service
    2. Collect data for 30 seconds
    3. Verify data in database
    4. Show statistics
    """
    print("=" * 70)
    print("Phase 2: Data Ingestion Pipeline - Verification Test")
    print("=" * 70)
    print()
    
    # Test configuration
    TEST_DURATION = 30  # seconds
    TEST_SYMBOLS = ["BTCUSDT", "ETHUSDT"]
    
    print(f"📊 Test Configuration:")
    print(f"  • Duration: {TEST_DURATION} seconds")
    print(f"  • Symbols: {TEST_SYMBOLS}")
    print(f"  • Buffer size: {settings.TICK_BUFFER_SIZE}")
    print()
    
    # Initialize repository
    repo = TickDataRepository()
    
    # Check initial state
    print("🔍 Checking initial database state...")
    initial_counts = {}
    for symbol in TEST_SYMBOLS:
        count = repo.get_tick_count(symbol)
        initial_counts[symbol] = count
        print(f"  • {symbol}: {count} existing records")
    print()
    
    # Initialize ingestion service
    print("🚀 Starting ingestion service...")
    service = IngestionService(symbols=TEST_SYMBOLS)
    
    # Start service in background
    service_task = asyncio.create_task(service.start())
    
    # Wait for connection
    await asyncio.sleep(3)
    
    if not service.ws_client.is_connected:
        print("❌ Failed to connect to Binance WebSocket")
        service_task.cancel()
        return False
    
    print("✅ Connected to Binance WebSocket")
    print()
    
    # Monitor for test duration
    print(f"📡 Collecting data for {TEST_DURATION} seconds...")
    print("   (You should see live price updates)")
    print()
    
    start_time = datetime.now()
    last_stats_time = start_time
    
    try:
        while (datetime.now() - start_time).total_seconds() < TEST_DURATION:
            await asyncio.sleep(1)
            
            # Print stats every 5 seconds
            if (datetime.now() - last_stats_time).total_seconds() >= 5:
                stats = service.get_statistics()
                print(f"⏱️  {(datetime.now() - start_time).total_seconds():.0f}s elapsed:")
                print(f"  • Ticks received: {stats['service']['ticks_received']}")
                print(f"  • Ticks stored: {stats['service']['ticks_stored']}")
                print(f"  • Buffer size: {stats['buffer']['buffer_size']}")
                print(f"  • WS messages: {stats['websocket']['messages_received']}")
                print()
                last_stats_time = datetime.now()
    
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    
    # Stop service
    print("🛑 Stopping ingestion service...")
    await service.stop()
    service_task.cancel()
    
    try:
        await service_task
    except asyncio.CancelledError:
        pass
    
    print()
    
    # Verify results
    print("=" * 70)
    print("📊 Verification Results")
    print("=" * 70)
    print()
    
    # Check final database state
    print("✓ Database Storage Check:")
    final_counts = {}
    new_records = {}
    total_new = 0
    
    for symbol in TEST_SYMBOLS:
        count = repo.get_tick_count(symbol)
        final_counts[symbol] = count
        new_records[symbol] = count - initial_counts[symbol]
        total_new += new_records[symbol]
        
        print(f"  • {symbol}:")
        print(f"    - Initial: {initial_counts[symbol]} records")
        print(f"    - Final: {count} records")
        print(f"    - New: {new_records[symbol]} records")
    
    print()
    print(f"  ✅ Total new records: {total_new}")
    print()
    
    # Service statistics
    final_stats = service.get_statistics()
    print("✓ Service Statistics:")
    print(f"  • Ticks received: {final_stats['service']['ticks_received']}")
    print(f"  • Ticks stored: {final_stats['service']['ticks_stored']}")
    print(f"  • Errors: {final_stats['service']['errors']}")
    print(f"  • WebSocket messages: {final_stats['websocket']['messages_received']}")
    print(f"  • Buffer flushes: {final_stats['buffer']['flush_count']}")
    print()
    
    # Sample data check
    print("✓ Sample Data Verification:")
    for symbol in TEST_SYMBOLS:
        recent = repo.get_recent_ticks(symbol, limit=3)
        if recent:
            print(f"  • {symbol} - Latest 3 ticks:")
            for tick in recent[:3]:
                print(f"    - {tick.timestamp.strftime('%H:%M:%S')} | "
                      f"${tick.price:,.2f} | qty: {tick.quantity:.4f}")
        else:
            print(f"  • {symbol} - No data found")
    print()
    
    # Overall assessment
    print("=" * 70)
    print("📋 Assessment")
    print("=" * 70)
    
    success = True
    issues = []
    
    # Check 1: Data was received
    if final_stats['service']['ticks_received'] == 0:
        success = False
        issues.append("No ticks received from WebSocket")
    else:
        print("✅ Ticks received from WebSocket")
    
    # Check 2: Data was stored
    if total_new == 0:
        success = False
        issues.append("No data stored to database")
    else:
        print("✅ Data stored to database")
    
    # Check 3: No errors
    if final_stats['service']['errors'] > 0:
        issues.append(f"{final_stats['service']['errors']} errors occurred")
        print(f"⚠️  {final_stats['service']['errors']} errors occurred")
    else:
        print("✅ No errors")
    
    # Check 4: Buffer functioning
    if final_stats['buffer']['flush_count'] == 0:
        success = False
        issues.append("Buffer never flushed")
    else:
        print("✅ Buffer flushing correctly")
    
    # Check 5: Data consistency
    stored_ratio = (final_stats['service']['ticks_stored'] / 
                   max(final_stats['service']['ticks_received'], 1))
    if stored_ratio < 0.9:
        issues.append(f"Data loss detected (only {stored_ratio*100:.1f}% stored)")
        print(f"⚠️  Possible data loss (stored: {stored_ratio*100:.1f}%)")
    else:
        print("✅ Data consistency verified")
    
    print()
    
    if success and not issues:
        print("🎉 Phase 2 Verification: PASSED")
        print()
        print("✅ All components working correctly:")
        print("   • WebSocket connection established")
        print("   • Real-time data streaming functional")
        print("   • Data buffering operational")
        print("   • Database storage working")
        print("   • Multi-symbol support verified")
        print()
        print("📁 Next: Proceed to Phase 3 - Data Resampling & OHLC")
        return True
    else:
        print("❌ Phase 2 Verification: FAILED")
        print()
        print("Issues found:")
        for issue in issues:
            print(f"   • {issue}")
        print()
        print("Please review the logs and fix issues before proceeding.")
        return False


def run_quick_component_test():
    """Quick test of individual components without full ingestion"""
    print("=" * 70)
    print("Phase 2: Quick Component Test")
    print("=" * 70)
    print()
    
    # Test 1: Import all modules
    print("✓ Test 1: Module Imports")
    try:
        from backend.ingestion.binance_websocket import BinanceWebSocketClient
        from backend.ingestion.data_buffer import TickDataBuffer
        from backend.storage.tick_repository import TickDataRepository
        from backend.ingestion.ingestion_service import IngestionService
        print("  ✅ All modules imported successfully")
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False
    
    print()
    
    # Test 2: Repository
    print("✓ Test 2: Tick Repository")
    try:
        repo = TickDataRepository()
        count = repo.get_tick_count()
        symbols = repo.get_available_symbols()
        print(f"  ✅ Repository functional")
        print(f"    - Total ticks: {count}")
        print(f"    - Symbols: {symbols if symbols else 'None yet'}")
    except Exception as e:
        print(f"  ❌ Repository error: {e}")
        return False
    
    print()
    
    # Test 3: Buffer creation
    print("✓ Test 3: Data Buffer")
    try:
        buffer = TickDataBuffer(max_size=10, flush_interval=1.0)
        stats = buffer.get_statistics()
        print(f"  ✅ Buffer created successfully")
        print(f"    - Max size: {stats['max_size']}")
        print(f"    - Current size: {stats['buffer_size']}")
    except Exception as e:
        print(f"  ❌ Buffer error: {e}")
        return False
    
    print()
    
    # Test 4: WebSocket client creation
    print("✓ Test 4: WebSocket Client")
    try:
        client = BinanceWebSocketClient(symbols=["BTCUSDT"])
        print(f"  ✅ WebSocket client created")
        print(f"    - URL: {client.ws_url[:60]}...")
        print(f"    - Symbols: {client.symbols}")
    except Exception as e:
        print(f"  ❌ WebSocket client error: {e}")
        return False
    
    print()
    
    # Test 5: Service initialization
    print("✓ Test 5: Ingestion Service")
    try:
        service = IngestionService(symbols=["BTCUSDT", "ETHUSDT"])
        stats = service.get_statistics()
        print(f"  ✅ Service initialized")
        print(f"    - Symbols: {stats['service']['symbols']}")
        print(f"    - Running: {stats['service']['is_running']}")
    except Exception as e:
        print(f"  ❌ Service error: {e}")
        return False
    
    print()
    print("=" * 70)
    print("✅ All component tests passed!")
    print()
    print("Ready for full ingestion test.")
    print("Run: python test_phase2.py --full")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    import sys
    
    if "--full" in sys.argv:
        # Run full integration test
        asyncio.run(test_ingestion_pipeline())
    else:
        # Run quick component test
        run_quick_component_test()
