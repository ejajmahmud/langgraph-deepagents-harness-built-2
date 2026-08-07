"""DeepAgents Crypto Trading System.

A low-risk cryptocurrency arbitrage trading system built on the Deep Agents framework.

Features:
- Market Analysis Engine - Real-time price monitoring
- Arbitrage Detection - Multiple arbitrage strategies
- Risk Management - Position sizing, stop-loss, exposure controls
- Memo0 Integration - Persistent storage and knowledge base
- Exchange Connectors - Real exchange API integration (Binance, Coinbase)
- WebSocket Connector - Real-time streaming price data
- Real-time Signals - Low-latency signal generation
- Circuit Breaker - API resilience pattern
- Order Management - Order lifecycle management (V58.0)
- Portfolio Manager - Investment portfolio management (V59.0)
- Charts Visualization - Price/P&L charts (V59.0)
- Real Trading Execution - Exchange API integration (V60.0)
- Backtesting Engine - Historical backtesting (V60.0)
- Multi-Timeframe Analysis - Cross-timeframe signals (V60.0)
- Advanced Risk Analytics - VaR/Stress testing (V60.0)
- Dashboard Integration - Real-time dashboard data
- Low Risk Arbitrage - V61.0 Enhanced low-risk strategies
- API Key Management - Secure API key storage (V61.0)
- Trade History Persistence - Historical trade storage (V61.0)
- Adaptive Learning - Self-optimizing strategies (V61.0)
- Grid Trading Strategy - Grid-based arbitrage (V62.0)
- Perpetual Futures Arbitrage - Funding rate arbitrage (V63.0)
- Multi-Exchange Gateway - Unified exchange API (V64.0)
"""

from typing import Optional

from deepagents_crypto_trading.arbitrage_engine import (
    ArbitrageEngine,
    CrossExchangeArbitrage,
    TriangularArbitrage,
)
from deepagents_crypto_trading.advanced_risk import (
    VaRCalculator,
    VaRMethod,
    VaRResult,
    RiskScenario,
    RiskReport,
    StressTester,
    StressResult,
    AdvancedRiskAnalytics,
    CorrelationAnalyzer,
)
from deepagents_crypto_trading.backtest_engine import (
    BacktestEngine,
    BacktestConfig,
    BacktestResult,
    BacktestStats,
    BacktestReport,
    PerformanceAnalyzer,
)
from deepagents_crypto_trading.charts import (
    ChartConfig,
    ChartDataPoint,
    ChartSeries,
    ChartTimeframe,
    ChartType,
    PnLChart,
    PriceChart,
)
from deepagents_crypto_trading.exchange_connector import (
    BinanceConnector,
    CircuitBreaker,
    CoinbaseConnector,
    ExchangeConnector,
    ExchangeConnectorManager,
    MockConnector,
)
from deepagents_crypto_trading.execution import (
    ExecutionEngine,
    ExecutionStrategy,
    ExchangeAPI,
    BinanceAPI,
    CoinbaseAPI,
    OrderExecutor,
    FeeCalculator,
    OrderResponse,
    OrderResponseStatus,
    Balance,
    Position,
)
from deepagents_crypto_trading.market_analyzer import MarketAnalyzer
from deepagents_crypto_trading.memo_client import KnowledgeBase, Memo0Client
from deepagents_crypto_trading.order_manager import (
    OrderManager,
    OrderExecutionSimulator,
    OrderStatus,
    OrderTimeInForce,
)
from deepagents_crypto_trading.portfolio_manager import (
    PortfolioAllocation,
    PortfolioConfig,
    PortfolioManager,
    PortfolioMetric,
    PortfolioPosition,
    PortfolioSnapshot,
    RebalanceStrategy,
)
from deepagents_crypto_trading.risk_manager import RiskManager
from deepagents_crypto_trading.real_time_signals import (
    RealTimeSignalGenerator,
    SignalAggregator,
    SignalFilter,
)
from deepagents_crypto_trading.types import (
    ArbitrageOpportunity,
    ArbitrageSignal,
    ArbitrageType,
    Exchange,
    MarketData,
    OrderSide,
    OrderType,
    Position,
    PositionStatus,
    Price,
    RiskConfig,
    SignalStatus,
    TradingConfig,
    TradingPair,
)
from deepagents_crypto_trading.timeframe import (
    Timeframe,
    TimeframeData,
    MultiTimeframeConfig,
    CrossTimeframeSignal,
    TimeframeAnalyzer,
    MultiTimeframeManager,
)
from deepagents_crypto_trading.low_risk_arbitrage import (
    APIKeyManager,
    TradeHistoryManager,
    LowRiskArbitrageScanner,
    AdaptiveLearningEngine,
    AdvancedOrder,
    TradeRecord,
    ArbitragePosition,
    LowRiskSignal,
    LiveTradingMode,
    AdvancedOrderType,
    OrderTimeInForce,
    get_api_key_manager,
    get_trade_history_manager,
    get_arbitrage_scanner,
)
from deepagents_crypto_trading.grid_trading import (
    GridTradingEngine,
    GridConfig,
    GridLevel,
    GridOrder,
    GridState,
    GridOrderSide,
    GridStatistics,
    get_grid_engine,
)
from deepagents_crypto_trading.perpetual_arbitrage import (
    PerpetualArbitrageEngine,
    PerpetualConfig,
    PerpetualSignal,
    FundingRateData,
    PerpetualSide,
    FundingRateDirection,
    get_perpetual_engine,
    create_funding_rate_data,
)
from deepagents_crypto_trading.multi_exchange_gateway import (
    MultiExchangeGateway,
    GatewayConfig,
    ExchangeConnection,
    ExchangeHealth,
    ConnectionState,
    UnifiedPriceResponse,
    get_gateway,
    create_gateway_config,
)
from deepagents_crypto_trading.websocket_connector import (
    BinanceWebSocketConnector,
    CoinbaseWebSocketConnector,
    WebSocketConnector,
    WebSocketManager,
)

__version__ = "1.0.0"

__all__ = [
    # Core
    "CryptoTradingSystem",
    "MarketAnalyzer",
    "ArbitrageEngine",
    "RiskManager",
    "Memo0Client",
    "KnowledgeBase",
    # Exchange Connectors
    "ExchangeConnector",
    "BinanceConnector",
    "CoinbaseConnector",
    "MockConnector",
    "ExchangeConnectorManager",
    "CircuitBreaker",
    # Execution (V60.0 new)
    "ExecutionEngine",
    "ExecutionStrategy",
    "ExchangeAPI",
    "BinanceAPI",
    "CoinbaseAPI",
    "OrderExecutor",
    "FeeCalculator",
    "OrderResponse",
    "OrderResponseStatus",
    "Balance",
    "Position",
    # WebSocket (V57.0 new)
    "WebSocketConnector",
    "BinanceWebSocketConnector",
    "CoinbaseWebSocketConnector",
    "WebSocketManager",
    # Real-time Signals (V57.0 new)
    "RealTimeSignalGenerator",
    "SignalAggregator",
    "SignalFilter",
    # Order Management (V58.0 new)
    "OrderManager",
    "OrderExecutionSimulator",
    "OrderStatus",
    "OrderTimeInForce",
    # Portfolio Management (V59.0 new)
    "PortfolioManager",
    "PortfolioPosition",
    "PortfolioAllocation",
    "PortfolioSnapshot",
    "PortfolioConfig",
    "RebalanceStrategy",
    # Charts (V59.0 new)
    "PriceChart",
    "PnLChart",
    "ChartConfig",
    "ChartDataPoint",
    "ChartType",
    "ChartTimeframe",
    # Backtest (V60.0 new)
    "BacktestEngine",
    "BacktestConfig",
    "BacktestResult",
    "BacktestStats",
    "BacktestReport",
    "PerformanceAnalyzer",
    # Timeframe (V60.0 new)
    "Timeframe",
    "TimeframeData",
    "MultiTimeframeConfig",
    "CrossTimeframeSignal",
    "TimeframeAnalyzer",
    "MultiTimeframeManager",
    # Advanced Risk (V60.0 new)
    "VaRCalculator",
    "VaRMethod",
    "VaRResult",
    "RiskScenario",
    "RiskReport",
    "StressTester",
    "StressResult",
    "AdvancedRiskAnalytics",
    "CorrelationAnalyzer",
    # Types
    "ArbitrageOpportunity",
    "ArbitrageSignal",
    "ArbitrageType",
    "Exchange",
    "MarketData",
    "OrderSide",
    "OrderType",
    "Position",
    "PositionStatus",
    "Price",
    "RiskConfig",
    "SignalStatus",
    "TradingConfig",
    "TradingPair",
    # Strategies
    "TriangularArbitrage",
    "CrossExchangeArbitrage",
    # Low Risk Arbitrage (V61.0 new)
    "APIKeyManager",
    "TradeHistoryManager",
    "LowRiskArbitrageScanner",
    "AdaptiveLearningEngine",
    "AdvancedOrder",
    "TradeRecord",
    "ArbitragePosition",
    "LowRiskSignal",
    "LiveTradingMode",
    "AdvancedOrderType",
    "OrderTimeInForce",
    # Grid Trading (V62.0 new)
    "GridTradingEngine",
    "GridConfig",
    "GridLevel",
    "GridOrder",
    "GridState",
    "GridOrderSide",
    "GridStatistics",
    "get_grid_engine",
    # Perpetual Arbitrage (V63.0 new)
    "PerpetualArbitrageEngine",
    "PerpetualConfig",
    "PerpetualSignal",
    "FundingRateData",
    "PerpetualSide",
    "FundingRateDirection",
    "get_perpetual_engine",
    "create_funding_rate_data",
    # Multi-Exchange Gateway (V64.0 new)
    "MultiExchangeGateway",
    "GatewayConfig",
    "ExchangeConnection",
    "ExchangeHealth",
    "ConnectionState",
    "UnifiedPriceResponse",
    "get_gateway",
    "create_gateway_config",
]


class CryptoTradingSystem:
    """Main crypto trading system.

    Coordinates all components for low-risk arbitrage trading.
    """

    def __init__(self, config: Optional[TradingConfig] = None) -> None:
        """Initialize the trading system.

        Args:
            config: Trading configuration. Uses defaults if not provided.
        """
        self.config = config or TradingConfig()
        self.market_analyzer = MarketAnalyzer(self.config)
        self.arbitrage_engine = ArbitrageEngine(self.config)
        self.risk_manager = RiskManager(self.config)
        self.memo_client = Memo0Client(self.config)
        self.knowledge_base = KnowledgeBase(self.memo_client)
        self.order_manager = OrderManager()
        self.portfolio_manager = PortfolioManager()
        self.pnl_chart = PnLChart()
        self._running = False

    async def initialize(self) -> None:
        """Initialize the trading system."""
        await self.market_analyzer.start()
        self._running = True

    async def shutdown(self) -> None:
        """Shutdown the trading system."""
        await self.market_analyzer.stop()
        self._running = False

    async def execute_cycle(self) -> list[ArbitrageOpportunity]:
        """Execute one trading cycle.

        Returns:
            List of detected opportunities.
        """
        if not self._running:
            return []

        # Get opportunities
        opportunities = self.market_analyzer.detect_opportunities()

        # Filter by risk
        open_positions = self.arbitrage_engine.get_open_positions()
        valid_opportunities = []

        for opp in opportunities:
            if self.risk_manager.check_opportunity(opp, open_positions):
                valid_opportunities.append(opp)

        return valid_opportunities

    async def execute_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
    ) -> Optional[str]:
        """Execute a trading order.

        Args:
            symbol: Trading symbol.
            side: Order side (buy/sell).
            quantity: Order quantity.
            order_type: Order type (market/limit).
            price: Limit price (for limit orders).

        Returns:
            Order ID if created.
        """
        if order_type == "market":
            order = self.order_manager.create_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
            )
        else:
            order = self.order_manager.create_limit_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price or 0.0,
            )

        # Save to memo0
        await self.memo_client.save_order(
            order_id=order.id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status=order.status.value,
        )

        return order.id

    def get_status(self) -> dict:
        """Get system status.

        Returns:
            Dictionary of system status.
        """
        return {
            "version": __version__,
            "running": self._running,
            "memo_enabled": self.memo_client.is_enabled(),
            "positions": self.arbitrage_engine.get_positions_summary(),
            "orders": self.order_manager.get_order_statistics(),
            "portfolio": self.portfolio_manager.get_positions_summary(),
            "pnl_chart": self.pnl_chart.get_chart_data(),
            "risk": self.risk_manager.get_risk_metrics(),
            "market": self.market_analyzer.get_market_summary(),
            "memo": self.memo_client.get_stats(),
        }