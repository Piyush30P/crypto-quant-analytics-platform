"""
Main ingestion service that coordinates WebSocket client, buffer, and database
"""
import asyncio
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger

from config.settings import settings
from backend.ingestion.binance_websocket import BinanceWebSocketClient
from backend.ingestion.data_buffer import TickDataBuffer
from backend.storage.tick_repository import TickDataRepository


class IngestionService:
    """
    Main service orchestrating real-time data ingestion pipeline
    
    Components:
    - WebSocket client (receives data from Binance)
    - Data buffer (accumulates ticks for batch insert)
    - Repository (writes to database)
    
    Flow: WebSocket → Buffer → Database
    """
    
    def __init__(self, symbols: Optional[List[str]] = None):
        """
        Initialize ingestion service
        
        Args:
            symbols: List of trading pairs to track
        """
        self.symbols = symbols or settings.DEFAULT_SYMBOLS
        
        # Components
        self.buffer = TickDataBuffer(
            max_size=settings.TICK_BUFFER_SIZE,
            flush_interval=1.0,
            on_flush_callback=self._on_buffer_flush
        )
        
        self.ws_client = BinanceWebSocketClient(
            symbols=self.symbols,
            on_message_callback=self._on_tick_received
        )
        
        self.repository = TickDataRepository()
        
        # State
        self.is_running = False
        self.start_time = None
        
        # Statistics
        self.ticks_received = 0
        self.ticks_stored = 0
        self.errors = 0
        
        logger.info(f"Initialized IngestionService for {len(self.symbols)} symbols: {self.symbols}")
    
    async def _on_tick_received(self, tick_data: Dict):
        """
        Callback when tick data is received from WebSocket
        
        Args:
            tick_data: Parsed tick data from Binance
        """
        try:
            self.ticks_received += 1
            
            # Add to buffer (buffer will auto-flush when full)
            await self.buffer.add(tick_data)
            
            # Log periodically
            if self.ticks_received % 100 == 0:
                logger.info(
                    f"Received {self.ticks_received} ticks, "
                    f"stored {self.ticks_stored}, "
                    f"buffer: {len(self.buffer)}"
                )
                
        except Exception as e:
            logger.error(f"Error processing tick: {e}")
            self.errors += 1
    
    async def _on_buffer_flush(self, records: List[Dict]):
        """
        Callback when buffer is flushed (batch insert to DB)
        
        Args:
            records: List of tick records to insert
        """
        try:
            # Batch insert to database
            inserted_count = await asyncio.to_thread(
                self.repository.insert_batch,
                records
            )
            
            self.ticks_stored += inserted_count
            
            logger.debug(
                f"Stored {inserted_count} ticks to database "
                f"(total: {self.ticks_stored})"
            )
            
        except Exception as e:
            logger.error(f"Error flushing buffer to database: {e}")
            self.errors += 1
            raise
    
    async def start(self):
        """
        Start the ingestion service
        
        This will:
        1. Start the data buffer auto-flush
        2. Connect to Binance WebSocket
        3. Begin receiving and storing tick data
        """
        if self.is_running:
            logger.warning("Ingestion service already running")
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info("Starting Ingestion Service")
        logger.info("=" * 60)
        logger.info(f"Symbols: {self.symbols}")
        logger.info(f"Buffer size: {settings.TICK_BUFFER_SIZE}")
        logger.info(f"Database: {settings.DATABASE_URL}")
        logger.info("=" * 60)
        
        try:
            # Start buffer auto-flush
            await self.buffer.start_auto_flush()
            
            # Start WebSocket client (this blocks until disconnect)
            await self.ws_client.start()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in ingestion service: {e}")
            self.errors += 1
        finally:
            await self.stop()
    
    async def stop(self):
        """
        Stop the ingestion service gracefully
        """
        if not self.is_running:
            return
        
        logger.info("Stopping ingestion service...")
        
        self.is_running = False
        
        # Stop WebSocket client
        await self.ws_client.disconnect()
        
        # Stop buffer and flush remaining data
        await self.buffer.stop_auto_flush()
        
        logger.info("=" * 60)
        logger.info("Ingestion Service Stopped")
        logger.info(f"Ticks received: {self.ticks_received}")
        logger.info(f"Ticks stored: {self.ticks_stored}")
        logger.info(f"Errors: {self.errors}")
        logger.info("=" * 60)
    
    def add_symbol(self, symbol: str):
        """
        Add a new symbol to track
        
        Note: Requires reconnection of WebSocket
        """
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            self.ws_client.add_symbol(symbol)
            logger.info(f"Added symbol: {symbol}")
    
    def remove_symbol(self, symbol: str):
        """
        Remove a symbol from tracking
        
        Note: Requires reconnection of WebSocket
        """
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            self.ws_client.remove_symbol(symbol)
            logger.info(f"Removed symbol: {symbol}")
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics"""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "service": {
                "is_running": self.is_running,
                "uptime_seconds": uptime,
                "symbols": self.symbols,
                "ticks_received": self.ticks_received,
                "ticks_stored": self.ticks_stored,
                "errors": self.errors
            },
            "websocket": self.ws_client.get_statistics(),
            "buffer": self.buffer.get_statistics()
        }


# Standalone execution
async def main():
    """Main entry point for standalone execution"""
    service = IngestionService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await service.stop()


if __name__ == "__main__":
    # Configure logging
    logger.add(
        "logs/ingestion.log",
        rotation="100 MB",
        retention="7 days",
        level="INFO"
    )
    
    asyncio.run(main())
