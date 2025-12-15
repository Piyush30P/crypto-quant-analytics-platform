"""
Data resampling service for converting tick data to OHLC bars
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from collections import defaultdict
import pandas as pd
from loguru import logger

from config.settings import settings
from backend.storage.tick_repository import TickDataRepository
from backend.storage.ohlc_repository import OHLCRepository


class DataResampler:
    """
    Resamples tick data into OHLC (Open, High, Low, Close) bars

    Supports multiple timeframes:
    - 1s (1 second)
    - 1m (1 minute)
    - 5m (5 minutes)

    Features:
    - Automatic resampling in background
    - Efficient pandas-based aggregation
    - VWAP calculation
    - Trade count tracking
    """

    def __init__(self, symbols: List[str], timeframes: Optional[List[str]] = None):
        """
        Initialize the data resampler

        Args:
            symbols: List of symbols to resample (e.g., ['BTCUSDT', 'ETHUSDT'])
            timeframes: List of timeframes (default: ['1s', '1m', '5m'])
        """
        self.symbols = symbols
        self.timeframes = timeframes or settings.RESAMPLE_INTERVAL_NAMES
        self.tick_repo = TickDataRepository()
        self.ohlc_repo = OHLCRepository()

        # Track last processed timestamp for each symbol
        self.last_processed: Dict[str, datetime] = {}

        # Running flag
        self.is_running = False
        self._resample_task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = {
            'bars_generated': 0,
            'ticks_processed': 0,
            'errors': 0,
            'last_resample_time': None
        }

        logger.info(
            f"Initialized DataResampler for {len(symbols)} symbols "
            f"with timeframes: {self.timeframes}"
        )

    def _timeframe_to_pandas_freq(self, timeframe: str) -> str:
        """
        Convert timeframe string to pandas frequency string

        Args:
            timeframe: Timeframe like '1s', '1m', '5m'

        Returns:
            Pandas frequency string like '1s', '1min', '5min'
        """
        mapping = {
            '1s': '1s',
            '1m': '1min',
            '5m': '5min',
            '15m': '15min',
            '1h': '1h',
            '4h': '4h',
            '1d': '1D'
        }
        return mapping.get(timeframe.lower(), timeframe.lower())

    def resample_ticks_to_ohlc(
        self,
        ticks: List[Dict],
        timeframe: str,
        symbol: str
    ) -> List[Dict]:
        """
        Resample tick data into OHLC bars using pandas

        Args:
            ticks: List of tick dictionaries
            timeframe: Target timeframe (1s, 1m, 5m)
            symbol: Trading pair symbol

        Returns:
            List of OHLC bar dictionaries
        """
        if not ticks:
            return []

        try:
            # Convert to DataFrame
            df = pd.DataFrame(ticks)

            # Ensure timestamp is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Set timestamp as index
            df.set_index('timestamp', inplace=True)

            # Sort by timestamp
            df.sort_index(inplace=True)

            # Convert timeframe to pandas frequency
            freq = self._timeframe_to_pandas_freq(timeframe)

            # Resample to OHLC
            ohlc = df['price'].resample(freq).agg(['first', 'max', 'min', 'last'])
            ohlc.columns = ['open', 'high', 'low', 'close']

            # Calculate volume
            volume = df['volume'].resample(freq).sum()

            # Calculate trade count
            trade_count = df['price'].resample(freq).count()

            # Calculate VWAP (Volume Weighted Average Price)
            df['price_volume'] = df['price'] * df['volume']
            price_volume_sum = df['price_volume'].resample(freq).sum()
            vwap = price_volume_sum / volume

            # Combine all metrics
            result_df = pd.concat([ohlc, volume, trade_count, vwap], axis=1)
            result_df.columns = ['open', 'high', 'low', 'close', 'volume', 'trade_count', 'vwap']

            # Drop rows with NaN (no data in that interval)
            result_df.dropna(subset=['open', 'close'], inplace=True)

            # Convert back to list of dictionaries
            ohlc_bars = []
            for timestamp, row in result_df.iterrows():
                ohlc_bars.append({
                    'timestamp': timestamp.to_pydatetime(),
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume']),
                    'trade_count': int(row['trade_count']),
                    'vwap': float(row['vwap']) if pd.notna(row['vwap']) else None
                })

            self.stats['ticks_processed'] += len(ticks)
            self.stats['bars_generated'] += len(ohlc_bars)

            logger.debug(
                f"Resampled {len(ticks)} ticks into {len(ohlc_bars)} "
                f"{timeframe} bars for {symbol}"
            )

            return ohlc_bars

        except Exception as e:
            logger.error(f"Error resampling ticks for {symbol} ({timeframe}): {e}")
            self.stats['errors'] += 1
            return []

    async def resample_symbol_timeframe(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """
        Resample ticks for a specific symbol and timeframe

        Args:
            symbol: Trading pair symbol
            timeframe: Target timeframe
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Number of OHLC bars generated
        """
        try:
            # Fetch ticks from database (returns dictionaries)
            ticks = self.tick_repo.get_ticks_by_timerange(
                symbol=symbol,
                start_time=start_time,
                end_time=end_time
            )

            if not ticks:
                logger.debug(f"No ticks found for {symbol} in range {start_time} to {end_time}")
                return 0

            # Resample to OHLC
            ohlc_bars = self.resample_ticks_to_ohlc(ticks, timeframe, symbol)

            if not ohlc_bars:
                return 0

            # Store OHLC bars
            bars_inserted = self.ohlc_repo.insert_batch(ohlc_bars)

            logger.info(
                f"Generated {bars_inserted} {timeframe} bars for {symbol} "
                f"from {len(ticks)} ticks"
            )

            return bars_inserted

        except Exception as e:
            logger.error(f"Error in resample_symbol_timeframe for {symbol}: {e}")
            self.stats['errors'] += 1
            return 0

    async def resample_all_pending(self) -> Dict[str, int]:
        """
        Resample all pending data for all symbols and timeframes

        Returns:
            Dictionary with statistics
        """
        results = {
            'total_bars': 0,
            'symbols_processed': 0,
            'errors': 0
        }

        try:
            # Calculate time window (last 5 minutes to now)
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=5)

            # Process each symbol
            for symbol in self.symbols:
                symbol_bars = 0

                # Process each timeframe
                for timeframe in self.timeframes:
                    bars_count = await self.resample_symbol_timeframe(
                        symbol=symbol,
                        timeframe=timeframe,
                        start_time=start_time,
                        end_time=end_time
                    )
                    symbol_bars += bars_count

                if symbol_bars > 0:
                    results['symbols_processed'] += 1
                    results['total_bars'] += symbol_bars

            self.stats['last_resample_time'] = datetime.now()

            logger.info(
                f"Resampling complete: {results['total_bars']} bars generated "
                f"for {results['symbols_processed']} symbols"
            )

        except Exception as e:
            logger.error(f"Error in resample_all_pending: {e}")
            results['errors'] += 1
            self.stats['errors'] += 1

        return results

    async def start(self, interval_seconds: int = 60):
        """
        Start automatic resampling in background

        Args:
            interval_seconds: How often to run resampling (default: 60 seconds)
        """
        if self.is_running:
            logger.warning("DataResampler is already running")
            return

        self.is_running = True
        logger.info(f"Starting DataResampler (interval: {interval_seconds}s)")

        try:
            while self.is_running:
                try:
                    # Perform resampling
                    results = await self.resample_all_pending()

                    # Wait for next interval
                    await asyncio.sleep(interval_seconds)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in resampler loop: {e}")
                    await asyncio.sleep(interval_seconds)

        finally:
            self.is_running = False
            logger.info("DataResampler stopped")

    async def stop(self):
        """Stop the automatic resampling"""
        if not self.is_running:
            return

        logger.info("Stopping DataResampler...")
        self.is_running = False

        if self._resample_task and not self._resample_task.done():
            self._resample_task.cancel()
            try:
                await self._resample_task
            except asyncio.CancelledError:
                pass

        logger.info("DataResampler stopped successfully")

    def get_statistics(self) -> Dict:
        """
        Get resampling statistics

        Returns:
            Dictionary with stats
        """
        return {
            'is_running': self.is_running,
            'symbols': self.symbols,
            'timeframes': self.timeframes,
            'bars_generated': self.stats['bars_generated'],
            'ticks_processed': self.stats['ticks_processed'],
            'errors': self.stats['errors'],
            'last_resample_time': self.stats['last_resample_time']
        }
