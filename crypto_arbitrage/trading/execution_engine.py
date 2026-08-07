"""交易执行引擎 - Phase 13核心模块

执行交易订单，管理订单生命周期，优化订单执行。

核心功能：
1. 订单执行管理 - 管理订单的创建、提交、取消
2. 智能订单路由 - 智能选择最优交易所
3. 执行优化 - 优化订单执行以减少滑点
4. 执行监控 - 监控订单执行状态
5. 执行报告 - 生成详细的执行报告

创建时间：2026-04-19 23:18:00
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"        # 市价单
    LIMIT = "limit"          # 限价单
    STOP_LOSS = "stop_loss"  # 止损单
    TAKE_PROFIT = "take_profit"  # 止盈单


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"        # 待提交
    SUBMITTED = "submitted"    # 已提交
    PARTIAL_FILLED = "partial_filled"  # 部分成交
    FILLED = "filled"          # 完全成交
    CANCELLED = "cancelled"    # 已取消
    REJECTED = "rejected"      # 已拒绝
    EXPIRED = "expired"        # 已过期
    FAILED = "failed"          # 失败


class ExecutionEngine:
    """交易执行引擎

    执行交易订单。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化交易执行引擎

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 订单管理
        self.orders: Dict[str, Dict] = {}
        self.order_history: List[Dict] = []
        self.max_order_history = 1000

        # 交易所连接
        self.exchanges: Dict[str, Dict] = {}
        self.active_exchange: Optional[str] = None

        # 执行配置
        self.execution_timeout = self.config.get('execution_timeout', 30)  # 秒
        self.max_retries = self.config.get('max_retries', 3)
        self.enable_smart_routing = self.config.get('enable_smart_routing', True)
        self.enable_execution_optimization = self.config.get('enable_execution_optimization', True)

        # 执行统计
        self.execution_stats = {
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'cancelled_orders': 0,
            'avg_execution_time': 0.0,
            'avg_slippage': 0.0,
            'total_volume': 0.0,
            'total_value': 0.0,
        }

        # 订单队列
        self.order_queue: asyncio.Queue = asyncio.Queue()
        self._order_processing_task: Optional[asyncio.Task] = None

        # 存储引用
        self.storage: Optional[Any] = None

        # 市场数据管理器引用
        self.market_data_manager: Optional[Any] = None

        logger.info("✅ 交易执行引擎初始化完成")

    async def initialize(self) -> bool:
        """初始化交易所连接

        Returns:
            是否成功
        """
        logger.info("🚀 初始化交易执行引擎...")

        try:
            # 注册默认交易所
            await self._register_default_exchanges()

            # 选择活动交易所
            if self.exchanges:
                self.active_exchange = next(iter(self.exchanges.keys()))
                logger.info(f"✅ 活动交易所: {self.active_exchange}")
            else:
                logger.warning("⚠️ 未注册交易所，使用模拟执行")
                self.active_exchange = 'simulation'

            # 启动订单处理任务
            self._order_processing_task = asyncio.create_task(
                self._order_processing_loop()
            )
            logger.info("✅ 订单处理任务已启动")

            logger.info("✅ 交易执行引擎初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 交易执行引擎初始化失败: {e}")
            return False

    async def stop(self) -> bool:
        """停止交易执行引擎

        Returns:
            是否成功
        """
        logger.info("🛑 停止交易执行引擎...")

        try:
            # 停止订单处理任务
            if self._order_processing_task:
                self._order_processing_task.cancel()
                try:
                    await self._order_processing_task
                except asyncio.CancelledError:
                    pass

            # 取消所有未完成订单
            await self._cancel_all_pending_orders()

            logger.info("✅ 交易执行引擎已停止")
            return True

        except Exception as e:
            logger.error(f"❌ 停止交易执行引擎失败: {e}")
            return False

    async def execute_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """执行订单

        Args:
            order: 订单字典

        Returns:
            执行结果字典
        """
        try:
            # 生成订单ID
            order_id = self._generate_order_id()
            order['order_id'] = order_id

            # 验证订单
            validation_result = self._validate_order(order)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'order_id': order_id,
                    'error': validation_result['reason'],
                    'status': OrderStatus.REJECTED.value,
                }

            # 预先存储订单到orders字典，确保_wait_for_order_completion能找到
            self.orders[order_id] = order
            order['status'] = OrderStatus.PENDING.value
            order['created_at'] = datetime.now().isoformat()

            # 添加到订单队列
            await self.order_queue.put(order)
            self.execution_stats['total_orders'] += 1

            logger.info(f"✅ 订单已添加到队列: {order_id}")

            # 等待订单完成（超时控制）
            try:
                return await asyncio.wait_for(
                    self._wait_for_order_completion(order_id),
                    timeout=self.execution_timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ 订单执行超时: {order_id}")
                return {
                    'success': False,
                    'order_id': order_id,
                    'error': 'Execution timeout',
                    'status': OrderStatus.FAILED.value,
                }

        except Exception as e:
            logger.error(f"❌ 执行订单失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'status': OrderStatus.FAILED.value,
            }

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """取消订单

        Args:
            order_id: 订单ID

        Returns:
            取消结果字典
        """
        try:
            # 检查订单是否存在
            if order_id not in self.orders:
                return {
                    'success': False,
                    'error': f'Order not found: {order_id}',
                }

            order = self.orders[order_id]
            current_status = order.get('status')

            # 检查订单状态
            if current_status in [OrderStatus.FILLED.value, OrderStatus.CANCELLED.value]:
                return {
                    'success': False,
                    'error': f'Order cannot be cancelled: current status={current_status}',
                }

            # 更新订单状态
            order['status'] = OrderStatus.CANCELLED.value
            order['cancelled_at'] = datetime.now().isoformat()

            # 记录到历史
            self._add_to_order_history(order)

            # 更新统计
            self.execution_stats['cancelled_orders'] += 1

            logger.info(f"✅ 订单已取消: {order_id}")

            return {
                'success': True,
                'order_id': order_id,
                'status': OrderStatus.CANCELLED.value,
            }

        except Exception as e:
            logger.error(f"❌ 取消订单失败: {e}")
            return {
                'success': False,
                'error': str(e),
            }

    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """获取订单状态

        Args:
            order_id: 订单ID

        Returns:
            订单状态字典
        """
        return self.orders.get(order_id)

    def get_execution_report(self) -> Dict[str, Any]:
        """获取执行报告

        Returns:
            执行报告字典
        """
        return {
            'stats': self.execution_stats,
            'active_orders': len([o for o in self.orders.values() if o.get('status') in [
                OrderStatus.PENDING.value,
                OrderStatus.SUBMITTED.value,
                OrderStatus.PARTIAL_FILLED.value,
            ]]),
            'total_orders': len(self.orders),
            'active_exchange': self.active_exchange,
        }

    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息

        Returns:
            执行统计信息字典
        """
        total_orders = self.execution_stats['total_orders']
        successful_orders = self.execution_stats['successful_orders']
        failed_orders = self.execution_stats['failed_orders']

        success_rate = successful_orders / total_orders if total_orders > 0 else 0.0
        avg_execution_time = self.execution_stats['avg_execution_time']
        avg_slippage = self.execution_stats['avg_slippage']

        return {
            'total_orders': total_orders,
            'successful_orders': successful_orders,
            'failed_orders': failed_orders,
            'cancelled_orders': self.execution_stats['cancelled_orders'],
            'success_rate': success_rate,
            'avg_execution_time': avg_execution_time,
            'avg_slippage': avg_slippage,
            'total_volume': self.execution_stats['total_volume'],
            'total_value': self.execution_stats['total_value'],
            'active_exchange': self.active_exchange,
            'timestamp': datetime.now().isoformat()
        }

    # ========== 私有方法 ==========

    async def _register_default_exchanges(self) -> None:
        """注册默认交易所"""
        # 注册模拟交易所
        self.exchanges['simulation'] = {
            'type': 'simulation',
            'enabled': True,
            'latency': 0.1,  # 100ms
            'fee_rate': 0.001,  # 0.1%
        }

        # 可以在这里注册真实交易所
        # self.exchanges['binance'] = {'type': 'binance', 'enabled': False}

    async def _order_processing_loop(self) -> None:
        """订单处理循环"""
        while True:
            try:
                # 从队列获取订单
                order = await self.order_queue.get()

                # 处理订单
                await self._process_order(order)

            except asyncio.CancelledError:
                logger.info("订单处理任务已取消")
                break
            except Exception as e:
                logger.error(f"订单处理失败: {e}")
                await asyncio.sleep(1)

    async def _process_order(self, order: Dict[str, Any]) -> None:
        """处理订单

        Args:
            order: 订单字典
        """
        order_id = order['order_id']
        start_time = time.time()

        # 存储订单到orders字典，供_wait_for_order_completion查询
        self.orders[order_id] = order

        try:
            # 更新订单状态
            order['status'] = OrderStatus.SUBMITTED.value
            order['submitted_at'] = datetime.now().isoformat()
            order['exchange'] = self.active_exchange

            # 智能路由
            if self.enable_smart_routing:
                selected_exchange = await self._select_exchange(order)
                order['exchange'] = selected_exchange
                logger.info(f"智能路由选择: {selected_exchange}")

            # 执行优化
            if self.enable_execution_optimization:
                order = await self._optimize_order(order)

            # 执行订单
            execution_result = await self._execute_order_on_exchange(order)

            # 更新订单状态
            order['status'] = execution_result['status']
            order['executed_at'] = datetime.now().isoformat()
            order['execution_result'] = execution_result

            # 计算执行时间
            execution_time = time.time() - start_time
            order['execution_time'] = execution_time

            # 更新统计
            if execution_result['success']:
                self.execution_stats['successful_orders'] += 1
                self.execution_stats['total_volume'] += execution_result.get('filled_quantity', 0)
                self.execution_stats['total_value'] += execution_result.get('filled_value', 0)

                # 更新平均执行时间
                successful_count = self.execution_stats['successful_orders']
                old_avg = self.execution_stats['avg_execution_time']
                self.execution_stats['avg_execution_time'] = (
                    (old_avg * (successful_count - 1) + execution_time) / successful_count
                )

                # 计算滑点
                if 'slippage' in execution_result:
                    slippage = execution_result['slippage']
                    total_slippage = self.execution_stats['avg_slippage'] * (successful_count - 1)
                    self.execution_stats['avg_slippage'] = (total_slippage + slippage) / successful_count

                logger.info(f"✅ 订单执行成功: {order_id}, 执行时间: {execution_time:.2f}s")

            else:
                self.execution_stats['failed_orders'] += 1
                logger.error(f"❌ 订单执行失败: {order_id}, 错误: {execution_result.get('error')}")

            # 记录到历史
            self._add_to_order_history(order)

            # 从orders字典中清理已完成的订单，避免内存泄漏
            self.orders.pop(order_id, None)

        except Exception as e:
            logger.error(f"处理订单失败: {order_id}, 错误: {e}")
            order['status'] = OrderStatus.FAILED.value
            order['error'] = str(e)
            order['failed_at'] = datetime.now().isoformat()

            # 记录到历史
            self._add_to_order_history(order)

            # 从orders字典中清理失败的订单
            self.orders.pop(order_id, None)

    async def _execute_order_on_exchange(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """在交易所执行订单

        Args:
            order: 订单字典

        Returns:
            执行结果字典
        """
        try:
            exchange = order.get('exchange', 'simulation')

            if exchange == 'simulation':
                return await self._execute_simulation_order(order)
            else:
                logger.warning(f"未实现交易所: {exchange}")
                return {
                    'success': False,
                    'status': OrderStatus.FAILED.value,
                    'error': f'Exchange not implemented: {exchange}',
                }

        except Exception as e:
            logger.error(f"在交易所执行订单失败: {e}")
            return {
                'success': False,
                'status': OrderStatus.FAILED.value,
                'error': str(e),
            }

    async def _execute_simulation_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """执行模拟订单

        Args:
            order: 订单字典

        Returns:
            执行结果字典
        """
        import random

        # 模拟延迟
        await asyncio.sleep(0.1)

        # 获取订单参数
        order_type = order.get('type', OrderType.MARKET.value)
        side = order.get('side')
        symbol = order.get('symbol')
        quantity = order.get('quantity')
        price = order.get('price')

        # 模拟执行
        if order_type == OrderType.MARKET.value:
            # 市价单直接成交
            execution_price = price * (1 + random.uniform(-0.001, 0.001))  # 模拟滑点
            slippage = abs((execution_price - price) / price) * 100

            result = {
                'success': True,
                'status': OrderStatus.FILLED.value,
                'filled_quantity': quantity,
                'filled_price': execution_price,
                'filled_value': quantity * execution_price,
                'slippage': slippage,
                'fee': quantity * execution_price * 0.001,  # 0.1% 手续费
            }
        elif order_type == OrderType.LIMIT.value:
            # 限价单部分成交
            filled_quantity = quantity * random.uniform(0.5, 1.0)
            if filled_quantity > 0:
                result = {
                    'success': True,
                    'status': OrderStatus.FILLED.value if filled_quantity == quantity else OrderStatus.PARTIAL_FILLED.value,
                    'filled_quantity': filled_quantity,
                    'filled_price': price,
                    'filled_value': filled_quantity * price,
                    'slippage': 0.0,
                    'fee': filled_quantity * price * 0.001,
                }
            else:
                result = {
                    'success': False,
                    'status': OrderStatus.EXPIRED.value,
                    'error': 'Order expired without fill',
                }
        else:
            result = {
                'success': False,
                'status': OrderStatus.REJECTED.value,
                'error': f'Unsupported order type: {order_type}',
            }

        return result

    async def _select_exchange(self, order: Dict[str, Any]) -> str:
        """选择交易所

        Args:
            order: 订单字典

        Returns:
            交易所名称
        """
        # 简单的交易所选择逻辑
        # 实际中可以基于流动性、手续费、延迟等因素选择
        return self.active_exchange or 'simulation'

    async def _optimize_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """优化订单

        Args:
            order: 订单字典

        Returns:
            优化后的订单字典
        """
        # 简单的订单优化
        # 实际中可以基于市场深度、波动率等因素优化
        return order

    async def _wait_for_order_completion(self, order_id: str) -> Dict[str, Any]:
        """等待订单完成

        Args:
            order_id: 订单ID

        Returns:
            执行结果字典
        """
        while True:
            order = self.orders.get(order_id)

            if order is None:
                return {
                    'success': False,
                    'order_id': order_id,
                    'error': 'Order not found',
                }

            status = order.get('status')

            if status in [OrderStatus.FILLED.value, OrderStatus.CANCELLED.value,
                         OrderStatus.REJECTED.value, OrderStatus.EXPIRED.value,
                         OrderStatus.FAILED.value]:
                return {
                    'success': status == OrderStatus.FILLED.value,
                    'order_id': order_id,
                    'status': status,
                    'execution_result': order.get('execution_result', {}),
                }

            # 等待100ms后检查
            await asyncio.sleep(0.1)

    async def _cancel_all_pending_orders(self) -> None:
        """取消所有待处理订单"""
        pending_orders = [
            (order_id, order)
            for order_id, order in self.orders.items()
            if order.get('status') in [
                OrderStatus.PENDING.value,
                OrderStatus.SUBMITTED.value,
                OrderStatus.PARTIAL_FILLED.value,
            ]
        ]

        for order_id, order in pending_orders:
            await self.cancel_order(order_id)

    def _validate_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """验证订单

        Args:
            order: 订单字典

        Returns:
            验证结果字典
        """
        # 检查必要字段
        required_fields = ['side', 'symbol', 'quantity']
        for field in required_fields:
            if field not in order:
                return {
                    'valid': False,
                    'reason': f'Missing required field: {field}',
                }

        # 检查订单方向
        side = order.get('side')
        if side not in [OrderSide.BUY.value, OrderSide.SELL.value]:
            return {
                'valid': False,
                'reason': f'Invalid order side: {side}',
            }

        # 检查数量
        quantity = order.get('quantity', 0)
        if quantity <= 0:
            return {
                'valid': False,
                'reason': f'Invalid quantity: {quantity}',
            }

        # 检查价格（限价单需要价格）
        order_type = order.get('type', OrderType.MARKET.value)
        if order_type == OrderType.LIMIT.value:
            price = order.get('price', 0)
            if price <= 0:
                return {
                    'valid': False,
                    'reason': f'Invalid price for limit order: {price}',
                }

        return {
            'valid': True,
        }

    def _generate_order_id(self) -> str:
        """生成订单ID

        Returns:
            订单ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        import random
        random_str = ''.join(random.choices('0123456789ABCDEF', k=8))
        return f"ORDER_{timestamp}_{random_str}"

    def _add_to_order_history(self, order: Dict[str, Any]) -> None:
        """添加到订单历史

        Args:
            order: 订单字典
        """
        self.order_history.append(order.copy())

        # 限制历史大小
        if len(self.order_history) > self.max_order_history:
            self.order_history = self.order_history[-self.max_order_history:]


# ========== 全局交易执行引擎实例 ==========

_execution_engine_instance: Optional[ExecutionEngine] = None


def get_execution_engine() -> ExecutionEngine:
    """获取交易执行引擎单例

    Returns:
        交易执行引擎实例
    """
    global _execution_engine_instance
    if _execution_engine_instance is None:
        _execution_engine_instance = ExecutionEngine()
    return _execution_engine_instance
