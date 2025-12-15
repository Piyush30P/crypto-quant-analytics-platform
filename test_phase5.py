"""
Phase 5 verification - API Layer
"""
import sys
import asyncio
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import httpx
from loguru import logger

# API configuration
API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 30.0


def test_api_layer():
    """
    Test the complete API layer

    This will:
    1. Check if API server is running
    2. Test health endpoint
    3. Test statistics endpoint
    4. Test OHLC endpoint
    5. Test ticks endpoint
    6. Test pair analysis endpoint
    7. Test symbols and timeframes endpoints
    """
    print("=" * 70)
    print("Phase 5: API Layer - Verification Test")
    print("=" * 70)
    print()

    # Test configuration
    TEST_SYMBOLS = ["BTCUSDT", "ETHUSDT"]
    TEST_TIMEFRAME = "1m"

    print(f"📊 Test Configuration:")
    print(f"  • API URL: {API_BASE_URL}")
    print(f"  • Test Symbols: {TEST_SYMBOLS}")
    print(f"  • Timeframe: {TEST_TIMEFRAME}")
    print()

    success = True
    issues = []

    # Test 1: Check if server is running
    print("=" * 70)
    print("Test 1: Server Connectivity")
    print("=" * 70)
    print()

    try:
        with httpx.Client(timeout=API_TIMEOUT) as client:
            print("🔍 Checking if API server is running...")
            try:
                response = client.get(f"{API_BASE_URL}/")
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Server is running")
                    print(f"  • API Name: {data.get('name')}")
                    print(f"  • Version: {data.get('version')}")
                    print(f"  • Status: {data.get('status')}")
                    print()
                else:
                    print(f"❌ Server returned status code: {response.status_code}")
                    issues.append("Server not returning 200 status")
                    success = False
            except httpx.ConnectError:
                print("❌ Cannot connect to API server!")
                print()
                print("Please start the API server in another terminal:")
                print("  python backend/api/app.py")
                print()
                print("Or use uvicorn:")
                print("  uvicorn backend.api.app:app --reload")
                print()
                return False
            except Exception as e:
                print(f"❌ Connection error: {e}")
                issues.append(f"Connection error: {e}")
                success = False
                return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    # Test 2: Health Check
    print("=" * 70)
    print("Test 2: Health Check Endpoint")
    print("=" * 70)
    print()

    try:
        with httpx.Client(timeout=API_TIMEOUT) as client:
            print("🔍 Testing /api/health...")
            response = client.get(f"{API_BASE_URL}/api/health")

            if response.status_code == 200:
                data = response.json()
                print("✅ Health check passed")
                print(f"  • Status: {data.get('status')}")
                print(f"  • Timestamp: {data.get('timestamp')}")

                components = data.get('components', {})
                print(f"  • Components:")
                print(f"    - Database: {components.get('database')}")
                print(f"    - Analytics: {components.get('analytics')}")
                print()
            else:
                print(f"❌ Health check failed: {response.status_code}")
                print(f"  Response: {response.text}")
                issues.append("Health check endpoint failed")
                success = False

    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        issues.append(f"Health check error: {e}")
        success = False

    # Test 3: Statistics Endpoint
    print("=" * 70)
    print("Test 3: Statistics Endpoint")
    print("=" * 70)
    print()

    try:
        with httpx.Client(timeout=API_TIMEOUT) as client:
            for symbol in TEST_SYMBOLS:
                print(f"🔍 Testing /api/stats/{symbol}...")
                response = client.get(
                    f"{API_BASE_URL}/api/stats/{symbol}",
                    params={"timeframe": TEST_TIMEFRAME, "limit": 50, "rolling_window": 10}
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Statistics for {symbol}")
                    print(f"  • Symbol: {data.get('symbol')}")
                    print(f"  • Data points: {data.get('data_points')}")

                    price_stats = data.get('price_stats', {})
                    if price_stats:
                        print(f"  • Latest Price: ${price_stats.get('latest'):,.2f}")
                        print(f"  • Mean: ${price_stats.get('mean'):,.2f}")
                        print(f"  • Change: {price_stats.get('change_pct'):.2f}%")

                    volatility = data.get('volatility', {})
                    if volatility and 'current' in volatility and volatility['current']:
                        print(f"  • Volatility: {volatility.get('current')*100:.4f}%")

                    print()
                elif response.status_code == 404:
                    print(f"⚠️  No data found for {symbol}")
                    print(f"  Run test_phase3.py --full to generate OHLC data")
                    print()
                else:
                    print(f"❌ Statistics endpoint failed: {response.status_code}")
                    print(f"  Response: {response.text}")
                    issues.append(f"Statistics endpoint failed for {symbol}")
                    success = False

    except Exception as e:
        print(f"❌ Error testing statistics endpoint: {e}")
        issues.append(f"Statistics error: {e}")
        success = False

    # Test 4: OHLC Endpoint
    print("=" * 70)
    print("Test 4: OHLC Data Endpoint")
    print("=" * 70)
    print()

    try:
        with httpx.Client(timeout=API_TIMEOUT) as client:
            symbol = TEST_SYMBOLS[0]
            print(f"🔍 Testing /api/ohlc/{symbol}...")
            response = client.get(
                f"{API_BASE_URL}/api/ohlc/{symbol}",
                params={"timeframe": TEST_TIMEFRAME, "limit": 20}
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ OHLC data for {symbol}")
                print(f"  • Symbol: {data.get('symbol')}")
                print(f"  • Timeframe: {data.get('timeframe')}")
                print(f"  • Bars returned: {len(data.get('bars', []))}")

                bars = data.get('bars', [])
                if bars:
                    latest = bars[-1]
                    print(f"  • Latest bar:")
                    print(f"    - Time: {latest.get('timestamp')}")
                    print(f"    - Close: ${latest.get('close'):,.2f}")
                    print(f"    - Volume: {latest.get('volume'):,.2f}")
                print()
            elif response.status_code == 404:
                print(f"⚠️  No OHLC data found for {symbol}")
                print(f"  Run test_phase3.py --full to generate OHLC data")
                print()
            else:
                print(f"❌ OHLC endpoint failed: {response.status_code}")
                print(f"  Response: {response.text}")
                issues.append(f"OHLC endpoint failed")
                success = False

    except Exception as e:
        print(f"❌ Error testing OHLC endpoint: {e}")
        issues.append(f"OHLC error: {e}")
        success = False

    # Test 5: Ticks Endpoint
    print("=" * 70)
    print("Test 5: Tick Data Endpoint")
    print("=" * 70)
    print()

    try:
        with httpx.Client(timeout=API_TIMEOUT) as client:
            symbol = TEST_SYMBOLS[0]
            print(f"🔍 Testing /api/ticks/{symbol}...")
            response = client.get(
                f"{API_BASE_URL}/api/ticks/{symbol}",
                params={"limit": 10}
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Tick data for {symbol}")
                print(f"  • Symbol: {data.get('symbol')}")
                print(f"  • Ticks returned: {len(data.get('ticks', []))}")

                ticks = data.get('ticks', [])
                if ticks:
                    latest = ticks[-1]
                    print(f"  • Latest tick:")
                    print(f"    - Time: {latest.get('timestamp')}")
                    print(f"    - Price: ${latest.get('price'):,.2f}")
                    print(f"    - Quantity: {latest.get('quantity'):.4f}")
                print()
            elif response.status_code == 404:
                print(f"⚠️  No tick data found for {symbol}")
                print(f"  Run test_phase2.py to collect tick data")
                print()
            else:
                print(f"❌ Ticks endpoint failed: {response.status_code}")
                print(f"  Response: {response.text}")
                issues.append(f"Ticks endpoint failed")
                success = False

    except Exception as e:
        print(f"❌ Error testing ticks endpoint: {e}")
        issues.append(f"Ticks error: {e}")
        success = False

    # Test 6: Pair Analysis Endpoint
    print("=" * 70)
    print("Test 6: Pair Analysis Endpoint")
    print("=" * 70)
    print()

    try:
        with httpx.Client(timeout=API_TIMEOUT) as client:
            print(f"🔍 Testing /api/pairs/analyze...")
            payload = {
                "symbol1": TEST_SYMBOLS[0],
                "symbol2": TEST_SYMBOLS[1],
                "timeframe": TEST_TIMEFRAME,
                "rolling_window": 10,
                "limit": 50
            }
            response = client.post(
                f"{API_BASE_URL}/api/pairs/analyze",
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Pair analysis for {TEST_SYMBOLS[0]} vs {TEST_SYMBOLS[1]}")
                print(f"  • Symbol 1: {data.get('symbol1')}")
                print(f"  • Symbol 2: {data.get('symbol2')}")
                print(f"  • Data points: {data.get('data_points')}")

                correlation = data.get('correlation', {})
                if correlation:
                    print(f"  • Pearson Correlation: {correlation.get('pearson'):.4f}")
                    print(f"  • Strength: {correlation.get('strength')}")

                hedge_ratio = data.get('hedge_ratio', {})
                if hedge_ratio:
                    print(f"  • Hedge Ratio: {hedge_ratio.get('ratio'):.6f}")
                    print(f"  • R²: {hedge_ratio.get('r_squared'):.4f}")

                cointegration = data.get('cointegration', {})
                if cointegration and 'error' not in cointegration:
                    print(f"  • Cointegrated: {'✅' if cointegration.get('is_cointegrated_5pct') else '❌'}")
                    print(f"  • P-value: {cointegration.get('pvalue'):.4f}")

                zscore = data.get('zscore', {})
                if zscore and 'error' not in zscore and zscore.get('current') is not None:
                    print(f"  • Z-Score: {zscore.get('current'):.4f}")
                    print(f"  • Signal: {zscore.get('signal')}")

                print()
            elif response.status_code == 404:
                print(f"⚠️  Not enough data for pair analysis")
                print(f"  Run test_phase3.py --full to generate OHLC data")
                print()
            else:
                print(f"❌ Pair analysis endpoint failed: {response.status_code}")
                print(f"  Response: {response.text}")
                issues.append(f"Pair analysis endpoint failed")
                success = False

    except Exception as e:
        print(f"❌ Error testing pair analysis endpoint: {e}")
        issues.append(f"Pair analysis error: {e}")
        success = False

    # Test 7: Symbols and Timeframes Endpoints
    print("=" * 70)
    print("Test 7: Symbols and Timeframes Endpoints")
    print("=" * 70)
    print()

    try:
        with httpx.Client(timeout=API_TIMEOUT) as client:
            # Test symbols endpoint
            print(f"🔍 Testing /api/symbols...")
            response = client.get(f"{API_BASE_URL}/api/symbols")

            if response.status_code == 200:
                symbols = response.json()  # Response is a list, not a dict
                print(f"✅ Symbols endpoint")
                print(f"  • Available symbols: {len(symbols)}")
                if symbols:
                    print(f"  • Symbols: {', '.join(symbols[:5])}")
                print()
            else:
                print(f"❌ Symbols endpoint failed: {response.status_code}")
                issues.append("Symbols endpoint failed")
                success = False

            # Test timeframes endpoint
            symbol = TEST_SYMBOLS[0]
            print(f"🔍 Testing /api/timeframes/{symbol}...")
            response = client.get(f"{API_BASE_URL}/api/timeframes/{symbol}")

            if response.status_code == 200:
                timeframes = response.json()  # Response is a list, not a dict
                print(f"✅ Timeframes endpoint")
                print(f"  • Available timeframes: {len(timeframes)}")
                if timeframes:
                    print(f"  • Timeframes: {', '.join(timeframes)}")
                print()
            elif response.status_code == 404:
                print(f"⚠️  No data found for {symbol}")
                print()
            else:
                print(f"❌ Timeframes endpoint failed: {response.status_code}")
                issues.append("Timeframes endpoint failed")
                success = False

    except Exception as e:
        print(f"❌ Error testing symbols/timeframes endpoints: {e}")
        issues.append(f"Symbols/timeframes error: {e}")
        success = False

    # Test 8: API Documentation
    print("=" * 70)
    print("Test 8: API Documentation")
    print("=" * 70)
    print()

    try:
        with httpx.Client(timeout=API_TIMEOUT) as client:
            print(f"🔍 Testing /docs...")
            response = client.get(f"{API_BASE_URL}/docs")

            if response.status_code == 200:
                print("✅ Swagger UI documentation available")
                print(f"  • URL: {API_BASE_URL}/docs")
                print()
            else:
                print(f"⚠️  Documentation not available: {response.status_code}")

            print(f"🔍 Testing /redoc...")
            response = client.get(f"{API_BASE_URL}/redoc")

            if response.status_code == 200:
                print("✅ ReDoc documentation available")
                print(f"  • URL: {API_BASE_URL}/redoc")
                print()
            else:
                print(f"⚠️  ReDoc not available: {response.status_code}")

    except Exception as e:
        print(f"⚠️  Error checking documentation: {e}")

    # Assessment
    print("=" * 70)
    print("📋 Assessment")
    print("=" * 70)
    print()

    if success and not issues:
        print("🎉 Phase 5 Verification: PASSED")
        print()
        print("✅ All API endpoints working correctly:")
        print("   • Health check endpoint")
        print("   • Statistics endpoint with comprehensive metrics")
        print("   • OHLC data endpoint with candlestick bars")
        print("   • Tick data endpoint for raw price data")
        print("   • Pair analysis endpoint with correlations")
        print("   • Symbols and timeframes listing endpoints")
        print("   • Interactive API documentation (Swagger UI & ReDoc)")
        print()
        print("📚 API Documentation:")
        print(f"   • Swagger UI: {API_BASE_URL}/docs")
        print(f"   • ReDoc: {API_BASE_URL}/redoc")
        print()
        print("📁 Next Steps:")
        print("   • Phase 6: Frontend Dashboard (Streamlit + Plotly)")
        print("   • Phase 7: Alert System (Z-score notifications)")
        print()
        print("💡 API Usage Example:")
        print(f"   curl {API_BASE_URL}/api/stats/BTCUSDT?timeframe=1m&limit=100")
        print()
        return True
    else:
        print("❌ Phase 5 Verification: FAILED")
        print()
        if issues:
            print("Issues found:")
            for issue in issues:
                print(f"   • {issue}")
        print()
        return False


def run_quick_component_test():
    """Quick test of API components"""
    print("=" * 70)
    print("Phase 5: Quick Component Test")
    print("=" * 70)
    print()

    # Test 1: Import all modules
    print("✓ Test 1: Module Imports")
    try:
        from backend.api.app import app
        from backend.api.routes import router
        from backend.api import schemas
        print("  ✅ All API modules imported successfully")
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False

    print()

    # Test 2: FastAPI app configuration
    print("✓ Test 2: FastAPI Application")
    try:
        from backend.api.app import app
        print("  ✅ FastAPI app created")
        print(f"    - Title: {app.title}")
        print(f"    - Version: {app.version}")
        print(f"    - Docs URL: {app.docs_url}")
    except Exception as e:
        print(f"  ❌ App creation error: {e}")
        return False

    print()

    # Test 3: Schema models
    print("✓ Test 3: Pydantic Schemas")
    try:
        from backend.api.schemas import (
            SymbolRequest,
            PairAnalysisRequest,
            BasicStatsResponse,
            PairAnalysisResponse
        )

        # Test request model
        pair_request = PairAnalysisRequest(
            symbol1="BTCUSDT",
            symbol2="ETHUSDT",
            timeframe="1m",
            rolling_window=20,
            limit=100
        )
        print("  ✅ Pydantic models working")
        print(f"    - Request: {pair_request.symbol1} vs {pair_request.symbol2}")
        print(f"    - Validation: ✓")
    except Exception as e:
        print(f"  ❌ Schema error: {e}")
        return False

    print()

    # Test 4: Routes registration
    print("✓ Test 4: API Routes")
    try:
        from backend.api.app import app
        routes = [route.path for route in app.routes]
        api_routes = [r for r in routes if r.startswith('/api')]

        print("  ✅ Routes registered")
        print(f"    - Total routes: {len(routes)}")
        print(f"    - API routes: {len(api_routes)}")
        print(f"    - Key endpoints:")
        for route in api_routes[:8]:
            print(f"      • {route}")
    except Exception as e:
        print(f"  ❌ Routes error: {e}")
        return False

    print()
    print("=" * 70)
    print("✅ All component tests passed!")
    print()
    print("Ready for full API test.")
    print()
    print("To test the API:")
    print("1. Start the API server in another terminal:")
    print("   python backend/api/app.py")
    print()
    print("2. Run the full test:")
    print("   python test_phase5.py --full")
    print()
    print("Or use uvicorn for development:")
    print("   uvicorn backend.api.app:app --reload")
    print("=" * 70)

    return True


if __name__ == "__main__":
    if "--full" in sys.argv:
        # Run full integration test
        test_api_layer()
    else:
        # Run quick component test
        run_quick_component_test()
