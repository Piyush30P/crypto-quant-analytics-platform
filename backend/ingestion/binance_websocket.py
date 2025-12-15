"""
Binance WebSocket client for real-time tick data ingestion
"""
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Callable, Optional, Set
import websockets
from websockets.exceptions import (
    ConnectionClosed, 
    ConnectionClosedError, 
    ConnectionClosedOK
)
from loguru import logger

from config.settings import settings


class BinanceWebSocketClient:
    """
    Async WebSocket client for Binance real-time market data streams
    
    Features:
    - Multi-symbol subscription
    - Auto-reconnection with exponential backoff
    - Message validation and parsing
    - Callback-based data handling
    - Connection health monitoring
    """
    
    def __init__(
        self, 
        symbols: Optional[List[str]] = None,
        on_message_callback: Optional[Callable] = None
    ):
        """
        Initialize WebSocket client
        
        Args:
            symbols: List of trading pairs (e.g., ['BTCUSDT', 'ETHUSDT'])
            on_message_callback: Async function to handle incoming messages
        """
        self.symbols = symbols or settings.DEFAULT_SYMBOLS
        self.symbols = [s.lower() for s in self.symbols]  # Binance uses lowercase
        self.on_message_callback = on_message_callback
        
        # Connection management
        self.websocket = None
        self.is_connected = False
        self.is_running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.base_reconnect_delay = 1  # seconds
        self.max_reconnect_delay = 60  # seconds
        
        # Statistics
        self.messages_received = 0
        self.last_message_time = None
        self.connection_start_time = None
        self.errors_count = 0
        
        # Build WebSocket URL
        self.ws_url = self._build_websocket_url()
        
        logger.info(f"Initialized BinanceWebSocketClient for symbols: {self.symbols}")
    
    def _build_websocket_url(self) -> str:
        """
        Build Binance WebSocket URL for combined streams
        
        Returns:
            WebSocket URL with all symbol streams
        """
        # Use aggTrade stream for tick data (aggregated trades)
        # Format: wss://stream.binance.com:9443/stream?streams=<symbol>@aggTrade/<symbol>@aggTrade
        
        if len(self.symbols) == 1:
            # Single stream format
            url = f"wss://stream.binance.com:9443/ws/{self.symbols[0]}@aggTrade"
        else:
            # Combined streams format
            streams = "/".join([f"{symbol}@aggTrade" for symbol in self.symbols])
            url = f"wss://stream.binance.com:9443/stream?streams={streams}"
        
        logger.debug(f"WebSocket URL: {url}")
        return url
    
    def add_symbol(self, symbol: str):
        """Add a new symbol to track (requires reconnection)"""
        symbol = symbol.lower()
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            self.ws_url = self._build_websocket_url()
            logger.info(f"Added symbol: {symbol}")
    
    def remove_symbol(self, symbol: str):
        """Remove a symbol from tracking (requires reconnection)"""
        symbol = symbol.lower()
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            self.ws_url = self._build_websocket_url()
            logger.info(f"Removed symbol: {symbol}")
    
    async def connect(self):
        """Establish WebSocket connection"""
        try:
            logger.info(f"Connecting to Binance WebSocket...")
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            self.is_connected = True
            self.connection_start_time = time.time()
            self.reconnect_attempts = 0
            logger.info(f"✅ Connected to Binance WebSocket for {len(self.symbols)} symbols")
            
        except Exception as e:
            self.is_connected = False
            logger.error(f"Failed to connect to Binance WebSocket: {e}")
            raise
    
    async def disconnect(self):
        """Gracefully close WebSocket connection"""
        self.is_running = False
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
        self.is_connected = False
    
    def _parse_message(self, raw_message: str) -> Optional[Dict]:
        """
        Parse and validate incoming WebSocket message
        
        Args:
            raw_message: Raw JSON message from WebSocket
            
        Returns:
            Parsed message dict or None if invalid
        """
        try:
            message = json.loads(raw_message)
            
            # Binance combined stream format: {"stream": "...", "data": {...}}
            if "stream" in message and "data" in message:
                data = message["data"]
                
                # Extract relevant fields from aggTrade
                # aggTrade fields: e, E, s, a, p, q, f, l, T, m, M
                if data.get("e") == "aggTrade":
                    tick_data = {
                        "event_type": data["e"],  # aggTrade
                        "event_time": data["E"],  # Event time (ms)
                        "symbol": data["s"].upper(),  # Symbol (BTCUSDT)
                        "trade_id": data["a"],  # Aggregate trade ID
                        "price": float(data["p"]),  # Price
                        "quantity": float(data["q"]),  # Quantity
                        "first_trade_id": data["f"],  # First trade ID
                        "last_trade_id": data["l"],  # Last trade ID
                        "trade_time": data["T"],  # Trade time (ms)
                        "is_buyer_maker": data["m"],  # Buyer is maker
                        "timestamp": datetime.fromtimestamp(data["T"] / 1000.0)
                    }
                    return tick_data
                else:
                    logger.warning(f"Unknown event type: {data.get('e')}")
                    return None
            else:
                logger.warning(f"Invalid message format: {message}")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message: {e}")
            self.errors_count += 1
            return None
        except KeyError as e:
            logger.error(f"Missing required field in message: {e}")
            self.errors_count += 1
            return None
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            self.errors_count += 1
            return None
    
    async def _handle_message(self, message: Dict):
        """
        Handle parsed message (call user callback)
        
        Args:
            message: Parsed tick data
        """
        self.messages_received += 1
        self.last_message_time = time.time()
        
        if self.on_message_callback:
            try:
                if asyncio.iscoroutinefunction(self.on_message_callback):
                    await self.on_message_callback(message)
                else:
                    self.on_message_callback(message)
            except Exception as e:
                logger.error(f"Error in message callback: {e}")
                self.errors_count += 1
    
    async def _receive_messages(self):
        """Main message receiving loop"""
        try:
            async for raw_message in self.websocket:
                if not self.is_running:
                    break
                
                # Parse message
                message = self._parse_message(raw_message)
                
                if message:
                    await self._handle_message(message)
                    
        except ConnectionClosedOK:
            logger.info("WebSocket connection closed normally")
            self.is_connected = False
        except ConnectionClosedError as e:
            logger.error(f"WebSocket connection closed with error: {e}")
            self.is_connected = False
            raise
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            self.is_connected = False
            self.errors_count += 1
            raise
    
    async def _reconnect_with_backoff(self):
        """Reconnect with exponential backoff"""
        while self.reconnect_attempts < self.max_reconnect_attempts and self.is_running:
            delay = min(
                self.base_reconnect_delay * (2 ** self.reconnect_attempts),
                self.max_reconnect_delay
            )
            self.reconnect_attempts += 1
            
            logger.warning(
                f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} "
                f"in {delay:.1f} seconds..."
            )
            
            await asyncio.sleep(delay)
            
            try:
                await self.connect()
                logger.info("✅ Reconnected successfully!")
                return True
            except Exception as e:
                logger.error(f"Reconnection attempt {self.reconnect_attempts} failed: {e}")
        
        logger.error("Max reconnection attempts reached. Giving up.")
        return False
    
    async def start(self):
        """
        Start WebSocket client (main entry point)
        
        This method will run indefinitely until disconnect() is called
        """
        self.is_running = True
        
        try:
            await self.connect()
            
            while self.is_running:
                try:
                    await self._receive_messages()
                    
                    # If we get here, connection was closed
                    if self.is_running:
                        logger.warning("Connection lost. Attempting to reconnect...")
                        reconnected = await self._reconnect_with_backoff()
                        if not reconnected:
                            break
                    
                except Exception as e:
                    logger.error(f"Error in message loop: {e}")
                    if self.is_running:
                        reconnected = await self._reconnect_with_backoff()
                        if not reconnected:
                            break
                    else:
                        break
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Fatal error in WebSocket client: {e}")
        finally:
            await self.disconnect()
            logger.info("WebSocket client stopped")
    
    def get_statistics(self) -> Dict:
        """Get connection statistics"""
        uptime = None
        if self.connection_start_time:
            uptime = time.time() - self.connection_start_time
        
        last_msg_age = None
        if self.last_message_time:
            last_msg_age = time.time() - self.last_message_time
        
        return {
            "is_connected": self.is_connected,
            "is_running": self.is_running,
            "symbols_count": len(self.symbols),
            "symbols": self.symbols,
            "messages_received": self.messages_received,
            "errors_count": self.errors_count,
            "reconnect_attempts": self.reconnect_attempts,
            "uptime_seconds": uptime,
            "last_message_age_seconds": last_msg_age
        }


# Example usage
async def example_callback(message: Dict):
    """Example callback function"""
    print(f"Received: {message['symbol']} @ ${message['price']} (qty: {message['quantity']})")


async def main():
    """Example main function"""
    client = BinanceWebSocketClient(
        symbols=["BTCUSDT", "ETHUSDT"],
        on_message_callback=example_callback
    )
    
    try:
        await client.start()
    except KeyboardInterrupt:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
