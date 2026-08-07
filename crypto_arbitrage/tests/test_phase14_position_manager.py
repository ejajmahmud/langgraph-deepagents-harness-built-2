"""PositionManager单元测试 - Phase 14 Week 1

测试仓位管理器的核心功能：
1. 初始化和配置
2. 仓位管理（添加、更新、平仓）
3. 仓位统计和报告
4. 风险评估

创建时间：2026-04-20 07:45:00
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from typing import Dict, Any

from trading.position_manager import (
    PositionManager,
    PositionStatus,
    PositionSide,
)


class TestPositionManagerInitialization:
    """测试PositionManager初始化"""

    @pytest.fixture
    def manager(self):
        """创建测试用的PositionManager实例"""
        return PositionManager()

    def test_initialization_default_config(self, manager):
        """测试默认配置初始化"""
        assert manager.config == {}
        assert manager.max_positions == 10
        assert manager.max_position_per_symbol == 3
        assert manager.enable_auto_rebalance is False
        assert manager.rebalance_interval == 3600
        assert len(manager.positions) == 0
        assert len(manager.position_history) == 0

    def test_initialization_custom_config(self):
        """测试自定义配置初始化"""
        config = {
            'max_positions': 5,
            'max_position_per_symbol': 2,
            'enable_auto_rebalance': True,
        }
        manager = PositionManager(config)
        assert manager.max_positions == 5
        assert manager.max_position_per_symbol == 2
        assert manager.enable_auto_rebalance is True

    def test_initialization_stats(self, manager):
        """测试统计信息初始化"""
        assert manager.position_stats['total_opened'] == 0
        assert manager.position_stats['total_closed'] == 0
        assert manager.position_stats['total_realized_pnl'] == 0.0
        assert manager.position_stats['total_unrealized_pnl'] == 0.0


class TestPositionManagerLifecycle:
    """测试PositionManager生命周期"""

    @pytest_asyncio.fixture
    async def initialized_manager(self):
        """创建已初始化的PositionManager实例"""
        manager = PositionManager()
        await manager.initialize()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """测试成功初始化"""
        manager = PositionManager()
        result = await manager.initialize()
        assert result is True
        await manager.stop()

    @pytest.mark.asyncio
    async def test_stop_success(self, initialized_manager):
        """测试成功停止"""
        result = await initialized_manager.stop()
        assert result is True


class TestPositionManagement:
    """测试仓位管理"""

    @pytest_asyncio.fixture
    async def initialized_manager(self):
        """创建已初始化的PositionManager实例"""
        manager = PositionManager()
        await manager.initialize()
        yield manager
        await manager.stop()

    @pytest.fixture
    def valid_position(self):
        """创建有效仓位"""
        return {
            'symbol': 'BTCUSDT',
            'side': 'long',
            'quantity': 1.0,
            'price': 65000.0,
        }

    @pytest.mark.asyncio
    async def test_add_position_success(self, initialized_manager, valid_position):
        """测试成功添加仓位"""
        position_id = await initialized_manager.add_position(valid_position)
        assert position_id is not None
        assert position_id in initialized_manager.positions

    @pytest.mark.asyncio
    async def test_add_position_exceeds_max_positions(self, initialized_manager):
        """测试超过最大仓位数量"""
        # 设置较小的最大值
        initialized_manager.max_positions = 2

        position = {
            'symbol': 'BTCUSDT',
            'side': 'long',
            'quantity': 1.0,
            'price': 65000.0,
        }

        # 添加2个仓位
        await initialized_manager.add_position(position)
        await initialized_manager.add_position(position)

        # 第3个应该失败
        position_id = await initialized_manager.add_position(position)
        assert position_id is None

    @pytest.mark.asyncio
    async def test_add_position_exceeds_max_per_symbol(self, initialized_manager):
        """测试超过单个交易对最大仓位数量"""
        # 设置较小的最大值
        initialized_manager.max_position_per_symbol = 2

        position = {
            'symbol': 'BTCUSDT',
            'side': 'long',
            'quantity': 1.0,
            'price': 65000.0,
        }

        # 添加2个BTCUSDT仓位
        await initialized_manager.add_position(position)
        await initialized_manager.add_position(position)

        # 第3个应该失败
        position_id = await initialized_manager.add_position(position)
        assert position_id is None

    @pytest.mark.asyncio
    async def test_update_position_success(self, initialized_manager, valid_position):
        """测试成功更新仓位"""
        position_id = await initialized_manager.add_position(valid_position)
        assert position_id is not None

        # 更新仓位
        update_data = {
            'current_price': 66000.0,
        }
        result = await initialized_manager.update_position(position_id, update_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_update_nonexistent_position(self, initialized_manager):
        """测试更新不存在的仓位"""
        result = await initialized_manager.update_position('nonexistent_id', {'current_price': 66000.0})
        assert result is False

    @pytest.mark.asyncio
    async def test_close_position_success(self, initialized_manager, valid_position):
        """测试成功平仓"""
        position_id = await initialized_manager.add_position(valid_position)
        assert position_id is not None

        # 先更新当前价格
        await initialized_manager.update_position(position_id, {'current_price': 66000.0})

        # 平仓
        result = await initialized_manager.close_position(position_id)
        assert result is True
        assert position_id not in initialized_manager.positions

    @pytest.mark.asyncio
    async def test_close_position_partial(self, initialized_manager, valid_position):
        """测试部分平仓"""
        position_id = await initialized_manager.add_position(valid_position)
        assert position_id is not None

        # 更新当前价格
        await initialized_manager.update_position(position_id, {'current_price': 66000.0})

        # 部分平仓
        result = await initialized_manager.close_position(position_id, quantity=0.5)
        assert result is True
        # 仓位应该还存在
        assert position_id in initialized_manager.positions

    @pytest.mark.asyncio
    async def test_close_nonexistent_position(self, initialized_manager):
        """测试平仓不存在的仓位"""
        result = await initialized_manager.close_position('nonexistent_id')
        assert result is False


class TestPositionReporting:
    """测试仓位报告"""

    @pytest_asyncio.fixture
    async def initialized_manager(self):
        """创建已初始化的PositionManager实例"""
        manager = PositionManager()
        await manager.initialize()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_get_positions_empty(self, initialized_manager):
        """测试获取空仓位列表"""
        positions = initialized_manager.get_positions()
        assert positions == []

    @pytest.mark.asyncio
    async def test_get_positions_with_data(self, initialized_manager):
        """测试获取仓位列表"""
        position = {
            'symbol': 'BTCUSDT',
            'side': 'long',
            'quantity': 1.0,
            'price': 65000.0,
        }
        await initialized_manager.add_position(position)

        positions = initialized_manager.get_positions()
        assert len(positions) == 1

    @pytest.mark.asyncio
    async def test_get_position_by_id(self, initialized_manager):
        """测试根据ID获取仓位"""
        position = {
            'symbol': 'BTCUSDT',
            'side': 'long',
            'quantity': 1.0,
            'price': 65000.0,
        }
        position_id = await initialized_manager.add_position(position)

        retrieved_position = initialized_manager.get_position(position_id)
        assert retrieved_position is not None
        assert retrieved_position['position_id'] == position_id


class TestPositionStatistics:
    """测试仓位统计"""

    @pytest_asyncio.fixture
    async def initialized_manager(self):
        """创建已初始化的PositionManager实例"""
        manager = PositionManager()
        await manager.initialize()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_statistics_updated_on_add_position(self, initialized_manager):
        """测试添加仓位时统计更新"""
        initial_opened = initialized_manager.position_stats['total_opened']

        position = {
            'symbol': 'BTCUSDT',
            'side': 'long',
            'quantity': 1.0,
            'price': 65000.0,
        }
        await initialized_manager.add_position(position)

        assert initialized_manager.position_stats['total_opened'] > initial_opened

    @pytest.mark.asyncio
    async def test_statistics_updated_on_close_position(self, initialized_manager):
        """测试平仓时统计更新"""
        position = {
            'symbol': 'BTCUSDT',
            'side': 'long',
            'quantity': 1.0,
            'price': 65000.0,
        }
        position_id = await initialized_manager.add_position(position)

        # 更新价格以计算盈亏
        await initialized_manager.update_position(position_id, {'current_price': 66000.0})

        initial_closed = initialized_manager.position_stats['total_closed']

        # 平仓
        await initialized_manager.close_position(position_id)

        assert initialized_manager.position_stats['total_closed'] > initial_closed


class TestPositionRiskAssessment:
    """测试仓位风险评估"""

    @pytest_asyncio.fixture
    async def initialized_manager(self):
        """创建已初始化的PositionManager实例"""
        manager = PositionManager()
        await manager.initialize()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_position_pnl_calculation(self, initialized_manager):
        """测试仓位盈亏计算"""
        position = {
            'symbol': 'BTCUSDT',
            'side': 'long',
            'quantity': 1.0,
            'price': 65000.0,
        }
        position_id = await initialized_manager.add_position(position)

        # 更新到更高价格
        await initialized_manager.update_position(position_id, {'current_price': 66000.0})

        # 获取仓位
        position = initialized_manager.get_position(position_id)
        assert position is not None
        assert 'unrealized_pnl' in position

    @pytest.mark.asyncio
    async def test_position_value_calculation(self, initialized_manager):
        """测试仓位价值计算"""
        position = {
            'symbol': 'BTCUSDT',
            'side': 'long',
            'quantity': 2.0,
            'price': 65000.0,
        }
        position_id = await initialized_manager.add_position(position)

        # 获取仓位
        position = initialized_manager.get_position(position_id)
        assert position is not None
        assert position['entry_value'] == 130000.0  # 2.0 * 65000.0


class TestErrorHandling:
    """测试错误处理"""

    @pytest_asyncio.fixture
    async def initialized_manager(self):
        """创建已初始化的PositionManager实例"""
        manager = PositionManager()
        await manager.initialize()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_add_position_with_missing_fields(self, initialized_manager):
        """测试添加缺失字段的仓位"""
        incomplete_position = {
            'symbol': 'BTCUSDT',
            # 缺少其他必要字段
        }
        position_id = await initialized_manager.add_position(incomplete_position)
        # 应该仍然返回position_id，使用默认值
        assert position_id is not None

    @pytest.mark.asyncio
    async def test_update_position_with_invalid_data(self, initialized_manager):
        """测试更新无效数据"""
        position = {
            'symbol': 'BTCUSDT',
            'side': 'long',
            'quantity': 1.0,
            'price': 65000.0,
        }
        position_id = await initialized_manager.add_position(position)

        # 尝试更新无效字段
        result = await initialized_manager.update_position(position_id, {'invalid_field': 'value'})
        # 应该仍然成功，只是忽略无效字段
        assert result is True


class TestPositionSides:
    """测试不同仓位方向"""

    @pytest_asyncio.fixture
    async def initialized_manager(self):
        """创建已初始化的PositionManager实例"""
        manager = PositionManager()
        await manager.initialize()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_long_position(self, initialized_manager):
        """测试多头仓位"""
        position = {
            'symbol': 'BTCUSDT',
            'side': 'long',
            'quantity': 1.0,
            'price': 65000.0,
        }
        position_id = await initialized_manager.add_position(position)
        assert position_id is not None

        position = initialized_manager.get_position(position_id)
        assert position['side'] == 'long'

    @pytest.mark.asyncio
    async def test_short_position(self, initialized_manager):
        """测试空头仓位"""
        position = {
            'symbol': 'BTCUSDT',
            'side': 'short',
            'quantity': 1.0,
            'price': 65000.0,
        }
        position_id = await initialized_manager.add_position(position)
        assert position_id is not None

        position = initialized_manager.get_position(position_id)
        assert position['side'] == 'short'


class TestPositionHistory:
    """测试仓位历史"""

    @pytest_asyncio.fixture
    async def initialized_manager(self):
        """创建已初始化的PositionManager实例"""
        manager = PositionManager()
        await manager.initialize()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_position_history_updated(self, initialized_manager):
        """测试仓位历史更新"""
        initial_history_length = len(initialized_manager.position_history)

        position = {
            'symbol': 'BTCUSDT',
            'side': 'long',
            'quantity': 1.0,
            'price': 65000.0,
        }
        await initialized_manager.add_position(position)

        assert len(initialized_manager.position_history) > initial_history_length
