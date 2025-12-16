"""
Generate demo OHLC data for dense chart visualization
Run this to quickly populate your database with sample data for testing
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.storage.database import get_db_sync
from backend.storage.models import OHLC
from sqlalchemy import text


def generate_demo_ohlc(symbol, timeframe, num_bars=500, base_price=85000):
    """Generate demo OHLC data"""
    print(f"\n📊 Generating {num_bars} {timeframe} bars for {symbol}...")

    bars = []
    current_time = datetime.now()

    # Determine time delta based on timeframe
    time_deltas = {
        '1s': timedelta(seconds=1),
        '1m': timedelta(minutes=1),
        '5m': timedelta(minutes=5),
        '15m': timedelta(minutes=15),
        '1h': timedelta(hours=1),
        '4h': timedelta(hours=4),
        '1d': timedelta(days=1)
    }

    delta = time_deltas.get(timeframe, timedelta(minutes=1))

    # Generate bars going backwards in time
    current_price = base_price
    for i in range(num_bars):
        timestamp = current_time - (delta * (num_bars - i))

        # Random price movement
        price_change = random.uniform(-0.02, 0.02)  # ±2% change
        current_price = current_price * (1 + price_change)

        open_price = current_price
        close_price = open_price * (1 + random.uniform(-0.01, 0.01))
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.005))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.005))
        volume = random.uniform(1000000, 5000000)

        bars.append({
            'timestamp': timestamp,
            'symbol': symbol,
            'timeframe': timeframe,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })

    return bars


def insert_bars(db, bars):
    """Insert bars into database"""
    try:
        # Delete existing data for the symbol and timeframe
        symbol = bars[0]['symbol']
        timeframe = bars[0]['timeframe']

        db.execute(
            text("DELETE FROM ohlc WHERE symbol = :symbol AND timeframe = :timeframe"),
            {"symbol": symbol, "timeframe": timeframe}
        )
        db.commit()
        print(f"   Cleared existing {symbol} {timeframe} data")

        # Insert new bars
        for bar in bars:
            ohlc = OHLC(**bar)
            db.add(ohlc)

        db.commit()
        print(f"   ✅ Inserted {len(bars)} bars")

    except Exception as e:
        db.rollback()
        print(f"   ❌ Error: {e}")


def main():
    """Generate demo data for all symbols and timeframes"""
    print("=" * 70)
    print("  📈 DEMO DATA GENERATOR - Dense Chart Visualization")
    print("=" * 70)

    # Configurations
    configs = [
        # Dense data for 1m timeframe (500 bars = ~8 hours of data)
        {'symbol': 'BTCUSDT', 'timeframe': '1m', 'num_bars': 500, 'base_price': 85000},
        {'symbol': 'ETHUSDT', 'timeframe': '1m', 'num_bars': 500, 'base_price': 2900},

        # Dense data for 5m timeframe (300 bars = ~25 hours of data)
        {'symbol': 'BTCUSDT', 'timeframe': '5m', 'num_bars': 300, 'base_price': 85000},
        {'symbol': 'ETHUSDT', 'timeframe': '5m', 'num_bars': 300, 'base_price': 2900},

        # Dense data for 1h timeframe (168 bars = ~1 week of data)
        {'symbol': 'BTCUSDT', 'timeframe': '1h', 'num_bars': 168, 'base_price': 85000},
        {'symbol': 'ETHUSDT', 'timeframe': '1h', 'num_bars': 168, 'base_price': 2900},
    ]

    db = get_db_sync()

    try:
        for config in configs:
            bars = generate_demo_ohlc(**config)
            insert_bars(db, bars)

        print("\n" + "=" * 70)
        print("  ✅ DEMO DATA GENERATION COMPLETE!")
        print("=" * 70)
        print("\n📊 Generated Data Summary:")
        print("   • BTCUSDT: 500 bars (1m), 300 bars (5m), 168 bars (1h)")
        print("   • ETHUSDT: 500 bars (1m), 300 bars (5m), 168 bars (1h)")
        print("\n🚀 Next Steps:")
        print("   1. Refresh your dashboard: http://localhost:8501")
        print("   2. Select a symbol (BTCUSDT or ETHUSDT)")
        print("   3. Choose timeframe: 1m (500 bars), 5m (300 bars), or 1h (168 bars)")
        print("   4. Set Data Points slider to match bar count")
        print("   5. Click 'Analyze' to see DENSE charts!")
        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
