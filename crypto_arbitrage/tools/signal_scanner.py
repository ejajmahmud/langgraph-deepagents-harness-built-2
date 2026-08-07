"""实时信号扫描器 - V1.3 (Phase 104新增智能信号评分)

持续监控多个交易所，生成套利信号并自动执行交易。

核心功能:
1. 多交易所价格监控
2. 跨交易所价差检测
3. 信号生成与智能评分 (新增: 历史表现评分)
4. 信号持久化到Memo0
5. 机会过滤
6. 集成多策略编排器
7. 信号自动执行
8. 动态仓位计算 (新增)
9. 交易前风控预检查 (新增)

运行方式:
    python -m tools.signal_scanner
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 尝试导入Memo0存储
try:
    from storage.mem0_storage import get_unified_storage
    _MEM0_STORAGE_AVAILABLE = True
except ImportError:
    _MEM0_STORAGE_AVAILABLE = False
    get_unified_storage = None


class SignalType(Enum):
    """信号类型"""
    CROSS_EXCHANGE = "cross_exchange"  # 跨交易所套利
    TRIANGULAR = "triangular"       # 三角套利
    FUNDING = "funding"           # 资金费率套利
    CONVERGENCE = "convergence"    # 价差收敛


class SignalStatus(Enum):
    """信号状态"""
    ACTIVE = "active"      # 活跃
    EXPIRED = "expired"  # 已过期
    EXECUTED = "executed"  # 已执行


@dataclass
class ArbitrageSignal:
    """套利信号"""
    signal_id: str
    signal_type: SignalType
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread: float  # 价差百分比
    expected_profit: float
    confidence: float  # 置信度 0-1
    timestamp: float
    status: SignalStatus = SignalStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'signal_id': self.signal_id,
            'signal_type': self.signal_type.value,
            'symbol': self.symbol,
            'buy_exchange': self.buy_exchange,
            'sell_exchange': self.sell_exchange,
            'buy_price': self.buy_price,
            'sell_price': self.sell_price,
            'spread': self.spread,
            'expected_profit': self.expected_profit,
            'confidence': self.confidence,
            'timestamp': self.timestamp,
            'status': self.status.value,
        }


class SignalScanner:
    """实时信号扫描器 - V1.3

    持续监控交易所价格，生成套利信号并可选自动执行。
    新增功能:
    - 智能信号评分 (基于历史表现)
    - 动态仓位计算
    - 交易前风控预检查
    """

    def __init__(
        self,
        exchanges: Dict[str, Any],
        min_spread: float = 0.2,  # 最小价差百分比
        min_profit: float = 10.0,    # 最小预期利润
        scan_interval: float = 2.0,  # 扫描间隔（秒）
        auto_execute: bool = False,  # 是否自动执行
        portfolio_manager=None,  # 组合风险管理器 (新增)
    ):
        """初始化信号扫描器

        Args:
            exchanges: 交易所字典 {name: exchange_instance}
            min_spread: 最小价差百分比 (%)
            min_profit: 最小预期利润
            scan_interval: 扫描间隔（秒）
            auto_execute: 是否自动执行信号
            portfolio_manager: 组合风险管理器（可选，用于风控预检查）
        """
        self.exchanges = exchanges
        self.min_spread = min_spread
        self.min_profit = min_profit
        self.scan_interval = scan_interval
        self.auto_execute = auto_execute
        self.portfolio_manager = portfolio_manager

        # 执行器（用于自动执行）
        self._executor = None
        self._trade_state = None

        # 信号历史用于评分 (新增)
        self._signal_performance_history: List[Dict[str, Any]] = []

        # 交易对配置
        self.symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

        # 信号存储
        self.active_signals: Dict[str, ArbitrageSignal] = {}
        self.signal_history: List[ArbitrageSignal] = []

        # 统计
        self.total_scans = 0
        self.total_signals = 0
        self.expired_signals = 0
        self.executed_signals = 0

        # 控制
        self._running = False
        self._scan_task: Optional[asyncio.Task] = None

        # 信号回调
        self._signal_callbacks: List[callable] = []

        logger.info(
            f"信号扫描器初始化: {len(exchanges)} 交易所, "
            f"最小价差={min_spread}%, 最小利润=${min_profit}, "
            f"自动执行={auto_execute}"
        )

    def add_signal_callback(self, callback: callable) -> None:
        """添加信号回调

        Args:
            callback: 信号回调函数 (signal: ArbitrageSignal) -> None
        """
        self._signal_callbacks.append(callback)
        logger.info(f"添加信号回调: {callback.__name__}")

    def set_executor(self, executor, trade_state=None) -> None:
        """设置执行器

        Args:
            executor: 模拟执行器实例
            trade_state: 交易状态管理器（可选）
        """
        self._executor = executor
        self._trade_state = trade_state
        logger.info(f"执行器已设置: {executor.__class__.__name__}")

    async def start(self) -> None:
        """启动扫描器"""
        if self._running:
            logger.warning("扫描器已在运行中")
            return

        self._running = True
        self._scan_task = asyncio.create_task(self._scan_loop())
        logger.info("信号扫描器已启动")

    async def stop(self) -> None:
        """停止扫描器"""
        if not self._running:
            return

        self._running = False
        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass

        logger.info("信号扫描器已停止")

    async def _scan_loop(self) -> None:
        """扫描循环"""
        while self._running:
            try:
                await self._scan_prices()
                self.total_scans += 1
            except Exception as e:
                logger.error(f"扫描循环异常: {e}")

            await asyncio.sleep(self.scan_interval)

    async def _scan_prices(self) -> None:
        """扫描价格并检测信号"""
        for symbol in self.symbols:
            await self._check_cross_exchange_opportunity(symbol)

    async def _check_cross_exchange_opportunity(self, symbol: str) -> None:
        """检查跨交易所套利机会

        Args:
            symbol: 交易对
        """
        exchange_names = list(self.exchanges.keys())

        # 获取所有交易所的价格
        prices: Dict[str, Dict[str, float]] = {}  # exchange -> {bid, ask}

        for exchange_name in exchange_names:
            try:
                exchange = self.exchanges[exchange_name]
                ticker = await exchange.fetch_ticker(symbol)
                prices[exchange_name] = {
                    'bid': ticker.get('bid', ticker.get('last', 0)),
                    'ask': ticker.get('ask', ticker.get('last', 0)),
                }
            except Exception as e:
                logger.debug(f"获取 {exchange_name} {symbol} 价格失败: {e}")
                continue

        if len(prices) < 2:
            return

        # 寻找最佳买卖组合
        best_opportunity: Optional[Dict[str, Any]] = None

        for buy_ex in exchange_names:
            for sell_ex in exchange_names:
                if buy_ex == sell_ex:
                    continue

                buy_price = prices[buy_ex]['ask']
                sell_price = prices[sell_ex]['bid']

                if buy_price <= 0 or sell_price <= 0:
                    continue

                # 计算价差
                spread = (sell_price - buy_price) / buy_price * 100
                expected_profit = (sell_price - buy_price) * 0.1  # 假设交易0.1单位

                # 检查是否满足条件
                if spread >= self.min_spread and expected_profit >= self.min_profit:
                    if best_opportunity is None or spread > best_opportunity['spread']:
                        best_opportunity = {
                            'symbol': symbol,
                            'buy_exchange': buy_ex,
                            'sell_exchange': sell_ex,
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'spread': spread,
                            'expected_profit': expected_profit,
                        }

        # 如果发现机会，生成信号
        if best_opportunity:
            await self._generate_signal(best_opportunity)

    async def _generate_signal(self, opportunity: Dict[str, Any]) -> None:
        """生成套利信号

        Args:
            opportunity: 机会字典
        """
        signal_id = f"sig_{int(time.time() * 1000)}"

        # 计算置信度 (基于价差)
        spread = opportunity['spread']
        confidence = min(1.0, spread / 1.0)  # 价差1%时置信度为1

        signal = ArbitrageSignal(
            signal_id=signal_id,
            signal_type=SignalType.CROSS_EXCHANGE,
            symbol=opportunity['symbol'],
            buy_exchange=opportunity['buy_exchange'],
            sell_exchange=opportunity['sell_exchange'],
            buy_price=opportunity['buy_price'],
            sell_price=opportunity['sell_price'],
            spread=opportunity['spread'],
            expected_profit=opportunity['expected_profit'],
            confidence=confidence,
            timestamp=time.time(),
            status=SignalStatus.ACTIVE,
        )

        self.active_signals[signal_id] = signal
        self.total_signals += 1

        # 保存到Memo0存储 (V1.1新增)
        self._save_signal_to_storage(signal)

        # 自动执行（如果启用）
        if self.auto_execute and self._executor:
            await self._execute_signal(signal)

        # 触发回调
        for callback in self._signal_callbacks:
            try:
                callback(signal)
            except Exception as e:
                logger.error(f"信号回调异常: {e}")

        logger.info(
            f"生成信号: {signal_id} {signal.signal_type.value} "
            f"{signal.symbol} {signal.buy_exchange}→{signal.sell_exchange} "
            f"价差={signal.spread:.2f}% 预期利润=${signal.expected_profit:.2f}"
        )

    def _save_signal_to_storage(self, signal: ArbitrageSignal) -> None:
        """保存信号到Memo0存储

        Args:
            signal: 套利信号
        """
        if not _MEM0_STORAGE_AVAILABLE:
            return

        try:
            storage = get_unified_storage()
            if storage is None:
                return

            # 构建信号内容
            content = (
                f"套利信号: {signal.symbol} "
                f"{signal.buy_exchange}→{signal.sell_exchange} "
                f"价差={signal.spread:.2f}% "
                f"预期利润=${signal.expected_profit:.2f} "
                f"置信度={signal.confidence:.1%} "
                f"类型={signal.signal_type.value}"
            )

            metadata = {
                'signal_id': signal.signal_id,
                'symbol': signal.symbol,
                'buy_exchange': signal.buy_exchange,
                'sell_exchange': signal.sell_exchange,
                'buy_price': signal.buy_price,
                'sell_price': signal.sell_price,
                'spread': signal.spread,
                'expected_profit': signal.expected_profit,
                'confidence': signal.confidence,
                'signal_type': signal.signal_type.value,
                'status': signal.status.value,
            }

            storage.add_knowledge('arbitrage_signal', content, metadata)
            logger.debug(f"信号已保存到存储: {signal.signal_id}")
        except Exception as e:
            logger.debug(f"保存信号到存储失败: {e}")

    def _calculate_enhanced_confidence(self, signal: ArbitrageSignal) -> float:
        """计算增强的信号置信度（基于历史表现）

        Args:
            signal: 套利信号

        Returns:
            增强后的置信度 (0-1)
        """
        # 基础置信度 (基于价差)
        base_confidence = min(1.0, signal.spread / 1.0)

        # 历史表现评分
        history_score = 0.5  # 默认中立
        if self._signal_performance_history:
            # 计算最近N次信号的成功率
            recent_signals = self._signal_performance_history[-10:]
            successful = sum(1 for s in recent_signals if s.get('actual_profit', 0) > 0)
            history_score = successful / len(recent_signals) if recent_signals else 0.5

        # 时间衰减因子 (信号越新越可靠)
        time_elapsed = time.time() - signal.timestamp
        recency_factor = max(0.7, 1.0 - time_elapsed / 300)  # 5分钟后衰减

        # 综合评分
        # 基础置信度60% + 历史表现25% + 时间因子15%
        enhanced = base_confidence * 0.6 + history_score * 0.25 + recency_factor * 0.15

        return min(1.0, max(0.0, enhanced))

    def calculate_position_size(
        self,
        signal: ArbitrageSignal,
        available_capital: float = 100000.0
    ) -> float:
        """计算动态仓位

        Args:
            signal: 套利信号
            available_capital: 可用资金

        Returns:
            推荐仓位数量
        """
        # 基础仓位 (使用1%资金)
        base_size = available_capital * 0.01 / signal.buy_price

        # 根据置信度调整仓位
        confidence_multiplier = signal.confidence

        # 根据价差调整仓位 (价差越大，仓位可以越大)
        spread_multiplier = min(2.0, signal.spread / 0.5)

        # 综合仓位
        position_size = base_size * confidence_multiplier * spread_multiplier

        # 限制最大仓位
        max_size = available_capital * 0.05 / signal.buy_price  # 最大5%资金
        return min(position_size, max_size)

    def pre_execution_risk_check(self, signal: ArbitrageSignal) -> Dict[str, Any]:
        """交易前风控预检查

        Args:
            signal: 套利信号

        Returns:
            检查结果字典
        """
        # 如果没有组合风险管理器，直接通过
        if self.portfolio_manager is None:
            return {'allowed': True, 'reason': '无组合风控管理器'}

        try:
            # 检查组合状态
            summary = self.portfolio_manager.get_portfolio_summary()

            # 检查是否暂停交易
            if summary['risk']['is_halted']:
                return {
                    'allowed': False,
                    'reason': '组合已暂停交易',
                    'detail': f"当前回撤: {summary['risk']['current_drawdown']*100:.2f}%"
                }

            # 计算建议仓位
            position_value = self.calculate_position_size(
                signal,
                summary['capital']['current']
            ) * signal.buy_price

            # 检查开仓权限
            can_open = self.portfolio_manager.can_open_position(
                symbol=signal.symbol,
                position_value=position_value
            )

            if not can_open['allowed']:
                return {
                    'allowed': False,
                    'reason': can_open.get('message', '开仓被拒绝'),
                    'detail': can_open.get('detail', '')
                }

            return {
                'allowed': True,
                'reason': '通过风控检查',
                'recommended_size': position_value / signal.buy_price,
                'current_drawdown': summary['risk']['current_drawdown']
            }

        except Exception as e:
            logger.warning(f"风控检查异常: {e}")
            return {'allowed': True, 'reason': f'风控检查异常: {e}'}

    def record_execution_result(
        self,
        signal_id: str,
        actual_profit: float,
        execution_time: float
    ) -> None:
        """记录执行结果用于后续评分

        Args:
            signal_id: 信号ID
            actual_profit: 实际利润
            execution_time: 执行时间
        """
        self._signal_performance_history.append({
            'signal_id': signal_id,
            'actual_profit': actual_profit,
            'execution_time': execution_time,
            'timestamp': time.time()
        })

        # 保留最近50条记录
        if len(self._signal_performance_history) > 50:
            self._signal_performance_history = self._signal_performance_history[-50:]

    async def _execute_signal(self, signal: ArbitrageSignal) -> Dict[str, Any]:
        """自动执行信号

        Args:
            signal: 套利信号

        Returns:
            执行结果字典
        """
        # 交易前风控预检查 (新增)
        risk_check = self.pre_execution_risk_check(signal)
        if not risk_check['allowed']:
            logger.warning(f"风控预检查未通过: {risk_check['reason']}")
            return {'status': 'rejected', 'reason': risk_check['reason']}

        if self._executor is None:
            return {'status': 'no_executor', 'error': '未设置执行器'}

        # 计算动态仓位
        position_size = self.calculate_position_size(signal)
        logger.info(f"动态计算仓位: {position_size:.4f} {signal.symbol}")

        try:
            if signal.signal_type == SignalType.CROSS_EXCHANGE:
                # 执行跨交易所套利
                result = await self._executor.execute_cross_exchange_arbitrage(
                    symbol=signal.symbol,
                    buy_exchange=signal.buy_exchange,
                    sell_exchange=signal.sell_exchange,
                    amount=position_size,  # 使用动态仓位
                    expected_profit=signal.expected_profit
                )

                # 记录到交易状态
                if result['status'] == 'completed' and self._trade_state:
                    self._trade_state.open_position(
                        symbol=signal.symbol,
                        entry_price=signal.buy_price,
                        amount=position_size,
                        side='long',
                        exchange=signal.buy_exchange
                    )
                    self._trade_state.close_position(
                        symbol=signal.symbol,
                        exit_price=signal.sell_price
                    )

                # 记录执行结果用于后续评分
                if result['status'] == 'completed':
                    self.record_execution_result(
                        signal.signal_id,
                        result.get('actual_profit', 0),
                        result.get('execution_time', 0)
                    )

                # 标记已执行
                if result['status'] == 'completed':
                    self.mark_executed(signal.signal_id)
                    logger.info(f"信号已自动执行: {signal.signal_id}, 利润=${result.get('actual_profit', 0):.2f}")

                return result

        except Exception as e:
            logger.error(f"自动执行信号失败: {e}")
            return {'status': 'error', 'error': str(e)}

        return {'status': 'unsupported', 'error': '不支持的信号类型'}

    def get_active_signals(self) -> List[ArbitrageSignal]:
        """获取活跃信号"""
        return list(self.active_signals.values())

    def get_signal_by_id(self, signal_id: str) -> Optional[ArbitrageSignal]:
        """按ID获取信号"""
        return self.active_signals.get(signal_id)

    def mark_executed(self, signal_id: str) -> bool:
        """标记信号已执行

        Args:
            signal_id: 信号ID

        Returns:
            是否成功
        """
        signal = self.active_signals.get(signal_id)
        if signal is None:
            return False

        signal.status = SignalStatus.EXECUTED
        self.signal_history.append(signal)
        del self.active_signals[signal_id]
        self.executed_signals += 1

        logger.info(f"信号已执行: {signal_id}")
        return True

    def mark_expired(self, signal_id: str) -> bool:
        """标记信号已过期

        Args:
            signal_id: 信号ID

        Returns:
            是否成功
        """
        signal = self.active_signals.get(signal_id)
        if signal is None:
            return False

        signal.status = SignalStatus.EXPIRED
        self.signal_history.append(signal)
        del self.active_signals[signal_id]
        self.expired_signals += 1

        logger.info(f"信号已过期: {signal_id}")
        return True

    def cleanup_expired_signals(self, max_age: float = 60.0) -> int:
        """清理过期信号

        Args:
            max_age: 最大存活时间（秒）

        Returns:
            清理数量
        """
        current_time = time.time()
        expired_ids = []

        for signal_id, signal in self.active_signals.items():
            if current_time - signal.timestamp > max_age:
                expired_ids.append(signal_id)

        for signal_id in expired_ids:
            self.mark_expired(signal_id)

        return len(expired_ids)

    def search_stored_signals(
        self,
        query: str = "arbitrage_signal",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """从Memo0存储搜索信号历史

        Args:
            query: 查询关键词
            limit: 返回数量

        Returns:
            信号列表
        """
        if not _MEM0_STORAGE_AVAILABLE:
            return []

        try:
            storage = get_unified_storage()
            if storage is None:
                return []

            results = storage.search_knowledge(query, 'arbitrage_signal', limit)
            return results
        except Exception as e:
            logger.debug(f"搜索存储信号失败: {e}")
            return []

    def get_signal_history_from_storage(self, limit: int = 10) -> List[Dict[str, Any]]:
        """从Memo0存储获取信号历史

        Args:
            limit: 返回数量

        Returns:
            信号列表
        """
        if not _MEM0_STORAGE_AVAILABLE:
            return []

        try:
            storage = get_unified_storage()
            if storage is None:
                return []

            results = storage.get_all_knowledge('arbitrage_signal')
            return results[:limit]
        except Exception as e:
            logger.debug(f"获取信号历史失败: {e}")
            return []

    def get_scanner_summary(self) -> Dict[str, Any]:
        """获取扫描器摘要"""
        return {
            'total_scans': self.total_scans,
            'total_signals': self.total_signals,
            'active_signals': len(self.active_signals),
            'expired_signals': self.expired_signals,
            'executed_signals': self.executed_signals,
            'signals_history': len(self.signal_history),
            'is_running': self._running,
        }

    def get_all_signals(self) -> List[Dict[str, Any]]:
        """获取所有信号（包括历史）"""
        all_signals = []

        for signal in self.active_signals.values():
            all_signals.append(signal.to_dict())

        for signal in self.signal_history:
            all_signals.append(signal.to_dict())

        return all_signals


# 工厂函数
def create_signal_scanner(
    exchanges: Dict[str, Any],
    min_spread: float = 0.2,
    min_profit: float = 10.0,
    scan_interval: float = 2.0,
    auto_execute: bool = False,
    portfolio_manager=None,  # 新增: 组合风险管理器
) -> SignalScanner:
    """工厂函数：创建信号扫描器

    Args:
        exchanges: 交易所字典
        min_spread: 最小价差百分比
        min_profit: 最小预期利润
        scan_interval: 扫描间隔
        auto_execute: 是否自动执行信号
        portfolio_manager: 组合风险管理器（可选，用于风控预检查）

    Returns:
        SignalScanner实例
    """
    return SignalScanner(
        exchanges=exchanges,
        min_spread=min_spread,
        min_profit=min_profit,
        scan_interval=scan_interval,
        auto_execute=auto_execute,
        portfolio_manager=portfolio_manager,
    )