"""交易协调器 - Phase 13核心模块

协调交易流程，管理交易生命周期，确保从市场数据到交易执行的完整流程顺畅运行。

核心功能：
1. 交易流程编排 - 协调市场数据、信号生成、风险控制、交易执行
2. 交易生命周期管理 - 统一管理交易的生命周期
3. 交易队列管理 - 管理待执行、执行中、已完成的交易
4. 交易事件处理 - 处理交易相关的事件
5. 交易性能监控 - 监控交易性能指标

创建时间：2026-04-19 23:06:00
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    """交易状态"""
    PENDING = "pending"           # 待执行
    QUEUED = "queued"             # 已排队
    EXECUTING = "executing"       # 执行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class TradeEventType(Enum):
    """交易事件类型"""
    TRADE_CREATED = "trade_created"
    TRADE_QUEUED = "trade_queued"
    TRADE_EXECUTING = "trade_executing"
    TRADE_COMPLETED = "trade_completed"
    TRADE_FAILED = "trade_failed"
    TRADE_CANCELLED = "trade_cancelled"
    RISK_CHECK_PASSED = "risk_check_passed"
    RISK_CHECK_FAILED = "risk_check_failed"
    EXECUTION_ERROR = "execution_error"
    CIRCUIT_BREAKER_TRIGGERED = "circuit_breaker_triggered"


class TradingCoordinator:
    """交易协调器

    协调交易流程，管理交易生命周期。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化交易协调器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 交易队列
        self.trade_queue: deque = deque()
        self.executing_trades: Dict[str, Dict] = {}
        self.completed_trades: List[Dict] = []
        self.max_completed_trades = 1000

        # 交易统计
        self.stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'cancelled_trades': 0,
            'avg_execution_time': 0.0,
            'total_profit': 0.0,
            'total_loss': 0.0,
        }

        # 事件总线
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.event_history: List[Dict] = []
        self.max_event_history = 1000

        # 配置参数
        self.max_queue_size = self.config.get('max_queue_size', 100)
        self.execution_timeout = self.config.get('execution_timeout', 30)  # 秒
        self.enable_circuit_breaker = self.config.get('enable_circuit_breaker', True)
        self.circuit_breaker_threshold = self.config.get('circuit_breaker_threshold', 5)
        self.circuit_breaker_window = self.config.get('circuit_breaker_window', 300)  # 秒
        self.circuit_breaker_cooldown = self.config.get('circuit_breaker_cooldown', 600)  # 秒

        # 熔断器状态
        self.circuit_breaker_triggered = False
        self.circuit_breaker_triggered_at: Optional[datetime] = None
        self.failed_trades_window: deque = deque()

        # 交易周期任务
        self._trading_cycle_task: Optional[asyncio.Task] = None
        self._trading_cycle_interval = self.config.get('trading_cycle_interval', 5)  # 秒

        # 模块引用
        self.market_data_manager: Optional[Any] = None
        self.signal_generator: Optional[Any] = None
        self.risk_manager: Optional[Any] = None
        self.execution_engine: Optional[Any] = None
        self.position_manager: Optional[Any] = None
        self.trade_monitor: Optional[Any] = None

        logger.info("✅ 交易协调器初始化完成")

    async def initialize(self) -> bool:
        """初始化交易协调器

        Returns:
            是否成功
        """
        logger.info("🚀 初始化交易协调器...")

        try:
            # 这里可以初始化各个交易模块
            # 实际实现中会从其他模块导入

            logger.info("✅ 交易协调器初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 交易协调器初始化失败: {e}")
            return False

    async def start(self) -> bool:
        """启动交易流程

        Returns:
            是否成功
        """
        logger.info("🚀 启动交易流程...")

        try:
            # 启动交易周期任务
            self._trading_cycle_task = asyncio.create_task(
                self._trading_cycle_loop()
            )

            logger.info("✅ 交易流程启动成功")
            return True

        except Exception as e:
            logger.error(f"❌ 交易流程启动失败: {e}")
            return False

    async def stop(self) -> bool:
        """停止交易流程

        Returns:
            是否成功
        """
        logger.info("🛑 停止交易流程...")

        try:
            # 停止交易周期任务
            if self._trading_cycle_task:
                self._trading_cycle_task.cancel()
                try:
                    await self._trading_cycle_task
                except asyncio.CancelledError:
                    pass

            logger.info("✅ 交易流程停止成功")
            return True

        except Exception as e:
            logger.error(f"❌ 交易流程停止失败: {e}")
            return False

    async def execute_trade(self, trade: Dict[str, Any]) -> Optional[str]:
        """执行交易

        Args:
            trade: 交易字典

        Returns:
            交易ID，失败返回None
        """
        try:
            # 检查熔断器
            if self.circuit_breaker_triggered:
                if self._is_circuit_breaker_active():
                    logger.warning("⚠️ 熔断器激活，拒绝交易")
                    await self._publish_event({
                        'type': TradeEventType.CIRCUIT_BREAKER_TRIGGERED,
                        'data': trade
                    })
                    return None

            # 生成交易ID
            trade_id = self._generate_trade_id()
            trade['trade_id'] = trade_id
            trade['status'] = TradeStatus.PENDING.value
            trade['created_at'] = datetime.now().isoformat()

            # 发布交易创建事件
            await self._publish_event({
                'type': TradeEventType.TRADE_CREATED,
                'data': trade
            })

            # 添加到交易队列
            if len(self.trade_queue) >= self.max_queue_size:
                logger.warning("⚠️ 交易队列已满")
                trade['status'] = TradeStatus.FAILED.value
                trade['error'] = "Trade queue is full"
                await self._publish_event({
                    'type': TradeEventType.TRADE_FAILED,
                    'data': trade
                })
                return None

            self.trade_queue.append(trade)
            self.stats['total_trades'] += 1

            # 发布交易排队事件
            trade['status'] = TradeStatus.QUEUED.value
            await self._publish_event({
                'type': TradeEventType.TRADE_QUEUED,
                'data': trade
            })

            logger.info(f"✅ 交易已排队: {trade_id}")
            return trade_id

        except Exception as e:
            logger.error(f"❌ 执行交易失败: {e}")
            return None

    def get_trading_status(self) -> Dict[str, Any]:
        """获取交易状态

        Returns:
            交易状态字典
        """
        return {
            'queue_size': len(self.trade_queue),
            'executing_trades': len(self.executing_trades),
            'completed_trades': len(self.completed_trades),
            'circuit_breaker_triggered': self.circuit_breaker_triggered,
            'circuit_breaker_active': self._is_circuit_breaker_active(),
            'stats': self.stats,
        }

    def get_trade_queue(self) -> List[Dict]:
        """获取交易队列

        Returns:
            交易队列列表
        """
        return list(self.trade_queue)

    def get_completed_trades(self, limit: int = 100) -> List[Dict]:
        """获取已完成交易

        Args:
            limit: 返回数量限制

        Returns:
            已完成交易列表
        """
        return self.completed_trades[-limit:]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标

        Returns:
            性能指标字典
        """
        total_trades = self.stats['total_trades']
        if total_trades == 0:
            return {
                'success_rate': 0.0,
                'avg_execution_time': 0.0,
                'profit_loss': 0.0,
                'profit_factor': 0.0,
            }

        success_rate = self.stats['successful_trades'] / total_trades
        avg_execution_time = self.stats['avg_execution_time']
        profit_loss = self.stats['total_profit'] - self.stats['total_loss']

        if self.stats['total_loss'] > 0:
            profit_factor = self.stats['total_profit'] / self.stats['total_loss']
        else:
            profit_factor = float('inf') if self.stats['total_profit'] > 0 else 0.0

        return {
            'success_rate': success_rate,
            'avg_execution_time': avg_execution_time,
            'profit_loss': profit_loss,
            'profit_factor': profit_factor,
            'total_trades': total_trades,
            'successful_trades': self.stats['successful_trades'],
            'failed_trades': self.stats['failed_trades'],
            'cancelled_trades': self.stats['cancelled_trades'],
        }

    # ========== 事件处理 ==========

    def register_event_handler(
        self,
        event_type: str,
        handler: Callable
    ) -> None:
        """注册事件处理器

        Args:
            event_type: 事件类型
            handler: 事件处理器函数
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.debug(f"注册交易事件处理器: {event_type}")

    async def publish_trade_event(self, event: Dict[str, Any]) -> None:
        """发布交易事件

        Args:
            event: 事件字典
        """
        await self._publish_event(event)

    async def handle_trade_event(self, event: Dict[str, Any]) -> None:
        """处理交易事件

        Args:
            event: 事件字典
        """
        event_type = event.get('type')
        logger.info(f"处理交易事件: {event_type}")

        # 调用注册的事件处理器
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"事件处理器执行失败: {e}")

    # ========== 私有方法 ==========

    async def _trading_cycle_loop(self) -> None:
        """交易周期循环"""
        while True:
            try:
                # 执行交易周期
                await self._execute_trading_cycle()

                # 等待下一个周期
                await asyncio.sleep(self._trading_cycle_interval)

            except asyncio.CancelledError:
                logger.info("交易周期任务已取消")
                break
            except Exception as e:
                logger.error(f"交易周期执行失败: {e}")
                await asyncio.sleep(10)  # 错误后等待10秒

    async def _execute_trading_cycle(self) -> None:
        """执行交易周期"""
        try:
            # 1. 收集市场数据
            market_data = await self._collect_market_data()
            if not market_data:
                return

            # 2. 生成交易信号
            signals = await self._generate_trading_signals(market_data)
            if not signals:
                return

            # 3. 评估风险
            risk_assessment = await self._assess_risk(signals)
            if not risk_assessment['approved']:
                logger.warning(f"风险评估未通过: {risk_assessment.get('reason')}")
                return

            # 4. 处理交易队列
            await self._process_trade_queue()

            # 5. 监控仓位
            await self._monitor_positions()

        except Exception as e:
            logger.error(f"交易周期执行失败: {e}")

    async def _collect_market_data(self) -> Optional[Dict[str, Any]]:
        """收集市场数据

        Returns:
            市场数据字典
        """
        try:
            if self.market_data_manager:
                return await self.market_data_manager.get_market_data()
            else:
                logger.warning("市场数据管理器未初始化")
                return None
        except Exception as e:
            logger.error(f"收集市场数据失败: {e}")
            return None

    async def _generate_trading_signals(
        self,
        market_data: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """生成交易信号

        Args:
            market_data: 市场数据

        Returns:
            交易信号列表
        """
        try:
            if self.signal_generator:
                return await self.signal_generator.generate_signals(market_data)
            else:
                logger.warning("信号生成器未初始化")
                return None
        except Exception as e:
            logger.error(f"生成交易信号失败: {e}")
            return None

    async def _assess_risk(
        self,
        signals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """评估风险

        Args:
            signals: 交易信号列表

        Returns:
            风险评估字典
        """
        try:
            if self.risk_manager:
                return await self.risk_manager.check_pre_trade_risk(signals)
            else:
                logger.warning("风险管理器未初始化")
                return {'approved': True, 'reason': 'Risk manager not initialized'}
        except Exception as e:
            logger.error(f"风险评估失败: {e}")
            return {'approved': False, 'reason': f'Risk assessment error: {e}'}

    async def _process_trade_queue(self) -> None:
        """处理交易队列"""
        while self.trade_queue and not self._is_circuit_breaker_active():
            # 获取下一个交易
            trade = self.trade_queue.popleft()

            # 添加到执行中
            trade_id = trade['trade_id']
            trade['status'] = TradeStatus.EXECUTING.value
            trade['started_at'] = datetime.now().isoformat()
            self.executing_trades[trade_id] = trade

            # 发布交易执行事件
            await self._publish_event({
                'type': TradeEventType.TRADE_EXECUTING,
                'data': trade
            })

            # 执行交易
            asyncio.create_task(self._execute_single_trade(trade))

    async def _execute_single_trade(self, trade: Dict[str, Any]) -> None:
        """执行单个交易

        Args:
            trade: 交易字典
        """
        trade_id = trade['trade_id']
        start_time = time.time()

        try:
            # 执行订单
            if self.execution_engine:
                execution_result = await self.execution_engine.execute_order(
                    trade.get('order')
                )

                # 检查执行结果
                if execution_result.get('success'):
                    # 交易成功
                    trade['status'] = TradeStatus.COMPLETED.value
                    trade['completed_at'] = datetime.now().isoformat()
                    trade['execution_result'] = execution_result

                    # 更新统计
                    execution_time = time.time() - start_time
                    self.stats['successful_trades'] += 1
                    self.stats['avg_execution_time'] = (
                        (self.stats['avg_execution_time'] * (self.stats['successful_trades'] - 1) +
                         execution_time) / self.stats['successful_trades']
                    )

                    # 更新盈亏
                    profit = execution_result.get('profit', 0)
                    if profit >= 0:
                        self.stats['total_profit'] += profit
                    else:
                        self.stats['total_loss'] += abs(profit)

                    # 清理失败交易窗口
                    self._clean_failed_trades_window()

                    # 发布交易完成事件
                    await self._publish_event({
                        'type': TradeEventType.TRADE_COMPLETED,
                        'data': trade
                    })

                    logger.info(f"✅ 交易执行成功: {trade_id}")

                else:
                    # 交易失败
                    trade['status'] = TradeStatus.FAILED.value
                    trade['completed_at'] = datetime.now().isoformat()
                    trade['error'] = execution_result.get('error', 'Unknown error')

                    # 更新统计
                    self.stats['failed_trades'] += 1

                    # 添加到失败交易窗口
                    self._add_to_failed_trades_window(trade)

                    # 检查熔断器
                    if self.enable_circuit_breaker:
                        self._check_circuit_breaker()

                    # 发布交易失败事件
                    await self._publish_event({
                        'type': TradeEventType.TRADE_FAILED,
                        'data': trade
                    })

                    # 发布执行错误事件
                    await self._publish_event({
                        'type': TradeEventType.EXECUTION_ERROR,
                        'data': {
                            'trade_id': trade_id,
                            'error': trade['error'],
                            'execution_result': execution_result,
                        }
                    })

                    logger.error(f"❌ 交易执行失败: {trade_id} - {trade['error']}")

            else:
                logger.warning("交易执行引擎未初始化")
                trade['status'] = TradeStatus.FAILED.value
                trade['error'] = "Execution engine not initialized"

        except Exception as e:
            logger.error(f"❌ 执行交易异常: {trade_id} - {e}")
            trade['status'] = TradeStatus.FAILED.value
            trade['error'] = str(e)

            # 添加到失败交易窗口
            self._add_to_failed_trades_window(trade)

            # 检查熔断器
            if self.enable_circuit_breaker:
                self._check_circuit_breaker()

        finally:
            # 从执行中移除
            if trade_id in self.executing_trades:
                del self.executing_trades[trade_id]

            # 添加到已完成
            self.completed_trades.append(trade)

            # 限制已完成交易数量
            if len(self.completed_trades) > self.max_completed_trades:
                self.completed_trades = self.completed_trades[-self.max_completed_trades:]

    async def _monitor_positions(self) -> None:
        """监控仓位"""
        try:
            if self.position_manager:
                positions = await self.position_manager.get_positions()
                logger.debug(f"当前仓位: {len(positions)} 个")
        except Exception as e:
            logger.error(f"监控仓位失败: {e}")

    def cancel_trade(self, trade_id: str) -> bool:
        """取消交易

        Args:
            trade_id: 交易ID

        Returns:
            是否成功
        """
        try:
            # 检查交易是否在队列中
            for trade in self.trade_queue:
                if trade['trade_id'] == trade_id:
                    self.trade_queue.remove(trade)
                    trade['status'] = TradeStatus.CANCELLED.value
                    trade['cancelled_at'] = datetime.now().isoformat()

                    # 更新统计
                    self.stats['cancelled_trades'] += 1

                    # 发布取消事件
                    asyncio.create_task(self._publish_event({
                        'type': TradeEventType.TRADE_CANCELLED,
                        'data': trade
                    }))

                    logger.info(f"✅ 交易已取消: {trade_id}")
                    return True

            # 检查交易是否在执行中
            if trade_id in self.executing_trades:
                logger.warning(f"⚠️ 交易正在执行中，无法取消: {trade_id}")
                return False

            logger.warning(f"⚠️ 未找到交易: {trade_id}")
            return False

        except Exception as e:
            logger.error(f"❌ 取消交易失败: {e}")
            return False

    def _generate_trade_id(self) -> str:
        """生成交易ID

        Returns:
            交易ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        import random
        random_str = ''.join(random.choices('0123456789ABCDEF', k=8))
        return f"TRADE_{timestamp}_{random_str}"

    def _is_circuit_breaker_active(self) -> bool:
        """检查熔断器是否激活

        Returns:
            是否激活
        """
        if not self.circuit_breaker_triggered:
            return False

        # 检查冷却时间
        if self.circuit_breaker_triggered_at:
            cooldown_end = self.circuit_breaker_triggered_at + timedelta(
                seconds=self.circuit_breaker_cooldown
            )
            if datetime.now() > cooldown_end:
                # 冷却结束，重置熔断器
                logger.info("✅ 熔断器冷却结束，重置熔断器")
                self.circuit_breaker_triggered = False
                self.circuit_breaker_triggered_at = None
                return False

        return True

    def _check_circuit_breaker(self) -> None:
        """检查熔断器"""
        if not self.enable_circuit_breaker:
            return

        # 清理过期的失败交易
        self._clean_failed_trades_window()

        # 检查失败交易数量
        if len(self.failed_trades_window) >= self.circuit_breaker_threshold:
            # 触发熔断器
            self.circuit_breaker_triggered = True
            self.circuit_breaker_triggered_at = datetime.now()

            logger.warning(
                f"🚨 熔断器触发！{self.circuit_breaker_threshold}个交易在"
                f"{self.circuit_breaker_window}秒内失败"
            )

            # 发布熔断器事件
            asyncio.create_task(self._publish_event({
                'type': TradeEventType.CIRCUIT_BREAKER_TRIGGERED,
                'data': {
                    'failed_trades': len(self.failed_trades_window),
                    'window': self.circuit_breaker_window,
                    'threshold': self.circuit_breaker_threshold,
                }
            }))

    def _add_to_failed_trades_window(self, trade: Dict[str, Any]) -> None:
        """添加失败交易到窗口

        Args:
            trade: 交易字典
        """
        self.failed_trades_window.append({
            'trade_id': trade['trade_id'],
            'timestamp': datetime.now(),
        })

    def _clean_failed_trades_window(self) -> None:
        """清理过期的失败交易"""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.circuit_breaker_window)

        # 保留窗口内的失败交易
        self.failed_trades_window = deque([
            ft for ft in self.failed_trades_window
            if ft['timestamp'] >= window_start
        ])

    async def _publish_event(self, event: Dict[str, Any]) -> None:
        """发布事件

        Args:
            event: 事件字典
        """
        # 记录事件历史
        event['published_at'] = datetime.now().isoformat()
        self.event_history.append(event)

        # 限制历史大小
        if len(self.event_history) > self.max_event_history:
            self.event_history = self.event_history[-self.max_event_history:]

        # 调用事件处理器
        event_type = event.get('type')
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"事件处理器执行失败: {e}")


# ========== 全局交易协调器实例 ==========

_trading_coordinator_instance: Optional[TradingCoordinator] = None


def get_trading_coordinator() -> TradingCoordinator:
    """获取交易协调器单例

    Returns:
        交易协调器实例
    """
    global _trading_coordinator_instance
    if _trading_coordinator_instance is None:
        _trading_coordinator_instance = TradingCoordinator()
    return _trading_coordinator_instance
