"""WebSocket connector for real-time market data streaming."""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Callable, Optional

import pandas as pd
import websockets

from deepagents_crypto_trading.types import Exchange, Price


class WebSocketConnector(ABC):
    """Base class for WebSocket connectors."""

    def __init__(self, exchange: Exchange) -> None:
        """Initialize WebSocket connector.

        Args:
            exchange: The exchange to connect to.
        """
        self.exchange = exchange
        self._connection: Optional[websockets.WebSocketCommon] = None
        self._running = False
        self._callbacks: list[Callable[[dict], None]] = []
        self._reconnect_delay = 1
        self._max_reconnect_delay = 60

    @abstractmethod
    def get_stream_url(self) -> str:
        """Get WebSocket stream URL.

        Returns:
            WebSocket URL for the exchange.
        """
        ...

    @abstractmethod
    def get_subscribe_message(self, symbols: list[str]) -> str:
        """Get subscription message for symbols.

        Args:
            symbols: List of symbols to subscribe to.

        Returns:
            JSON subscription message.
        """
        ...

    def add_callback(self, callback: Callable[[dict], None]) -> None:
        """Add a callback for price updates.

        Args:
            callback: Function to call with price data.
        """
        self._callbacks.append(callback)

    async def connect(self) -> bool:
        """Connect to WebSocket.

        Returns:
            True if connected successfully.
        """
        try:
            self._connection = await websockets.connect(
                self.get_stream_url(),
                ping_interval=20,
                ping_timeout=10,
            )
            self._running = True
            self._reconnect_delay = 1
            return True
        except Exception:
            self._running = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        self._running = False
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def subscribe(self, symbols: list[str]) -> None:
        """Subscribe to symbol streams.

        Args:
            symbols: List of symbols to subscribe to.
        """
        if self._connection:
            message = self.get_subscribe_message(symbols)
            await self._connection.send(message)

    async def listen(self) -> None:
        """Listen for price updates."""
        while self._running and self._connection:
            try:
                message = await self._connection.recv()
                data = json.loads(message)
                for callback in self._callbacks:
                    callback(data)
            except Exception:
                await self._handle_disconnect()
                break

    async def _handle_disconnect(self) -> None:
        """Handle disconnection with auto-reconnect."""
        self._running = False
        if self._connection:
            await self._connection.close()
            self._connection = None

        # Exponential backoff for reconnection
        await asyncio.sleep(self._reconnect_delay)
        self._reconnect_delay = min(
            self._reconnect_delay * 2, self._max_reconnect_delay
        )

        if await self.connect():
            self._running = True


class BinanceWebSocketConnector(WebSocketConnector):
    """Binance WebSocket connector for real-time prices.

    Uses Binance combined stream API for real-time price updates.
    """

    def __init__(self) -> None:
        """Initialize Binance WebSocket connector."""
        super().__init__(Exchange.BINANCE)
        self._base_url = "wss://stream.binance.com:9443/ws"

    def get_stream_url(self) -> str:
        """Get WebSocket stream URL."""
        return self._base_url

    def get_subscribe_message(self, symbols: list[str]) -> str:
        """Get subscription message."""
        streams = [f"{s.lower()}@ticker" for s in symbols]
        return json.dumps({"method": "SUBSCRIBE", "params": streams, "id": 1})


class CoinbaseWebSocketConnector(WebSocketConnector):
    """Coinbase WebSocket connector for real-time prices."""

    def __init__(self) -> None:
        """Initialize Coinbase WebSocket connector."""
        super().__init__(Exchange.COINBASE)
        self._base_url = "wss://ws-feed.exchange.coinbase.com"

    def get_stream_url(self) -> str:
        """Get WebSocket stream URL."""
        return self._base_url

    def get_subscribe_message(self, symbols: list[str]) -> str:
        """Get subscription message."""
        product_ids = [f"{s.replace('USDT', '-USDT')}" for s in symbols]
        return json.dumps({
            "type": "subscribe",
            "product_ids": product_ids,
            "channels": ["ticker"],
        })


class WebSocketManager:
    """Manager for multiple WebSocket connectors."""

    def __init__(self) -> None:
        """Initialize WebSocket manager."""
        self._connectors: dict[Exchange, WebSocketConnector] = {}
        self._running = False

    def add_connector(self, connector: WebSocketConnector) -> None:
        """Add a WebSocket connector.

        Args:
            connector: The connector to add.
        """
        self._connectors[connector.exchange] = connector

    async def connect_all(self) -> dict[Exchange, bool]:
        """Connect to all exchanges.

        Returns:
            Dictionary of exchange to connection status.
        """
        results = {}
        for exchange, connector in self._connectors.items():
            results[exchange] = await connector.connect()
        self._running = True
        return results

    async def disconnect_all(self) -> None:
        """Disconnect from all exchanges."""
        self._running = False
        for connector in self._connectors.values():
            await connector.disconnect()

    async def subscribe_all(self, symbols: list[str]) -> None:
        """Subscribe to symbols on all exchanges.

        Args:
            symbols: List of symbols to subscribe to.
        """
        for connector in self._connectors.values():
            await connector.subscribe(symbols)

    async def listen(self) -> None:
        """Listen to all connectors."""
        tasks = []
        for connector in self._connectors.values():
            if connector._running:
                tasks.append(asyncio.create_task(connector.listen()))
        await asyncio.gather(*tasks)

    def is_connected(self, exchange: Exchange) -> bool:
        """Check if exchange is connected.

        Args:
            exchange: The exchange to check.

        Returns:
            True if connected.
        """
        connector = self._connectors.get(exchange)
        return connector is not None and connector._running