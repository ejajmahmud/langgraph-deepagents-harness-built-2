"""Market analysis engine for real-time price monitoring."""

import asyncio
from collections import defaultdict
from typing import Optional

import pandas as pd

from deepagents_crypto_trading.exchange_connector import (
    CircuitBreaker,
    Exchange,
    ExchangeConnector,
    ExchangeConnectorManager,
    MockConnector,
)
from deepagents_crypto_trading.types import (
    ArbitrageOpportunity,
    ArbitrageType,
    MarketData,
    Price,
    TradingConfig,
    TradingPair,
)


class MarketAnalyzer:
    """Market analysis engine for detecting arbitrage opportunities.

    Monitors real-time prices across multiple exchanges and identifies
    profitable arbitrage opportunities based on price differentials.

    Attributes:
        config: Trading configuration.
        latest_data: Latest market data snapshot.
        price_history: Historical price data for analysis.
    """

    def __init__(self, config: TradingConfig) -> None:
        """Initialize the market analyzer.

        Args:
            config: Trading system configuration.
        """
        self.config = config
        self.latest_data: Optional[MarketData] = None
        self.price_history: dict[str, pd.DataFrame] = defaultdict(
            lambda: pd.DataFrame(
                columns=["price", "volume", "timestamp", "exchange"]
            )
        )
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        # Use exchange connector manager for real API data
        self._connector_manager = ExchangeConnectorManager()
        self._exchange_status: dict[str, bool] = {}

    async def start(self) -> None:
        """Start the market analyzer."""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop(self) -> None:
        """Stop the market analyzer."""
        self._running = False
        if self._monitor_task:
            await self._monitor_task

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                await self._fetch_market_data()
                await asyncio.sleep(self.config.check_interval_seconds)
            except Exception:
                # Continue monitoring on errors
                await asyncio.sleep(self.config.check_interval_seconds)

    async def _fetch_market_data(self) -> None:
        """Fetch current market data from all enabled exchanges."""
        prices: dict[str, Price] = {}
        volatility: dict[str, float] = {}

        # Fetch from each enabled exchange
        for exchange in self.config.enabled_exchanges:
            exchange_prices = await self._fetch_exchange_prices(exchange)
            for symbol, price_data in exchange_prices.items():
                key = f"{exchange.value}:{symbol}"
                prices[key] = price_data
                # Update history
                self._update_price_history(key, price_data)
                # Calculate volatility
                volatility[key] = self._calculate_volatility(key)

        self.latest_data = MarketData(
            prices=prices,
            timestamp=pd.Timestamp.now(),
            volatility=volatility,
        )

    async def _fetch_exchange_prices(
        self, exchange: Exchange
    ) -> dict[str, Price]:
        """Fetch prices from a specific exchange.

        Uses real exchange APIs when available, falls back to mock data.

        Args:
            exchange: The exchange to fetch from.

        Returns:
            Dictionary of symbol to Price.
        """
        base_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT"]

        # Check exchange availability
        is_available = await self._connector_manager.check_exchange_available(
            exchange
        )
        self._exchange_status[exchange.value] = is_available

        # Try real API first, fallback to mock
        if is_available:
            try:
                prices = await self._connector_manager.fetch_prices(
                    exchange, base_symbols
                )
                if prices:
                    return prices
            except Exception:
                pass

        # Fallback to mock connector
        connector = self._connector_manager.get_connector(exchange)
        if not connector:
            connector = MockConnector(exchange)

        return await connector.fetch_prices(base_symbols)

    def _update_price_history(self, key: str, price: Price) -> None:
        """Update price history for a symbol."""
        df = self.price_history[key]
        new_row = pd.DataFrame(
            {
                "price": [price.price],
                "volume": [price.volume_24h],
                "timestamp": [price.timestamp],
                "exchange": [price.exchange.value],
            }
        )
        self.price_history[key] = pd.concat([df, new_row], ignore_index=True)
        # Keep last 1000 data points
        if len(self.price_history[key]) > 1000:
            self.price_history[key] = self.price_history[key].tail(1000)

    def _calculate_volatility(self, key: str) -> float:
        """Calculate price volatility (standard deviation of returns)."""
        df = self.price_history[key]
        if len(df) < 2:
            return 0.0
        returns = df["price"].pct_change().dropna()
        if len(returns) == 0:
            return 0.0
        return float(returns.std())

    def detect_opportunities(
        self, min_profit_pct: float = 0.005, min_confidence: float = 0.7
    ) -> list[ArbitrageOpportunity]:
        """Detect arbitrage opportunities in current market data.

        Args:
            min_profit_pct: Minimum profit percentage to consider.
            min_confidence: Minimum confidence level.

        Returns:
            List of detected arbitrage opportunities.
        """
        if not self.latest_data:
            return []

        opportunities: list[ArbitrageOpportunity] = []

        # Check triangular arbitrage
        if ArbitrageType.TRIANGULAR in self.config.enabled_strategies:
            triangular = self._detect_triangular_arbitrage(
                min_profit_pct, min_confidence
            )
            opportunities.extend(triangular)

        # Check cross-exchange arbitrage
        if ArbitrageType.CROSS_EXCHANGE in self.config.enabled_strategies:
            cross = self._detect_cross_exchange_arbitrage(
                min_profit_pct, min_confidence
            )
            opportunities.extend(cross)

        return opportunities

    def _detect_triangular_arbitrage(
        self, min_profit_pct: float, min_confidence: float
    ) -> list[ArbitrageOpportunity]:
        """Detect triangular arbitrage opportunities.

        Triangular arbitrage exploits price differences between three pairs
        on the same exchange (e.g., USDT->BTC->ETH->USDT).
        """
        opportunities: list[ArbitrageOpportunity] = []

        # Only check first enabled exchange for triangular
        if not self.config.enabled_exchanges:
            return []

        exchange = self.config.enabled_exchanges[0]

        # Check common triangular paths
        paths = [
            (("BTC", "USDT"), ("BTC", "ETH"), ("ETH", "USDT")),
            (("ETH", "USDT"), ("ETH", "BTC"), ("BTC", "USDT")),
            (("SOL", "USDT"), ("SOL", "ETH"), ("ETH", "USDT")),
        ]

        for path in paths:
            opp = self._analyze_triangular_path(
                exchange, path, min_profit_pct, min_confidence
            )
            if opp:
                opportunities.append(opp)

        return opportunities

    def _analyze_triangular_path(
        self,
        exchange: Exchange,
        path: tuple[tuple[str, str], tuple[str, str], tuple[str, str]],
        min_profit_pct: float,
        min_confidence: float,
    ) -> Optional[ArbitrageOpportunity]:
        """Analyze a specific triangular arbitrage path.

        Args:
            exchange: Exchange to check.
            path: (pair1, pair2, pair3) tuples of (base, quote).
            min_profit_pct: Minimum profit threshold.
            min_confidence: Minimum confidence.

        Returns:
            Arbitrage opportunity if found, None otherwise.
        """
        if not self.latest_data:
            return None

        # Get prices for each pair
        pairs = [
            TradingPair(base=p[0], quote=p[1], exchange=exchange)
            for p in path
        ]

        try:
            prices = []
            for pair in pairs:
                key = f"{exchange.value}:{pair.symbol}"
                price_obj = self.latest_data.prices.get(key)
                if not price_obj:
                    return None
                prices.append(price_obj.price)
        except (KeyError, TypeError):
            return None

        # Calculate triangular arbitrage profit correctly
        # Path: A/B -> B/C -> C/A
        # Example: USDT/BTC -> BTC/ETH -> ETH/USDT
        # Start with 1 USDT:
        # 1 USDT / price_of_USDT_BTC = BTC_amount
        # BTC_amount * price_of_BTC_ETH = ETH_amount
        # ETH_amount * price_of_ETH_USDT = final_USDT
        p1, p2, p3 = prices

        # Correct triangular arbitrage formula:
        # Start with 1 unit of quote, buy first base, sell for second base, sell for quote
        try:
            amount1 = 1.0 / p1  # 1 USDT -> BTC (using USDT/BTC rate)
            amount2 = amount1 * p2  # BTC -> ETH (using BTC/ETH rate)
            amount3 = amount2 * p3  # ETH -> USDT (using ETH/USDT rate)
            profit_pct = (amount3 - 1.0) * 100
        except (ZeroDivisionError, TypeError):
            return None

        if profit_pct < min_profit_pct * 100:
            return None

        # Risk assessment
        volatility = self._get_avg_volatility(pairs)
        risk_level = min(1.0, volatility * 10)  # Scale volatility to risk

        # Confidence based on liquidity and volatility
        confidence = self._calculate_confidence(pairs, volatility)

        if confidence < min_confidence:
            return None

        return ArbitrageOpportunity(
            arbitrage_type=ArbitrageType.TRIANGULAR,
            trading_pairs=pairs,
            expected_profit_pct=profit_pct,
            required_capital=1000.0 / profit_pct if profit_pct > 0 else 10000,
            estimated_duration_seconds=30,
            risk_level=risk_level,
            confidence=confidence,
            exchanges=[exchange],
        )

    def _detect_cross_exchange_arbitrage(
        self, min_profit_pct: float, min_confidence: float
    ) -> list[ArbitrageOpportunity]:
        """Detect cross-exchange arbitrage opportunities."""
        opportunities: list[ArbitrageOpportunity] = []

        if not self.latest_data or len(self.config.enabled_exchanges) < 2:
            return opportunities

        # Check each symbol across exchanges
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

        for symbol in symbols:
            # Get prices from different exchanges
            prices_by_exchange: dict[Exchange, float] = {}
            for exchange in self.config.enabled_exchanges:
                key = f"{exchange.value}:{symbol}"
                price_obj = self.latest_data.prices.get(key)
                if price_obj:
                    prices_by_exchange[exchange] = price_obj.price

            if len(prices_by_exchange) < 2:
                continue

            # Find max price difference
            max_exchange = max(
                prices_by_exchange, key=prices_by_exchange.get  # type: ignore
            )
            min_exchange = min(
                prices_by_exchange, key=prices_by_exchange.get  # type: ignore
            )

            max_price = prices_by_exchange[max_exchange]
            min_price = prices_by_exchange[min_exchange]

            profit_pct = ((max_price - min_price) / min_price) * 100

            if profit_pct < min_profit_pct * 100:
                continue

            # Calculate risk and confidence
            pairs = [
                TradingPair(
                    base=symbol.replace("USDT", ""), quote="USDT", exchange=max_exchange
                ),
                TradingPair(
                    base=symbol.replace("USDT", ""), quote="USDT", exchange=min_exchange
                ),
            ]
            volatility = self._get_avg_volatility(pairs)
            risk_level = min(1.0, volatility * 10)
            confidence = self._calculate_confidence(pairs, volatility)

            if confidence < min_confidence:
                continue

            opportunities.append(
                ArbitrageOpportunity(
                    arbitrage_type=ArbitrageType.CROSS_EXCHANGE,
                    trading_pairs=pairs,
                    expected_profit_pct=profit_pct,
                    required_capital=1000.0 / profit_pct if profit_pct > 0 else 10000,
                    estimated_duration_seconds=60,
                    risk_level=risk_level,
                    confidence=confidence,
                    exchanges=[max_exchange, min_exchange],
                )
            )

        return opportunities

    def _get_avg_volatility(self, pairs: list[TradingPair]) -> float:
        """Get average volatility for trading pairs."""
        if not self.latest_data:
            return 0.0

        volatilities = []
        for pair in pairs:
            key = f"{pair.exchange.value}:{pair.symbol}"
            vol = self.latest_data.volatility.get(key, 0.0)
            if vol > 0:
                volatilities.append(vol)

        return sum(volatilities) / len(volatilities) if volatilities else 0.0

    def _calculate_confidence(
        self, pairs: list[TradingPair], volatility: float
    ) -> float:
        """Calculate confidence score for an opportunity.

        Based on liquidity and market stability.
        """
        if not self.latest_data:
            return 0.0

        # Higher volatility = lower confidence
        vol_score = max(0.0, 1.0 - volatility * 10)

        # Check liquidity (volume)
        volume_scores = []
        for pair in pairs:
            key = f"{pair.exchange.value}:{pair.symbol}"
            price = self.latest_data.prices.get(key)
            if price and price.volume_24h > 1_000_000:
                volume_scores.append(1.0)
            elif price and price.volume_24h > 100000:
                volume_scores.append(0.7)
            else:
                volume_scores.append(0.3)

        vol_score = sum(volume_scores) / len(volume_scores) if volume_scores else 0.0

        return (vol_score + vol_score) / 2

    def get_market_summary(self) -> dict:
        """Get market data summary."""
        if not self.latest_data:
            return {}

        summary = {
            "timestamp": str(self.latest_data.timestamp),
            "symbols": len(self.latest_data.prices),
            "exchanges": len(self.config.enabled_exchanges),
            "exchange_status": self._exchange_status,
        }

        return summary