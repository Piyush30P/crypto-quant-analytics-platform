"""
Data buffer for batch inserting tick data to optimize database writes
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from collections import deque
from loguru import logger

from config.settings import settings


class TickDataBuffer:
    """
    Buffer for accumulating tick data before batch insertion to database
    
    Features:
    - Configurable buffer size
    - Time-based flushing
    - Thread-safe operations
    - Overflow protection
    """
    
    def __init__(
        self,
        max_size: int = None,
        flush_interval: float = 1.0,
        on_flush_callback: Optional[callable] = None
    ):
        """
        Initialize tick data buffer
        
        Args:
            max_size: Maximum buffer size before auto-flush (default from settings)
            flush_interval: Seconds between automatic flushes
            on_flush_callback: Async function called when buffer is flushed
        """
        self.max_size = max_size or settings.TICK_BUFFER_SIZE
        self.flush_interval = flush_interval
        self.on_flush_callback = on_flush_callback
        
        # Buffer storage
        self.buffer: deque = deque(maxlen=self.max_size * 2)  # Extra room for overflow
        self._lock = asyncio.Lock()
        
        # Statistics
        self.total_added = 0
        self.total_flushed = 0
        self.flush_count = 0
        self.last_flush_time = datetime.now()
        
        # Background task
        self._flush_task = None
        self._running = False
        
        logger.info(f"Initialized TickDataBuffer (max_size={self.max_size}, flush_interval={flush_interval}s)")
    
    async def add(self, tick_data: Dict):
        """
        Add tick data to buffer
        
        Args:
            tick_data: Dictionary containing tick information
        """
        async with self._lock:
            # Convert to database-ready format
            db_record = {
                "timestamp": tick_data["timestamp"],
                "symbol": tick_data["symbol"],
                "price": tick_data["price"],
                "quantity": tick_data["quantity"],
                "volume": tick_data["price"] * tick_data["quantity"]
            }
            
            self.buffer.append(db_record)
            self.total_added += 1
            
            # Auto-flush if buffer is full
            if len(self.buffer) >= self.max_size:
                logger.debug(f"Buffer full ({len(self.buffer)} records), triggering flush")
                await self._flush()
    
    async def add_batch(self, tick_data_list: List[Dict]):
        """
        Add multiple tick records at once
        
        Args:
            tick_data_list: List of tick data dictionaries
        """
        async with self._lock:
            for tick_data in tick_data_list:
                db_record = {
                    "timestamp": tick_data["timestamp"],
                    "symbol": tick_data["symbol"],
                    "price": tick_data["price"],
                    "quantity": tick_data["quantity"],
                    "volume": tick_data["price"] * tick_data["quantity"]
                }
                self.buffer.append(db_record)
                self.total_added += 1
            
            # Auto-flush if buffer is full
            if len(self.buffer) >= self.max_size:
                await self._flush()
    
    async def _flush(self):
        """
        Internal flush method (should be called with lock held)
        
        Sends buffered data to callback and clears buffer
        """
        if len(self.buffer) == 0:
            return
        
        # Get all records from buffer
        records = list(self.buffer)
        self.buffer.clear()
        
        # Update statistics
        self.total_flushed += len(records)
        self.flush_count += 1
        self.last_flush_time = datetime.now()
        
        logger.debug(f"Flushing {len(records)} records to database (flush #{self.flush_count})")
        
        # Call user callback
        if self.on_flush_callback:
            try:
                if asyncio.iscoroutinefunction(self.on_flush_callback):
                    await self.on_flush_callback(records)
                else:
                    self.on_flush_callback(records)
            except Exception as e:
                logger.error(f"Error in flush callback: {e}")
                # Re-add records to buffer if flush failed
                async with self._lock:
                    self.buffer.extendleft(reversed(records))
                    self.total_flushed -= len(records)
                raise
    
    async def flush(self):
        """
        Manually trigger a flush
        
        Public method that acquires lock before flushing
        """
        async with self._lock:
            await self._flush()
    
    async def _auto_flush_loop(self):
        """Background task for periodic flushing"""
        logger.info(f"Starting auto-flush loop (interval={self.flush_interval}s)")
        
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                
                # Flush if buffer has data
                if len(self.buffer) > 0:
                    await self.flush()
                    
            except asyncio.CancelledError:
                logger.info("Auto-flush loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in auto-flush loop: {e}")
    
    async def start_auto_flush(self):
        """Start background auto-flush task"""
        if self._running:
            logger.warning("Auto-flush already running")
            return
        
        self._running = True
        self._flush_task = asyncio.create_task(self._auto_flush_loop())
        logger.info("Auto-flush started")
    
    async def stop_auto_flush(self):
        """Stop background auto-flush task"""
        if not self._running:
            return
        
        self._running = False
        
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Final flush before stopping
        await self.flush()
        
        logger.info("Auto-flush stopped")
    
    def get_statistics(self) -> Dict:
        """Get buffer statistics"""
        return {
            "buffer_size": len(self.buffer),
            "max_size": self.max_size,
            "total_added": self.total_added,
            "total_flushed": self.total_flushed,
            "flush_count": self.flush_count,
            "last_flush_time": self.last_flush_time.isoformat(),
            "is_running": self._running
        }
    
    def __len__(self):
        """Return current buffer size"""
        return len(self.buffer)
