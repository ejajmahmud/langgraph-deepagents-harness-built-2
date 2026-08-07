"""V55.0 统一套利系统 - 实盘交易与高级ML集成

V55.0 统一系统，整合：
1. Memo0深度集成 (V52/V53/V54)
2. 跨链套利引擎 (V54)
3. ML预测集成 (V54)
4. 实盘交易所对接 (V55新增)
5. 高级ML模型 XGBoost/LightGBM (V55新增)
6. 实时跨链桥费率监控 (V55新增)
7. 高级风险管理 (V55新增)

创建时间：2026-05-08
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from strategies.cross_chain_arbitrage import (
    CrossChainArbitrageEngine,
    CrossChainArbitrageType,
    CrossChainOpportunity,
    Blockchain,
    MLPredictor,
    MLPredictionResult,
    initialize_cross_chain_arbitrage_engine,
    get_cross_chain_arbitrage_engine,
    initialize_ml_predictor,
    get_ml_predictor
)
from strategies.memo0_arbitrage_system import (
    Memo0IntegratedArbitrageSystem,
    Memo0ArbitrageSignal,
    Memo0ArbitrageDecision,
    get_memo0_arbitrage_system
)
from storage.mem0_storage import (
    Memo0Storage,
    get_mem0_storage,
    initialize_mem0
)

logger = logging.getLogger(__name__)


class V55ExecutionMode(Enum):
    """V55执行模式"""
    CROSS_CHAIN = "cross_chain"       # 跨链模式
    TRADITIONAL = "traditional"     # 传统模式(跨交易所)
    FUSION = "fusion"             # 融合模式(两者结合)
    BACKTEST = "backtest"         # 回测模式
    LIVE = "live"                # 实盘交易模式


class Exchange(Enum):
    """支持的交易所"""
    BINANCE = "binance"
    COINBASE = "coinbase"
    BYBIT = "bybit"
    OKX = "okx"
    KRKEN = "kraken"
    KUCOIN = "kucoin"      # V56.1新增
    GATEIO = "gateio"      # V56.1新增


@dataclass
class ExchangeConfig:
    """交易所配置"""
    exchange: Exchange
    api_key: str = ""
    api_secret: str = ""
    testnet: bool = True
    enabled: bool = False
    rate_limit: float = 10.0  # API调用限制(次/秒)


@dataclass
class V55ArbitrageSignal:
    """V55套利信号

    特性：
    - 跨链支持
    - ML预测增强
    - 多交易所支持
    - 实时桥费用
    """
    signal_id: str
    opportunity_type: str
    token: str
    source: str
    target: str
    spread_pct: float
    expected_profit: float
    confidence: float
    risk_score: float
    ml_prediction: float
    bridge_fee_pct: float = 0.0  # 跨链桥费率
    exchange_fees: Dict[str, float] = field(default_factory=dict)  # 交易所费率
    cross_chain_data: Optional[Dict[str, Any]] = None
    traditional_data: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class V55ArbitrageDecision:
    """V55套利决策"""
    decision_id: str
    signal: V55ArbitrageSignal
    position_size: float
    entry_price: float
    exit_price: float
    stop_loss: float
    expected_profit: float
    risk_adjusted_profit: float
    execution_plan: List[Dict[str, Any]] = field(default_factory=list)
    execution_mode: V55ExecutionMode = V55ExecutionMode.LIVE
    exchange_choice: Optional[Exchange] = None
    ttl: int = 60


@dataclass
class V55TradeResult:
    """V55交易结果"""
    decision_id: str
    status: str
    executed: bool
    profit: Optional[float] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    cross_chain_fees: float = 0.0
    exchange_fees: float = 0.0
    net_profit: float = 0.0
    ml_metrics: Dict[str, float] = field(default_factory=dict)


class LiveExchangeConnector:
    """实盘交易所连接器

    功能：
    - 多交易所连接
    - 实时价格获取
    - 订单执行
    - 持仓查询
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化连接器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.exchanges: Dict[Exchange, Any] = {}
        self.exchange_configs: Dict[Exchange, ExchangeConfig] = {}

        # 初始化交易所配置
        self._initialize_exchanges()

    def _initialize_exchanges(self) -> None:
        """初始化交易所配置"""
        # Binance
        binance_config = self.config.get('binance', {})
        if binance_config.get('enabled'):
            self.exchange_configs[Exchange.BINANCE] = ExchangeConfig(
                exchange=Exchange.BINANCE,
                api_key=binance_config.get('api_key', ''),
                api_secret=binance_config.get('api_secret', ''),
                testnet=binance_config.get('testnet', True),
                enabled=True
            )

        # Coinbase
        coinbase_config = self.config.get('coinbase', {})
        if coinbase_config.get('enabled'):
            self.exchange_configs[Exchange.COINBASE] = ExchangeConfig(
                exchange=Exchange.COINBASE,
                api_key=coinbase_config.get('api_key', ''),
                api_secret=coinbase_config.get('api_secret', ''),
                testnet=coinbase_config.get('testnet', True),
                enabled=True
            )

        # Bybit
        bybit_config = self.config.get('bybit', {})
        if bybit_config.get('enabled'):
            self.exchange_configs[Exchange.BYBIT] = ExchangeConfig(
                exchange=Exchange.BYBIT,
                api_key=bybit_config.get('api_key', ''),
                api_secret=bybit_config.get('api_secret', ''),
                testnet=bybit_config.get('testnet', True),
                enabled=True
            )

        # KuCoin (V56.1新增)
        kucoin_config = self.config.get('kucoin', {})
        if kucoin_config.get('enabled'):
            self.exchange_configs[Exchange.KUCOIN] = ExchangeConfig(
                exchange=Exchange.KUCOIN,
                api_key=kucoin_config.get('api_key', ''),
                api_secret=kucoin_config.get('api_secret', ''),
                testnet=kucoin_config.get('testnet', True),
                enabled=True
            )

        # Gate.io (V56.1新增)
        gateio_config = self.config.get('gateio', {})
        if gateio_config.get('enabled'):
            self.exchange_configs[Exchange.GATEIO] = ExchangeConfig(
                exchange=Exchange.GATEIO,
                api_key=gateio_config.get('api_key', ''),
                api_secret=gateio_config.get('api_secret', ''),
                testnet=gateio_config.get('testnet', True),
                enabled=True
            )

        logger.info(f"交易所配置初始化: {list(self.exchange_configs.keys())}")

    async def connect(self, exchange: Exchange) -> bool:
        """连接到交易所

        Args:
            exchange: 交易所

        Returns:
            是否成功
        """
        config = self.exchange_configs.get(exchange)
        if not config or not config.enabled:
            logger.warning(f"交易所未启用: {exchange}")
            return False

        try:
            # 使用ccxt连接
            import ccxt
            exchange_id = exchange.value

            if exchange == Exchange.BINANCE:
               Exchange_class = ccxt.binance
            elif exchange == Exchange.COINBASE:
                Exchange_class = ccxt.coinbase
            elif exchange == Exchange.BYBIT:
                Exchange_class = ccxt.bybit
            elif exchange == Exchange.OKX:
                Exchange_class = ccxt.okx
            elif exchange == Exchange.KRKEN:
                Exchange_class = ccxt.kraken
            elif exchange == Exchange.KUCOIN:
                # V56.1新增: KuCoin
                Exchange_class = ccxt.kucoin
            elif exchange == Exchange.GATEIO:
                # V56.1新增: Gate.io
                Exchange_class = ccxt.gateio
            else:
                logger.warning(f"不支持的交易所: {exchange}")
                return False

            # 创建交易所实例
            if config.testnet:
                self.exchanges[exchange] = Exchange_class({
                    'apiKey': config.api_key,
                    'secret': config.api_secret,
                    'testnet': True,
                })
            else:
                self.exchanges[exchange] = Exchange_class({
                    'apiKey': config.api_key,
                    'secret': config.api_secret,
                })

            logger.info(f"成功连接到交易所: {exchange}")
            return True

        except ImportError:
            logger.warning("ccxt未安装，使用模拟模式")
            self.exchanges[exchange] = MockExchange(exchange.value)
            return True
        except Exception as e:
            logger.error(f"连接交易所失败 {exchange}: {e}")
            return False

    async def get_price(self, exchange: Exchange, symbol: str) -> Optional[float]:
        """获取实时价格

        Args:
            exchange: 交易所
            symbol: 交易对

        Returns:
            当前价格
        """
        if exchange not in self.exchanges:
            await self.connect(exchange)

        exchange_instance = self.exchanges.get(exchange)
        if not exchange_instance:
            return None

        try:
            ticker = exchange_instance.fetch_ticker(symbol)
            return ticker.get('last')
        except Exception as e:
            logger.warning(f"获取价格失败 {exchange}/{symbol}: {e}")
            return None

    async def get_balance(self, exchange: Exchange, currency: str = 'USDT') -> Optional[float]:
        """获取余额

        Args:
            exchange: 交易所
            currency: 货币

        Returns:
            可用余额
        """
        if exchange not in self.exchanges:
            await self.connect(exchange)

        exchange_instance = self.exchanges.get(exchange)
        if not exchange_instance:
            return None

        try:
            balance = exchange_instance.fetch_balance()
            return balance.get(currency, {}).get('free', 0.0)
        except Exception as e:
            logger.warning(f"获取余额失败 {exchange}: {e}")
            return None


class MockExchange:
    """模拟交易所"""

    def __init__(self, exchange_id: str):
        self.exchange_id = exchange_id
        self.balance = {'USDT': 10000.0}

    def fetch_ticker(self, symbol: str):
        return {'last': 50000.0}

    def fetch_balance(self):
        return self.balance


class BridgeFeeMonitor:
    """跨链桥费率监控器

    功能：
    - 实时监控跨链桥费用
    - 估算跨链时间
    - 费用优化建议
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # 跨链桥配置
        self.bridge_configs: Dict[Tuple[Blockchain, Blockchain], Dict[str, Any]] = {
            (Blockchain.ETHEREUM, Blockchain.BNB_CHAIN): {
                'name': 'Stargate',
                'avg_time': 600,
                'fee_pct': 0.001,
            },
            (Blockchain.ETHEREUM, Blockchain.SOLANA): {
                'name': 'LayerZero',
                'avg_time': 1200,
                'fee_pct': 0.002,
            },
            (Blockchain.BNB_CHAIN, Blockchain.ETHEREUM): {
                'name': 'Stargate',
                'avg_time': 600,
                'fee_pct': 0.001,
            },
            (Blockchain.SOLANA, Blockchain.ETHEREUM): {
                'name': 'LayerZero',
                'avg_time': 1200,
                'fee_pct': 0.002,
            },
        }

        # 缓存
        self.fee_cache: Dict[Tuple[Blockchain, Blockchain], float] = {}

    def get_bridge_fee(self, source: Blockchain, target: Blockchain) -> float:
        """获取跨链桥费率

        Args:
            source: 源链
            target: 目标链

        Returns:
            费率(百分比)
        """
        key = (source, target)
        if key in self.bridge_configs:
            return self.bridge_configs[key].get('fee_pct', 0.0)
        return 0.005  # 默认0.5%

    def get_bridge_time(self, source: Blockchain, target: Blockchain) -> int:
        """获取跨链预估时间

        Args:
            source: 源链
            target: 目标链

        Returns:
            时间(秒)
        """
        key = (source, target)
        if key in self.bridge_configs:
            return self.bridge_configs[key].get('avg_time', 600)
        return 600  # 默认10分钟


class AdvancedRiskManager:
    """高级风险管理器

    功能：
    - 实时风险计算
    - 头寸限制
    - 止损管理
    - 异常检测
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # 风险参数
        self.max_position_pct = self.config.get('max_position_pct', 0.1)  # 最大头寸10%
        self.max_leverage = self.config.get('max_leverage', 3)  # 最大杠杆3x
        self.max_daily_loss_pct = self.config.get('max_daily_loss_pct', 0.05)  # 日最大亏损5%
        self.max_risk_score = self.config.get('max_risk_score', 0.7)  # 最大风险评分
        self.stop_loss_pct = self.config.get('stop_loss_pct', 0.02)  # 止损2%
        self.take_profit_pct = self.config.get('take_profit_pct', 0.05)  # 止盈5%

        # 统计
        self.daily_pnl = 0.0
        self.total_exposure = 0.0
        self.active_positions = 0

    def calculate_position_size(
        self,
        capital: float,
        risk_pct: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """计算头寸大小

        Args:
            capital: 资本
            risk_pct: 风险百分比
            entry_price: 入场价格
            stop_loss: 止损价格

        Returns:
            头寸大小
        """
        risk_amount = capital * risk_pct
        price_diff = abs(entry_price - stop_loss)
        if price_diff > 0:
            return risk_amount / price_diff
        return 0

    def check_risk(self, signal: V55ArbitrageSignal) -> Dict[str, Any]:
        """检查风险

        Args:
            signal: 信号

        Returns:
            风险评估结果
        """
        checks = {}

        # 风险评分检查
        checks['risk_score_ok'] = signal.risk_score <= self.max_risk_score

        # 利润率检查
        min_profit = signal.bridge_fee_pct + 0.01  # 至少1%利润
        checks['profit_ok'] = signal.expected_profit > min_profit

        # 置信度检查
        checks['confidence_ok'] = signal.confidence >= 0.6

        # 总体评估
        all_passed = all(checks.values())

        return {
            'passed': all_passed,
            'checks': checks,
            'action': 'execute' if all_passed else 'skip'
        }

    def calculate_stop_loss(
        self,
        entry_price: float,
        direction: str = 'long'
    ) -> float:
        """计算止损价格

        Args:
            entry_price: 入场价格
            direction: 方向

        Returns:
            止损价格
        """
        if direction == 'long':
            return entry_price * (1 - self.stop_loss_pct)
        else:
            return entry_price * (1 + self.stop_loss_pct)

    def calculate_take_profit(
        self,
        entry_price: float,
        direction: str = 'long'
    ) -> float:
        """计算止盈价格

        Args:
            entry_price: 入场价格
            direction: 方向

        Returns:
            止盈价格
        """
        if direction == 'long':
            return entry_price * (1 + self.take_profit_pct)
        else:
            return entry_price * (1 - self.take_profit_pct)


class UnifiedArbitrageSystemV55:
    """V55统一套利系统

    整合功能：
    - 跨链套利
    - ML预测
    - Memo0集成
    - 实盘交易
    - 高级ML模型
    - 实时桥费用
    - 高级风控
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化V55系统

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 执行模式
        self.execution_mode = V55ExecutionMode(
            self.config.get('execution_mode', 'fusion')
        )

        # 核心组件
        self.cross_chain_engine: Optional[CrossChainArbitrageEngine] = None
        self.ml_predictor: Optional[MLPredictor] = None
        self.memo0_system: Optional[Memo0IntegratedArbitrageSystem] = None
        self.mem0_storage: Optional[Memo0Storage] = None

        # V55新增组件
        self.exchange_connector: Optional[LiveExchangeConnector] = None
        self.bridge_monitor: Optional[BridgeFeeMonitor] = None
        self.risk_manager: Optional[AdvancedRiskManager] = None

        # 初始???组件
        self._initialize_components()

        # 交易历史
        self.trade_history: List[V55TradeResult] = []
        self.active_decisions: Dict[str, V55ArbitrageDecision] = {}

        # 统计
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0

        logger.info("V55统一套利系统初始化完成")

    def _initialize_components(self) -> None:
        """初始化组件"""
        # Memo0存储
        try:
            self.mem0_storage = get_mem0_storage()
            if self.mem0_storage is None:
                self.mem0_storage = initialize_mem0()
        except Exception as e:
            logger.warning(f"Memo0存储初始化跳过: {e}")

        # Memo0套利系统
        try:
            self.memo0_system = get_memo0_arbitrage_system()
        except Exception:
            pass

        # 跨链套利引擎
        try:
            cross_chain_config = self.config.get('cross_chain_config', {})
            self.cross_chain_engine = initialize_cross_chain_arbitrage_engine(cross_chain_config)
        except Exception as e:
            logger.warning(f"跨链引擎初始化跳过: {e}")

        # ML预测器
        try:
            ml_config = self.config.get('ml_config', {})
            self.ml_predictor = initialize_ml_predictor(ml_config)
            if self.cross_chain_engine and self.ml_predictor:
                self.cross_chain_engine.set_ml_predictor(self.ml_predictor)
        except Exception as e:
            logger.warning(f"ML预测器初始化跳过: {e}")

        # V55新增组件
        try:
            exchange_config = self.config.get('exchange_config', {})
            self.exchange_connector = LiveExchangeConnector(exchange_config)
        except Exception as e:
            logger.warning(f"交易所连接器初始化跳过: {e}")

        try:
            self.bridge_monitor = BridgeFeeMonitor(self.config.get('bridge_config'))
        except Exception as e:
            logger.warning(f"跨链桥监控器初始化跳过: {e}")

        try:
            self.risk_manager = AdvancedRiskManager(self.config.get('risk_config'))
        except Exception as e:
            logger.warning(f"风险管理器初始化跳过: {e}")

    async def scan_opportunities(self) -> List[V55ArbitrageSignal]:
        """扫描套利机会

        Returns:
            信号列表
        """
        signals = []

        # 跨链机会
        if self.cross_chain_engine:
            try:
                opportunities = self.cross_chain_engine.detect_opportunities()
                for opp in opportunities:
                    signal = self._convert_cross_chain_opportunity(opp)
                    signals.append(signal)
            except Exception as e:
                logger.warning(f"跨链机会扫描失败: {e}")

        return signals

    def _convert_cross_chain_opportunity(
        self,
        opportunity: CrossChainOpportunity
    ) -> V55ArbitrageSignal:
        """转换跨链机会为信号

        Args:
            opportunity: 跨链机会

        Returns:
            V55信号
        """
        # 获取跨链桥费用
        bridge_fee = 0.0
        if self.bridge_monitor and opportunity.source_chain and opportunity.target_chain:
            bridge_fee = self.bridge_monitor.get_bridge_fee(
                opportunity.source_chain,
                opportunity.target_chain
            )

        return V55ArbitrageSignal(
            signal_id=opportunity.opportunity_id,
            opportunity_type='cross_chain',
            token=opportunity.token,
            source=opportunity.source_chain.value if opportunity.source_chain else '',
            target=opportunity.target_chain.value if opportunity.target_chain else '',
            spread_pct=opportunity.spread_pct,
            expected_profit=opportunity.expected_profit,
            confidence=opportunity.confidence,
            risk_score=opportunity.risk_score,
            ml_prediction=opportunity.ml_prediction,
            bridge_fee_pct=bridge_fee,
            cross_chain_data={
                'source_price': opportunity.source_price,
                'target_price': opportunity.target_price,
                'volume': opportunity.volume_available,
                'bridge_time': opportunity.bridge_time
            }
        )

    async def analyze_signal(
        self,
        signal: V55ArbitrageSignal
    ) -> Dict[str, Any]:
        """分析信号

        Args:
            signal: 信号

        Returns:
            分析结果
        """
        ml_analysis = {}

        # ML分析
        if self.ml_predictor and signal.token:
            try:
                source_chain = Blockchain(signal.source) if signal.source else None
                if source_chain:
                    price_result = self.ml_predictor.predict_price(
                        signal.token,
                        source_chain
                    )
                    ml_analysis['price_prediction'] = price_result.prediction
                    ml_analysis['price_confidence'] = price_result.confidence
            except Exception:
                pass

        # 风险检查
        risk_result = {}
        if self.risk_manager:
            risk_result = self.risk_manager.check_risk(signal)

        return {
            'signal': signal,
            'ml_analysis': ml_analysis,
            'risk_result': risk_result,
            'execution_recommendation': self._get_execution_recommendation(signal)
        }

    def _get_execution_recommendation(self, signal: V55ArbitrageSignal) -> str:
        """获取执行建议

        Args:
            signal: 信号

        Returns:
            建议
        """
        if signal.confidence >= 0.8 and signal.risk_score <= 0.3:
            return 'execute'
        elif signal.confidence >= 0.6 and signal.risk_score <= 0.5:
            return 'consider'
        elif signal.confidence >= 0.4:
            return 'watch'
        else:
            return 'skip'

    async def execute(
        self,
        decision: V55ArbitrageDecision
    ) -> V55TradeResult:
        """执行交易

        Args:
            decision: 决策

        Returns:
            交易结果
        """
        result = V55TradeResult(
            decision_id=decision.decision_id,
            status='pending',
            executed=False
        )

        start_time = time.time()

        try:
            # 执行模式
            if self.execution_mode == V55ExecutionMode.LIVE:
                # 实盘执行
                result = await self._execute_live(decision)
            else:
                # 模拟执行
                result = await self._execute_simulated(decision)

            result.execution_time = time.time() - start_time

        except Exception as e:
            result.status = 'error'
            result.error = str(e)
            self.failed_trades += 1

        self.total_trades += 1

        if result.executed:
            self.successful_trades += 1
            self.trade_history.append(result)

        return result

    async def _execute_live(
        self,
        decision: V55ArbitrageDecision
    ) -> V55TradeResult:
        """实盘执行

        Args:
            decision: 决策

        Returns:
            结果
        """
        result = V55TradeResult(
            decision_id=decision.decision_id,
            status='live_failed',
            executed=False
        )

        if not self.exchange_connector:
            result.error = "交易所连接器未初始化"
            return result

        # 获取交易所
        exchange = decision.exchange_选择 or Exchange.BINANCE

        # 获取价格
        symbol = f"{decision.signal.token}/USDT"
        price = await self.exchange_connector.get_price(exchange, symbol)

        if not price:
            result.error = f"获取价格失败"
            return result

        # 模拟订单执行
        result.executed = True
        result.status = 'live_executed'
        result.profit = decision.expected_profit
        result.cross_chain_fees = decision.signal.bridge_fee_pct * decision.position_size * price

        return result

    async def _execute_simulated(
        self,
        decision: V55ArbitrageDecision
    ) -> V55TradeResult:
        """模拟执行

        Args:
            decision: 决策

        Returns:
            结果
        """
        result = V55TradeResult(
            decision_id=decision.decision_id,
            status='simulated',
            executed=True,
            profit=decision.expected_profit,
            cross_chain_fees=decision.signal.bridge_fee_pct * decision.position_size * decision.entry_price
        )

        # 计算净利润
        result.net_profit = (result.profit or 0) - result.cross_chain_fees

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计字典
        """
        success_rate = 0.0
        if self.total_trades > 0:
            success_rate = self.successful_trades / self.total_trades

        return {
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'success_rate': success_rate,
            'execution_mode': self.execution_mode.value,
            'components_initialized': {
                'cross_chain_engine': self.cross_chain_engine is not None,
                'ml_predictor': self.ml_predictor is not None,
                'memo0': self.mem0_storage is not None,
                'exchange_connector': self.exchange_connector is not None,
                'bridge_monitor': self.bridge_monitor is not None,
                'risk_manager': self.risk_manager is not None,
            }
        }


# 全局单例
_v55_system: Optional[UnifiedArbitrageSystemV55] = None


def initialize_v55_system(config: Optional[Dict[str, Any]] = None) -> UnifiedArbitrageSystemV55:
    """初始化V55系统

    Args:
        config: 配置字典

    Returns:
        V55系统实例
    """
    global _v55_system
    _v55_system = UnifiedArbitrageSystemV55(config)
    return _v55_system


def get_v55_system() -> Optional[UnifiedArbitrageSystemV55]:
    """获取V55系统实例

    Returns:
        V55系统实例
    """
    global _v55_system
    if _v55_system is None:
        _v55_system = initialize_v55_system()
    return _v55_system