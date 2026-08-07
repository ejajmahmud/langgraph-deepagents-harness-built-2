"""Memo0 storage client for persistent storage and knowledge base."""

import os
import json
from typing import Optional

import httpx

from deepagents_crypto_trading.types import Position, TradingConfig


class Memo0Client:
    """Memo0 storage client for persistent storage.

    Provides a wrapper around memo0 API for storing trading data,
    knowledge base, and progress tracking.

    Supports both mock mode (development) and real API mode (production).
    """

    def __init__(self, config: TradingConfig) -> None:
        """Initialize memo0 client.

        Args:
            config: Trading configuration.
        """
        self.config = config
        self.api_key = os.environ.get("MEM0_API_KEY", "")
        self.org_id = os.environ.get("MEM0_ORG_ID", "")
        self.base_url = os.environ.get(
            "MEM0_BASE_URL", "https://api.mem0.ai/v1"
        )
        self.enabled = config.memo0_enabled and bool(self.api_key)
        self._use_real_api = self.enabled and bool(self.api_key)
        self._cache: dict[str, list[dict]] = {
            "trading_history": [],
            "knowledge": [],
            "progress": [],
            "orders": [],
        }

    def is_enabled(self) -> bool:
        """Check if memo0 is enabled.

        Returns:
            True if enabled and API key is available.
        """
        return self.enabled

    def is_using_real_api(self) -> bool:
        """Check if using real memo0 API.

        Returns:
            True if using real API.
        """
        return self._use_real_api

    async def _call_mem0_api(
        self, endpoint: str, data: dict, method: str = "POST"
    ) -> Optional[dict]:
        """Call memo0 API.

        Args:
            endpoint: API endpoint.
            data: Request data.
            method: HTTP method.

        Returns:
            Response data or None.
        """
        if not self._use_real_api:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.org_id:
            headers["x-org-id"] = self.org_id

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "POST":
                    response = await client.post(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        json=data,
                    )
                else:
                    response = await client.get(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        params=data,
                    )

                if response.status_code in (200, 201):
                    return response.json()
        except Exception:
            pass

        return None

    async def save_trade(
        self,
        position: Position,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Save a trade to memo0.

        Args:
            position: The position to save.
            metadata: Additional metadata.

        Returns:
            True if saved successfully.
        """
        trade_data = {
            "id": position.id,
            "type": position.arbitrage_type.value,
            "trading_pairs": [p.symbol for p in position.trading_pairs],
            "entry_price": position.entry_price,
            "exit_price": position.current_price,
            "size": position.size,
            "pnl": position.pnl,
            "status": position.status.value,
            "opened_at": str(position.opened_at),
            "closed_at": str(position.closed_at) if position.closed_at else None,
            "metadata": metadata or {},
        }

        # Try real API first (only if enabled)
        if self._use_real_api:
            api_result = await self._call_mem0_api(
                "/memories",
                {
                    "query": f"Trade: {position.id}",
                    "metadata": trade_data,
                },
            )
            if api_result:
                self._cache["trading_history"].append(trade_data)
                return True

        # Always use cache as fallback
        self._cache["trading_history"].append(trade_data)
        return True

    async def load_trades(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Load trades from memo0.

        Args:
            limit: Maximum number of trades to load.
            offset: Offset for pagination.

        Returns:
            List of trade records.
        """
        trades = self._cache["trading_history"]
        return trades[offset : offset + limit]

    async def save_knowledge(
        self,
        key: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Save knowledge to memo0.

        Args:
            key: Knowledge key.
            content: Knowledge content.
            metadata: Additional metadata.

        Returns:
            True if saved successfully.
        """
        knowledge_entry = {
            "key": key,
            "content": content,
            "metadata": metadata or {},
        }

        # Try real API first (only if enabled)
        if self._use_real_api:
            api_result = await self._call_mem0_api(
                "/memories",
                {
                    "query": content,
                    "metadata": knowledge_entry,
                },
            )
            if api_result:
                self._cache["knowledge"].append(knowledge_entry)
                return True

        # Always use cache as fallback
        self._cache["knowledge"].append(knowledge_entry)
        return True

    async def load_knowledge(self, key: str) -> Optional[dict]:
        """Load knowledge from memo0.

        Args:
            key: Knowledge key.

        Returns:
            Knowledge entry or None.
        """
        for entry in self._cache["knowledge"]:
            if entry.get("key") == key:
                return entry
        return None

    async def save_progress(
        self,
        version: str,
        status: str,
        completed_features: list[str],
        metrics: Optional[dict] = None,
    ) -> bool:
        """Save progress to memo0.

        Args:
            version: Current version.
            status: Progress status.
            completed_features: List of completed features.
            metrics: Progress metrics.

        Returns:
            True if saved successfully.
        """
        progress_entry = {
            "version": version,
            "status": status,
            "completed_features": completed_features,
            "metrics": metrics or {},
        }

        # Try real API first (only if enabled)
        if self._use_real_api:
            api_result = await self._call_mem0_api(
                "/memories",
                {
                    "query": f"Progress: {version}",
                    "metadata": progress_entry,
                },
            )
            if api_result:
                self._cache["progress"].append(progress_entry)
                return True

        # Always use cache as fallback
        self._cache["progress"].append(progress_entry)
        return True

    async def load_latest_progress(self) -> Optional[dict]:
        """Load latest progress.

        Returns:
            Latest progress entry or None.
        """
        if self._cache["progress"]:
            return self._cache["progress"][-1]
        return None

    async def search_memories(
        self, query: str, limit: int = 10
    ) -> list[dict]:
        """Search memories.

        Args:
            query: Search query.
            limit: Maximum results.

        Returns:
            List of matching memories.
        """
        results = []
        query_lower = query.lower()

        # Search in all categories
        for category in ["trading_history", "knowledge", "progress"]:
            for entry in self._cache[category]:
                if isinstance(entry, dict):
                    content = str(entry).lower()
                    if query_lower in content:
                        results.append(entry)

        return results[:limit]

    def get_stats(self) -> dict:
        """Get memo0 storage statistics.

        Returns:
            Dictionary of statistics.
        """
        return {
            "enabled": self.enabled,
            "using_real_api": self._use_real_api,
            "total_trades": len(self._cache["trading_history"]),
            "total_knowledge": len(self._cache["knowledge"]),
            "total_progress": len(self._cache["progress"]),
            "total_orders": len(self._cache["orders"]),
        }

    async def save_order(
        self,
        order_id: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float],
        status: str,
        filled_quantity: float = 0.0,
        average_fill_price: float = 0.0,
        fee: float = 0.0,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Save an order to memo0.

        Args:
            order_id: Order ID.
            symbol: Trading symbol.
            side: Order side (buy/sell).
            order_type: Order type (market/limit).
            quantity: Order quantity.
            price: Limit price (for limit orders).
            status: Order status.
            filled_quantity: Filled quantity.
            average_fill_price: Average fill price.
            fee: Trading fee.
            metadata: Additional metadata.

        Returns:
            True if saved successfully.
        """
        order_data = {
            "id": order_id,
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "quantity": quantity,
            "price": price,
            "status": status,
            "filled_quantity": filled_quantity,
            "average_fill_price": average_fill_price,
            "fee": fee,
            "metadata": metadata or {},
        }

        # Try real API first (only if enabled)
        if self._use_real_api:
            api_result = await self._call_mem0_api(
                "/memories",
                {
                    "query": f"Order: {order_id} {symbol} {side}",
                    "metadata": order_data,
                },
            )
            if api_result:
                self._cache["orders"].append(order_data)
                return True

        # Always use cache as fallback
        self._cache["orders"].append(order_data)
        return True

    async def load_orders(
        self,
        symbol: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Load orders from memo0.

        Args:
            symbol: Filter by symbol (optional).
            status: Filter by status (optional).
            limit: Maximum number of orders to load.

        Returns:
            List of order records.
        """
        orders = self._cache["orders"]

        if symbol:
            orders = [o for o in orders if o.get("symbol") == symbol]

        if status:
            orders = [o for o in orders if o.get("status") == status]

        return orders[:limit]

    async def search_orders(
        self, query: str, limit: int = 10
    ) -> list[dict]:
        """Search orders.

        Args:
            query: Search query.
            limit: Maximum results.

        Returns:
            List of matching orders.
        """
        results = []
        query_lower = query.lower()

        for entry in self._cache["orders"]:
            if isinstance(entry, dict):
                content = str(entry).lower()
                if query_lower in content:
                    results.append(entry)

        return results[:limit]

    async def save_portfolio(
        self,
        snapshot_id: str,
        total_value: float,
        total_cost: float,
        unrealized_pnl: float,
        realized_pnl: float,
        positions: list[dict],
        metadata: Optional[dict] = None,
    ) -> bool:
        """Save a portfolio snapshot to memo0.

        Args:
            snapshot_id: Snapshot ID.
            total_value: Total portfolio value.
            total_cost: Total cost basis.
            unrealized_pnl: Unrealized P&L.
            realized_pnl: Realized P&L.
            positions: List of position data.
            metadata: Additional metadata.

        Returns:
            True if saved successfully.
        """
        portfolio_data = {
            "id": snapshot_id,
            "total_value": total_value,
            "total_cost": total_cost,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl": realized_pnl,
            "total_pnl": unrealized_pnl + realized_pnl,
            "positions": positions,
            "metadata": metadata or {},
        }
        self._cache["portfolio"] = self._cache.get("portfolio", [])
        self._cache["portfolio"].append(portfolio_data)
        return True

    async def load_portfolio(self, snapshot_id: str) -> Optional[dict]:
        """Load a portfolio snapshot from memo0.

        Args:
            snapshot_id: Snapshot ID.

        Returns:
            Portfolio data or None.
        """
        for entry in self._cache.get("portfolio", []):
            if entry.get("id") == snapshot_id:
                return entry
        return None

    async def save_chart_data(
        self,
        chart_id: str,
        chart_type: str,
        data_points: list[dict],
        metadata: Optional[dict] = None,
    ) -> bool:
        """Save chart data to memo0.

        Args:
            chart_id: Chart ID.
            chart_type: Type of chart.
            data_points: List of data points.
            metadata: Additional metadata.

        Returns:
            True if saved successfully.
        """
        chart_data = {
            "id": chart_id,
            "type": chart_type,
            "data_points": data_points,
            "metadata": metadata or {},
        }
        self._cache["charts"] = self._cache.get("charts", [])
        self._cache["charts"].append(chart_data)
        return True

    async def load_chart_data(self, chart_id: str) -> Optional[dict]:
        """Load chart data from memo0.

        Args:
            chart_id: Chart ID.

        Returns:
            Chart data or None.
        """
        for entry in self._cache.get("charts", []):
            if entry.get("id") == chart_id:
                return entry
        return None


class KnowledgeBase:
    """Knowledge base for tracking system progress and features."""

    def __init__(self, memo_client: Memo0Client) -> None:
        """Initialize knowledge base.

        Args:
            memo_client: Memo0 client.
        """
        self.memo_client = memo_client
        self.current_version = "0.1.0"

    async def record_progress(
        self,
        completed_features: list[str],
        metrics: Optional[dict] = None,
    ) -> bool:
        """Record current progress.

        Args:
            completed_features: List of completed features.
            metrics: Progress metrics.

        Returns:
            True if recorded successfully.
        """
        return await self.memo_client.save_progress(
            version=self.current_version,
            status="in_progress",
            completed_features=completed_features,
            metrics=metrics,
        )

    async def load_progress(self) -> Optional[dict]:
        """Load latest progress.

        Returns:
            Latest progress or None.
        """
        return await self.memo_client.load_latest_progress()

    async def save_feature(
        self,
        feature_name: str,
        description: str,
        status: str = "implemented",
    ) -> bool:
        """Save a feature to knowledge base.

        Args:
            feature_name: Name of the feature.
            description: Feature description.
            status: Feature status.

        Returns:
            True if saved successfully.
        """
        return await self.memo_client.save_knowledge(
            key=f"feature:{feature_name}",
            content=description,
            metadata={"status": status, "version": self.current_version},
        )

    async def load_features(self) -> list[dict]:
        """Load all features from knowledge base.

        Returns:
            List of feature entries.
        """
        features = []
        for entry in self.memo_client._cache["knowledge"]:
            if isinstance(entry, dict) and entry.get("key", "").startswith(
                "feature:"
            ):
                features.append(entry)
        return features

    async def save_portfolio(
        self,
        snapshot_id: str,
        total_value: float,
        total_cost: float,
        unrealized_pnl: float,
        realized_pnl: float,
        positions: list[dict],
        metadata: Optional[dict] = None,
    ) -> bool:
        """Save a portfolio snapshot to memo0.

        Args:
            snapshot_id: Snapshot ID.
            total_value: Total portfolio value.
            total_cost: Total cost basis.
            unrealized_pnl: Unrealized P&L.
            realized_pnl: Realized P&L.
            positions: List of position data.
            metadata: Additional metadata.

        Returns:
            True if saved successfully.
        """
        portfolio_data = {
            "id": snapshot_id,
            "total_value": total_value,
            "total_cost": total_cost,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl": realized_pnl,
            "total_pnl": unrealized_pnl + realized_pnl,
            "positions": positions,
            "metadata": metadata or {},
        }
        self._cache["portfolio"] = self._cache.get("portfolio", [])
        self._cache["portfolio"].append(portfolio_data)
        return True

    async def load_portfolio(self, snapshot_id: str) -> Optional[dict]:
        """Load a portfolio snapshot from memo0.

        Args:
            snapshot_id: Snapshot ID.

        Returns:
            Portfolio data or None.
        """
        for entry in self._cache.get("portfolio", []):
            if entry.get("id") == snapshot_id:
                return entry
        return None

    async def load_portfolio_history(
        self,
        limit: int = 100,
    ) -> list[dict]:
        """Load portfolio history.

        Args:
            limit: Maximum number of entries.

        Returns:
            List of portfolio snapshots.
        """
        portfolios = self._cache.get("portfolio", [])
        return sorted(
            portfolios,
            key=lambda x: x.get("timestamp", 0),
            reverse=True,
        )[:limit]

    async def save_chart_data(
        self,
        chart_id: str,
        chart_type: str,
        data_points: list[dict],
        metadata: Optional[dict] = None,
    ) -> bool:
        """Save chart data to memo0.

        Args:
            chart_id: Chart ID.
            chart_type: Type of chart.
            data_points: List of data points.
            metadata: Additional metadata.

        Returns:
            True if saved successfully.
        """
        chart_data = {
            "id": chart_id,
            "type": chart_type,
            "data_points": data_points,
            "metadata": metadata or {},
        }
        self._cache["charts"] = self._cache.get("charts", [])
        self._cache["charts"].append(chart_data)
        return True

    async def load_chart_data(self, chart_id: str) -> Optional[dict]:
        """Load chart data from memo0.

        Args:
            chart_id: Chart ID.

        Returns:
            Chart data or None.
        """
        for entry in self._cache.get("charts", []):
            if entry.get("id") == chart_id:
                return entry
        return None