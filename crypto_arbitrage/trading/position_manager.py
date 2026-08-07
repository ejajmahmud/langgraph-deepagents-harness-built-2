"""仓位管理器 - Phase 13核心模块

管理交易仓位，跟踪仓位变化，实现仓位再平衡。

核心功能：
1. 仓位跟踪 - 跟踪所有持仓
2. 仓位调整 - 根据信号调整仓位
3. 仓位再平衡 - 定期再平衡仓位
4. 仓位监控 - 监控仓位变化和盈亏
5. 仓位报告 - 生成详细的仓位报告

创建时间：2026-04-19 23:21:00
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class PositionStatus(Enum):
    """仓位状态"""
    OPEN = "open"            # 开仓
    CLOSED = "closed"        # 平仓
    PARTIAL_CLOSE = "partial_close"  # 部分平仓


class PositionSide(Enum):
    """仓位方向"""
    LONG = "long"            # 多头
    SHORT = "short"           # 空头


class PositionManager:
    """仓位管理器

    管理交易仓位。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化仓位管理器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 仓位管理
        self.positions: Dict[str, Dict] = {}
        self.position_history: List[Dict] = []
        self.max_position_history = 1000

        # 仓位配置
        self.max_positions = self.config.get('max_positions', 10)
        self.max_position_per_symbol = self.config.get('max_position_per_symbol', 3)
        self.enable_auto_rebalance = self.config.get('enable_auto_rebalance', False)
        self.rebalance_interval = self.config.get('rebalance_interval', 3600)  # 1小时

        # 仓位统计
        self.position_stats = {
            'total_opened': 0,
            'total_closed': 0,
            'total_realized_pnl': 0.0,
            'total_unrealized_pnl': 0.0,
            'win_rate': 0.0,
            'avg_holding_time': 0.0,
        }

        # 再平衡任务
        self._rebalance_task: Optional[asyncio.Task] = None

        # 存储引用
        self.storage: Optional[Any] = None

        # 市场数据管理器引用
        self.market_data_manager: Optional[Any] = None

        logger.info("✅ 仓位管理器初始化完成")

    async def initialize(self) -> bool:
        """初始化仓位数据

        Returns:
            是否成功
        """
        logger.info("🚀 初始化仓位管理器...")

        try:
            # 启动再平衡任务
            if self.enable_auto_rebalance:
                self._rebalance_task = asyncio.create_task(
                    self._rebalance_loop()
                )
                logger.info("✅ 再平衡任务已启动")

            logger.info("✅ 仓位管理器初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 仓位管理器初始化失败: {e}")
            return False

    async def stop(self) -> bool:
        """停止仓位管理器

        Returns:
            是否成功
        """
        logger.info("🛑 停止仓位管理器...")

        try:
            # 停止再平衡任务
            if self._rebalance_task:
                self._rebalance_task.cancel()
                try:
                    await self._rebalance_task
                except asyncio.CancelledError:
                    pass

            logger.info("✅ 仓位管理器已停止")
            return True

        except Exception as e:
            logger.error(f"❌ 停止仓位管理器失败: {e}")
            return False

    async def add_position(self, position: Dict[str, Any]) -> Optional[str]:
        """添加仓位

        Args:
            position: 仓位字典

        Returns:
            仓位ID，失败返回None
        """
        try:
            # 检查仓位限制
            if len(self.positions) >= self.max_positions:
                logger.warning(f"⚠️ 已达到最大仓位数量: {self.max_positions}")
                return None

            symbol = position.get('symbol')
            if symbol and self._count_positions_by_symbol(symbol) >= self.max_position_per_symbol:
                logger.warning(f"⚠️ {symbol} 已达到最大仓位数量")
                return None

            # 生成仓位ID
            position_id = self._generate_position_id()
            position['position_id'] = position_id
            position['status'] = PositionStatus.OPEN.value
            position['opened_at'] = datetime.now().isoformat()

            # 计算初始值
            position['entry_price'] = position.get('entry_price', position.get('price', 0))
            position['entry_value'] = position.get('quantity', 0) * position['entry_price']
            position['current_value'] = position['entry_value']
            position['unrealized_pnl'] = 0.0

            # 添加到仓位列表
            self.positions[position_id] = position

            # 更新统计
            self.position_stats['total_opened'] += 1

            # 记录到历史
            self._add_to_position_history(position)

            logger.info(f"✅ 仓位已添加: {position_id}")

            return position_id

        except Exception as e:
            logger.error(f"❌ 添加仓位失败: {e}")
            return None

    async def update_position(
        self,
        position_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """更新仓位

        Args:
            position_id: 仓位ID
            update_data: 更新数据字典

        Returns:
            是否成功
        """
        try:
            # 检查仓位是否存在
            if position_id not in self.positions:
                logger.warning(f"⚠️ 仓位不存在: {position_id}")
                return False

            position = self.positions[position_id]

            # 更新字段
            for key, value in update_data.items():
                position[key] = value

            # 如果更新了当前价格，重新计算盈亏
            if 'current_price' in update_data:
                await self._update_position_pnl(position)

            # 记录到历史
            self._add_to_position_history(position)

            logger.info(f"✅ 仓位已更新: {position_id}")

            return True

        except Exception as e:
            logger.error(f"❌ 更新仓位失败: {e}")
            return False

    async def close_position(
        self,
        position_id: str,
        quantity: Optional[float] = None
    ) -> bool:
        """平仓

        Args:
            position_id: 仓位ID
            quantity: 平仓数量，None表示全部平仓

        Returns:
            是否成功
        """
        try:
            # 检查仓位是否存在
            if position_id not in self.positions:
                logger.warning(f"⚠️ 仓位不存在: {position_id}")
                return False

            position = self.positions[position_id]

            # 检查仓位状态
            if position.get('status') != PositionStatus.OPEN.value:
                logger.warning(f"⚠️ 仓位未开仓: {position_id}")
                return False

            # 确定平仓数量
            close_quantity = quantity if quantity is not None else position.get('quantity', 0)

            # 更新仓位状态
            if close_quantity >= position.get('quantity', 0):
                # 全部平仓
                position['status'] = PositionStatus.CLOSED.value
                position['closed_at'] = datetime.now().isoformat()
                position['closed_price'] = position.get('current_price', position.get('entry_price', 0))
                position['closed_value'] = close_quantity * position['closed_price']

                # 计算已实现盈亏
                position['realized_pnl'] = position.get('unrealized_pnl', 0)

                # 移除仓位
                del self.positions[position_id]

                # 更新统计
                self.position_stats['total_closed'] += 1
                self.position_stats['total_realized_pnl'] += position['realized_pnl']

                logger.info(f"✅ 仓位已平仓: {position_id}, 实现盈亏: ${position['realized_pnl']:.2f}")

            else:
                # 部分平仓
                position['status'] = PositionStatus.PARTIAL_CLOSE.value
                position['quantity'] = position.get('quantity', 0) - close_quantity

                logger.info(f"✅ 仓位已部分平仓: {position_id}, 平仓数量: {close_quantity}")

            # 记录到历史
            self._add_to_position_history(position)

            return True

        except Exception as e:
            logger.error(f"❌ 平仓失败: {e}")
            return False

    def get_positions(self) -> List[Dict[str, Any]]:
        """获取所有仓位

        Returns:
            仓位列表
        """
        return list(self.positions.values())

    def get_position(self, position_id: str) -> Optional[Dict[str, Any]]:
        """获取特定仓位

        Args:
            position_id: 仓位ID

        Returns:
            仓位字典
        """
        return self.positions.get(position_id)

    def get_positions_by_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """获取特定交易对的仓位

        Args:
            symbol: 交易对

        Returns:
            仓位列表
        """
        return [
            position for position in self.positions.values()
            if position.get('symbol') == symbol
        ]

    async def update_all_positions(self) -> Dict[str, Any]:
        """更新所有仓位

        Returns:
            更新结果字典
        """
        try:
            updated_count = 0
            total_unrealized_pnl = 0.0

            for position_id, position in self.positions.items():
                # 获取当前价格
                current_price = await self._get_current_price(position.get('symbol'))
                if current_price:
                    # 更新仓位
                    await self.update_position(position_id, {
                        'current_price': current_price,
                        'updated_at': datetime.now().isoformat(),
                    })
                    updated_count += 1

                    # 累计未实现盈亏
                    total_unrealized_pnl += position.get('unrealized_pnl', 0)

            # 更新统计
            self.position_stats['total_unrealized_pnl'] = total_unrealized_pnl

            return {
                'updated_count': updated_count,
                'total_unrealized_pnl': total_unrealized_pnl,
                'total_positions': len(self.positions),
            }

        except Exception as e:
            logger.error(f"❌ 更新所有仓位失败: {e}")
            return {
                'error': str(e),
            }

    async def rebalance_positions(self) -> Dict[str, Any]:
        """再平衡仓位

        Returns:
            再平衡结果字典
        """
        try:
            if not self.positions:
                return {
                    'status': 'no_positions',
                    'message': '没有需要再平衡的仓位',
                }

            rebalanced_count = 0
            adjustments = []

            for position_id, position in self.positions.items():
                # 计算目标仓位大小
                current_size = position.get('quantity', 0) * position.get('current_price', position.get('entry_price', 0))
                target_size = self._calculate_target_position_size(position)

                # 判断是否需要调整
                if abs(current_size - target_size) > current_size * 0.1:  # 10% 的容差
                    # 生成调整建议
                    adjustment = {
                        'position_id': position_id,
                        'symbol': position.get('symbol'),
                        'current_size': current_size,
                        'target_size': target_size,
                        'adjustment': target_size - current_size,
                        'reason': 'Portfolio rebalancing',
                    }
                    adjustments.append(adjustment)

                    # 这里可以执行实际的仓位调整
                    # rebalanced_count += 1

            return {
                'status': 'completed',
                'rebalanced_count': rebalanced_count,
                'adjustments': adjustments,
                'total_positions': len(self.positions),
            }

        except Exception as e:
            logger.error(f"❌ 再平衡仓位失败: {e}")
            return {
                'status': 'failed',
                'error': str(e),
            }

    def generate_position_report(self) -> Dict[str, Any]:
        """生成仓位报告

        Returns:
            仓位报告字典
        """
        try:
            # 计算敞口统计
            total_exposure = sum(
                abs(p.get('quantity', 0) * p.get('current_price', p.get('entry_price', 0)))
                for p in self.positions.values()
            )

            # 按交易对统计
            positions_by_symbol = defaultdict(list)
            for position in self.positions.values():
                symbol = position.get('symbol', 'unknown')
                positions_by_symbol[symbol].append(position)

            symbol_summary = {}
            for symbol, positions in positions_by_symbol.items():
                total_quantity = sum(p.get('quantity', 0) for p in positions)
                total_value = sum(
                    p.get('quantity', 0) * p.get('current_price', p.get('entry_price', 0))
                    for p in positions
                )
                unrealized_pnl = sum(p.get('unrealized_pnl', 0) for p in positions)

                symbol_summary[symbol] = {
                    'count': len(positions),
                    'total_quantity': total_quantity,
                    'total_value': total_value,
                    'unrealized_pnl': unrealized_pnl,
                }

            return {
                'report_time': datetime.now().isoformat(),
                'total_positions': len(self.positions),
                'total_exposure': total_exposure,
                'unrealized_pnl': self.position_stats['total_unrealized_pnl'],
                'realized_pnl': self.position_stats['total_realized_pnl'],
                'total_pnl': (
                    self.position_stats['total_unrealized_pnl'] +
                    self.position_stats['total_realized_pnl']
                ),
                'positions_by_symbol': symbol_summary,
                'stats': self.position_stats,
            }

        except Exception as e:
            logger.error(f"❌ 生成仓位报告失败: {e}")
            return {
                'error': str(e),
            }

    # ========== 私有方法 ==========

    async def _update_position_pnl(self, position: Dict[str, Any]) -> None:
        """更新仓位盈亏

        Args:
            position: 仓位字典
        """
        try:
            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', entry_price)
            quantity = position.get('quantity', 0)
            side = position.get('side')

            if quantity == 0 or entry_price == 0:
                position['unrealized_pnl'] = 0.0
                return

            # 计算未实现盈亏
            if side == PositionSide.LONG.value:
                # 多头：当前价 - 进场价
                price_diff = current_price - entry_price
            elif side == PositionSide.SHORT.value:
                # 空头：进场价 - 当前价
                price_diff = entry_price - current_price
            else:
                price_diff = 0

            position['unrealized_pnl'] = price_diff * quantity
            position['current_value'] = quantity * current_price
            position['unrealized_pnl_percent'] = (price_diff / entry_price) * 100

        except Exception as e:
            logger.error(f"更新仓位盈亏失败: {e}")
            position['unrealized_pnl'] = 0.0

    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """获取当前价格

        Args:
            symbol: 交易对

        Returns:
            当前价格
        """
        try:
            # 这里应该从市场数据管理器获取实际价格
            # 暂时返回模拟价格
            base_prices = {
                'BTCUSDT': 65000.0,
                'ETHUSDT': 3500.0,
                'BNBUSDT': 550.0,
            }
            return base_prices.get(symbol, 100.0)

        except Exception as e:
            logger.error(f"获取当前价格失败: {e}")
            return None

    def _count_positions_by_symbol(self, symbol: str) -> int:
        """计算特定交易对的仓位数量

        Args:
            symbol: 交易对

        Returns:
            仓位数量
        """
        return len([
            p for p in self.positions.values()
            if p.get('symbol') == symbol
        ])

    def _calculate_target_position_size(self, position: Dict[str, Any]) -> float:
        """计算目标仓位大小

        Args:
            position: 仓位字典

        Returns:
            目标仓位大小
        """
        # 简单的目标仓位计算
        # 实际中可以基于风险预算、权重分配等复杂算法
        current_value = position.get('quantity', 0) * position.get('current_price', position.get('entry_price', 0))
        return current_value  # 暂时保持不变

    def _generate_position_id(self) -> str:
        """生成仓位ID

        Returns:
            仓位ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        import random
        random_str = ''.join(random.choices('0123456789ABCDEF', k=8))
        return f"POS_{timestamp}_{random_str}"

    def _add_to_position_history(self, position: Dict[str, Any]) -> None:
        """添加到仓位历史

        Args:
            position: 仓位字典
        """
        self.position_history.append(position.copy())

        # 限制历史大小
        if len(self.position_history) > self.max_position_history:
            self.position_history = self.position_history[-self.max_position_history:]

    async def _rebalance_loop(self) -> None:
        """再平衡循环"""
        while True:
            try:
                # 执行再平衡
                await self.rebalance_positions()

                # 等待下一个周期
                await asyncio.sleep(self.rebalance_interval)

            except asyncio.CancelledError:
                logger.info("再平衡任务已取消")
                break
            except Exception as e:
                logger.error(f"再平衡失败: {e}")
                await asyncio.sleep(10)  # 错误后等待10秒


# ========== 全局仓位管理器实例 ==========

_position_manager_instance: Optional[PositionManager] = None


def get_position_manager() -> PositionManager:
    """获取仓位管理器单例

    Returns:
        仓位管理器实例
    """
    global _position_manager_instance
    if _position_manager_instance is None:
        _position_manager_instance = PositionManager()
    return _position_manager_instance
