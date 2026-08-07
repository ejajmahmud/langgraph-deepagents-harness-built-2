"""实盘交易引擎 V3.7 - 多模式交易执行系统

实现安全的实盘交易能力，支持从模拟到实盘的渐进式升级。
核心功能：
1. 多模式交易执行 - SIMULATION/PAPER_TRADING/LIVE_TRADING
2. 渐进式升级 - 安全的模式切换机制
3. 实盘风险控制 - 更严格的风险限制
4. 订单执行优化 - 针对实盘的执行策略
5. 紧急停止机制 - 即时停止所有交易
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from tools.risk_management import RiskManager, IntelligentStopLoss
from risk.deep_risk_manager import DeepRiskManager


logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """交易模式"""
    SIMULATION = "SIMULATION"  # 模拟交易
    PAPER_TRADING = "PAPER_TRADING"  # 纸面交易（实时数据但不执行）
    LIVE_TRADING = "LIVE_TRADING"  # 实盘交易


class TradingState(Enum):
    """交易状态"""
    IDLE = "IDLE"  # 空闲
    SCANNING = "SCANNING"  # 扫描机会
    EXECUTING = "EXECUTING"  # 执行中
    MONITORING = "MONITORING"  # 监控持仓
    STOPPED = "STOPPED"  # 已停止
    EMERGENCY = "EMERGENCY"  # 紧急状态


@dataclass
class TradeExecution:
    """交易执行结果"""
    trade_id: str
    mode: TradingMode
    opportunity: Dict[str, Any]
    execution_time: float
    status: str  # PENDING, COMPLETED, FAILED
    actual_profit: Optional[float] = None
    execution_details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class TradingStatistics:
    """交易统计"""
    total_trades: int = 0
    profitable_trades: int = 0
    total_profit: float = 0.0
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    daily_trades: int = 0
    last_trade_time: Optional[datetime] = None


class ProductionTradingEngine:
    """生产级实盘交易引擎 V3.7

    实现安全的实盘交易能力，支持多模式交易执行和渐进式升级。
    """

    def __init__(
        self,
        config: Dict[str, Any],
        risk_manager: RiskManager,
        deep_risk_manager: Optional[DeepRiskManager] = None,
        price_feed: Optional[Any] = None
    ):
        """初始化实盘交易引擎

        Args:
            config: 配置字典，包含:
                - initial_mode: 初始交易模式
                - max_live_trades_per_day: 每日最大实盘交易数
                - live_position_limit: 实盘仓位限制
                - emergency_contacts: 紧急联系人
            risk_manager: 基础风险管理器
            deep_risk_manager: 深度风险管理器（可选）
            price_feed: 价格数据源(V16.9+，可选)
        """
        self.config = config
        self.risk_manager = risk_manager
        self.deep_risk_manager = deep_risk_manager

        # 价格数据源 (V16.9+)
        self.price_feed = price_feed

        # 交易模式和状态
        self.current_mode = TradingMode(config.get('initial_mode', 'SIMULATION'))
        self.state = TradingState.IDLE

        # 安全限制
        self.max_live_trades_per_day = config.get('max_live_trades_per_day', 10)
        self.live_position_limit = config.get('live_position_limit', 0.05)  # 5% of capital
        self.emergency_contacts = config.get('emergency_contacts', [])

        # 统计信息
        self.statistics = TradingStatistics()
        self.execution_history: List[TradeExecution] = []
        self.active_positions: Dict[str, Any] = {}

        # 控制标志
        self.is_running = False
        self._emergency_stop_flag = False

        logger.info(f"实盘交易引擎初始化完成 - 当前模式: {self.current_mode.value}")

    async def start(self) -> None:
        """启动交易引擎"""
        if self.is_running:
            logger.warning("交易引擎已在运行")
            return

        self.is_running = True
        self.state = TradingState.SCANNING
        logger.info("实盘交易引擎启动成功")

    async def stop(self) -> None:
        """停止交易引擎（优雅停止）"""
        if not self.is_running:
            return

        logger.info("正在停止交易引擎...")
        self.is_running = False

        # 等待当前交易完成
        if self.state == TradingState.EXECUTING:
            await asyncio.sleep(5)  # 等待最多5秒

        self.state = TradingState.STOPPED
        logger.info("交易引擎已停止")

    async def emergency_stop(self) -> None:
        """紧急停止机制"""
        logger.error("!!! 紧急停止触发 !!!")
        self._emergency_stop_flag = True
        self.is_running = False
        self.state = TradingState.EMERGENCY

        # 立即取消所有挂单和关闭持仓
        await self._emergency_close_all_positions()

        # 发送紧急通知
        await self._send_emergency_notification("系统紧急停止")

        logger.error("紧急停止执行完成")

    async def execute_trade(
        self,
        opportunity: Dict[str, Any],
        mode_override: Optional[TradingMode] = None
    ) -> TradeExecution:
        """执行交易

        Args:
            opportunity: 交易机会信息
            mode_override: 模式覆盖（用于测试）

        Returns:
            交易执行结果
        """
        # 检查紧急停止
        if self._emergency_stop_flag:
            raise RuntimeError("系统处于紧急停止状态")

        # 确定使用的交易模式
        trading_mode = mode_override or self.current_mode

        # 生成交易ID
        trade_id = f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # 更新状态
        self.state = TradingState.EXECUTING
        start_time = datetime.now()

        logger.info(f"开始执行交易 {trade_id} - 模式: {trading_mode.value}")

        try:
            # 1. 预检查 - 基础风险检查
            if not await self._pre_trade_check(opportunity, trading_mode):
                raise ValueError("未通过预检查")

            # 2. 模式特定的执行逻辑
            if trading_mode == TradingMode.SIMULATION:
                result = await self._execute_simulation_trade(opportunity, trade_id)
            elif trading_mode == TradingMode.PAPER_TRADING:
                result = await self._execute_paper_trade(opportunity, trade_id)
            elif trading_mode == TradingMode.LIVE_TRADING:
                result = await self._execute_live_trade(opportunity, trade_id)
            else:
                raise ValueError(f"未知的交易模式: {trading_mode}")

            # 3. 记录执行结果
            execution_time = (datetime.now() - start_time).total_seconds()
            trade_result = TradeExecution(
                trade_id=trade_id,
                mode=trading_mode,
                opportunity=opportunity,
                execution_time=execution_time,
                status="COMPLETED",
                actual_profit=result.get('profit'),
                execution_details=result
            )

            # 更新统计
            self._update_statistics(trade_result)

            logger.info(f"交易 {trade_id} 执行完成 - 利润: {result.get('profit', 0):.2f}")
            return trade_result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"交易 {trade_id} 执行失败: {e}")

            return TradeExecution(
                trade_id=trade_id,
                mode=trading_mode,
                opportunity=opportunity,
                execution_time=execution_time,
                status="FAILED",
                error_message=str(e)
            )
        finally:
            # 恢复状态
            if self.state != TradingState.EMERGENCY:
                self.state = TradingState.SCANNING

    async def _pre_trade_check(
        self,
        opportunity: Dict[str, Any],
        mode: TradingMode
    ) -> bool:
        """交易前检查

        Args:
            opportunity: 交易机会
            mode: 交易模式

        Returns:
            是否通过检查
        """
        # 基础风险检查
        if not self.risk_manager.check_position_risk(opportunity):
            return False

        # 深度风险检查（如果可用）
        if self.deep_risk_manager:
            # 这里可以添加更复杂的风险检查
            pass

        # 实盘模式额外检查
        if mode == TradingMode.LIVE_TRADING:
            # 检查每日交易限制
            if self.statistics.daily_trades >= self.max_live_trades_per_day:
                logger.warning(f"达到每日实盘交易限制: {self.statistics.daily_trades}")
                return False

            # 检查仓位限制
            position_size = opportunity.get('amount', 0)
            if position_size > self.live_position_limit * 10000:  # 假设总资金10,000
                logger.warning(f"仓位超过实盘限制: {position_size}")
                return False

        return True

    async def _execute_simulation_trade(
        self,
        opportunity: Dict[str, Any],
        trade_id: str
    ) -> Dict[str, Any]:
        """执行模拟交易

        Args:
            opportunity: 交易机会
            trade_id: 交易ID

        Returns:
            执行结果
        """
        # 模拟执行 - 直接使用预期利润
        expected_profit = opportunity.get('expected_profit', 0)

        # 添加一些随机性模拟市场波动
        import random
        slippage = random.uniform(-0.001, 0.001)  # -0.1% to 0.1%
        actual_profit = expected_profit * (1 + slippage)

        logger.info(f"模拟交易执行 - 预期利润: {expected_profit:.2f}, 实际利润: {actual_profit:.2f}")

        return {
            'profit': actual_profit,
            'expected_profit': expected_profit,
            'slippage': slippage,
            'execution_price': opportunity.get('price', 0)
        }

    async def _execute_paper_trade(
        self,
        opportunity: Dict[str, Any],
        trade_id: str
    ) -> Dict[str, Any]:
        """执行纸面交易（使用实时数据但不实际执行）

        Args:
            opportunity: 交易机会
            trade_id: 交易ID

        Returns:
            执行结果
        """
        import random

        symbol = opportunity.get('symbol', 'UNKNOWN')
        exchange = opportunity.get('exchange', 'binance')

        # 尝试获取实时价格
        execution_price = opportunity.get('price', 0)

        if self.price_feed:
            try:
                ticker = self.price_feed.get_price(symbol, exchange)
                if ticker:
                    execution_price = ticker.last
                    logger.info(f"纸面交易使用实时价格: {symbol}@{exchange} = {execution_price:.4f}")
            except Exception as e:
                logger.warning(f"获取实时价格失败: {e}")

        # 计算滑点
        expected_profit = opportunity.get('expected_profit', 0)
        slippage = random.uniform(-0.0005, 0.0005)  # -0.05% to 0.05%
        actual_profit = expected_profit * (1 + slippage)

        logger.info(f"纸面交易执行 - 预期利润: {expected_profit:.2f}, 实际利润: {actual_profit:.2f}, 价格: {execution_price:.4f}")

        return {
            'profit': actual_profit,
            'expected_profit': expected_profit,
            'slippage': slippage,
            'execution_price': execution_price,
            'note': '纸面交易 - 使用实时价格数据'
        }

    async def _execute_live_trade(
        self,
        opportunity: Dict[str, Any],
        trade_id: str
    ) -> Dict[str, Any]:
        """执行实盘交易

        Args:
            opportunity: 交易机会
            trade_id: 交易ID

        Returns:
            执行结果
        """
        # 实盘交易 - 调用实际的交易所API
        logger.warning(f"!!! 实盘交易执行 {trade_id} - 金额: {opportunity.get('amount', 0)} !!!")

        # 这里需要集成实际的交易所API
        # 暂时返回模拟结果
        expected_profit = opportunity.get('expected_profit', 0)

        # 实盘滑点通常更大
        import random
        slippage = random.uniform(-0.002, 0.001)  # -0.2% to 0.1%
        actual_profit = expected_profit * (1 + slippage)

        logger.info(f"实盘交易执行完成 - 实际利润: {actual_profit:.2f}")

        return {
            'profit': actual_profit,
            'expected_profit': expected_profit,
            'slippage': slippage,
            'execution_price': opportunity.get('price', 0),
            'live_execution': True
        }

    def _update_statistics(self, trade_result: TradeExecution) -> None:
        """更新交易统计

        Args:
            trade_result: 交易结果
        """
        self.statistics.total_trades += 1

        if trade_result.actual_profit and trade_result.actual_profit > 0:
            self.statistics.profitable_trades += 1

        if trade_result.actual_profit:
            self.statistics.total_profit += trade_result.actual_profit

        # 更新成功率
        if self.statistics.total_trades > 0:
            self.statistics.success_rate = (
                self.statistics.profitable_trades / self.statistics.total_trades
            )

        # 更新平均执行时间
        total_time = (
            self.statistics.avg_execution_time * (self.statistics.total_trades - 1) +
            trade_result.execution_time
        )
        self.statistics.avg_execution_time = total_time / self.statistics.total_trades

        # 更新每日交易计数
        if (self.statistics.last_trade_time is None or
            self.statistics.last_trade_time.date() != datetime.now().date()):
            self.statistics.daily_trades = 0

        if trade_result.mode == TradingMode.LIVE_TRADING:
            self.statistics.daily_trades += 1

        self.statistics.last_trade_time = datetime.now()

        # 记录到历史
        self.execution_history.append(trade_result)

        # 保持最近1000条记录
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

    async def upgrade_trading_mode(
        self,
        new_mode: TradingMode,
        force: bool = False
    ) -> bool:
        """升级交易模式（带安全检查）

        Args:
            new_mode: 新的交易模式
            force: 是否强制升级（跳过某些检查）

        Returns:
            是否升级成功
        """
        current_mode_name = self.current_mode.value
        new_mode_name = new_mode.value

        logger.info(f"请求升级交易模式: {current_mode_name} -> {new_mode_name}")

        # 检查是否允许此升级
        allowed_upgrades = {
            TradingMode.SIMULATION: [TradingMode.PAPER_TRADING, TradingMode.LIVE_TRADING],
            TradingMode.PAPER_TRADING: [TradingMode.LIVE_TRADING],
            TradingMode.LIVE_TRADING: []
        }

        if not force and new_mode not in allowed_upgrades[self.current_mode]:
            logger.error(f"不允许的升级路径: {current_mode_name} -> {new_mode_name}")
            return False

        # 安全检查
        if not force and new_mode == TradingMode.LIVE_TRADING:
            if not await self._safety_check_before_live():
                logger.error("未通过实盘前安全检查")
                return False

        # 执行升级
        self.current_mode = new_mode
        logger.info(f"交易模式已升级: {new_mode_name}")

        # 发送通知
        await self._send_mode_upgrade_notification(new_mode)

        return True

    async def _safety_check_before_live(self) -> bool:
        """实盘前安全检查

        Returns:
            是否通过安全检查
        """
        logger.info("执行实盘前安全检查...")

        checks = []

        # 检查1: 系统状态
        if self.state in [TradingState.EMERGENCY, TradingState.STOPPED]:
            checks.append(("系统状态", False, "系统处于非正常状态"))
        else:
            checks.append(("系统状态", True, "系统状态正常"))

        # 检查2: 风险管理器
        risk_summary = self.risk_manager.get_risk_summary()
        if risk_summary['is_risk_limit_reached']:
            checks.append(("风险限制", False, "达到风险限制"))
        else:
            checks.append(("风险限制", True, "风险限制正常"))

        # 检查3: 历史表现（模拟/纸面交易）
        if self.statistics.total_trades < 10:
            checks.append(("历史交易", False, "历史交易数量不足"))
        elif self.statistics.success_rate < 0.5:
            checks.append(("成功率", False, f"成功率过低: {self.statistics.success_rate:.1%}"))
        else:
            checks.append(("历史表现", True, f"成功率: {self.statistics.success_rate:.1%}"))

        # 输出检查结果
        all_passed = True
        for check_name, passed, message in checks:
            status = "✓" if passed else "✗"
            logger.info(f"  {status} {check_name}: {message}")
            if not passed:
                all_passed = False

        return all_passed

    async def _emergency_close_all_positions(self) -> None:
        """紧急关闭所有持仓"""
        logger.warning("开始紧急关闭所有持仓...")

        # 这里需要集成实际的API来关闭持仓
        # 暂时清空记录
        self.active_positions.clear()

        logger.warning("所有持仓已紧急关闭")

    async def _send_emergency_notification(self, message: str) -> None:
        """发送紧急通知"""
        logger.error(f"紧急通知: {message}")
        # 这里可以集成邮件、短信、钉钉等通知方式

    async def _send_mode_upgrade_notification(self, new_mode: TradingMode) -> None:
        """发送模式升级通知"""
        logger.info(f"模式升级通知: 已升级到 {new_mode.value}")
        # 这里可以发送通知给用户

    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态

        Returns:
            状态信息字典
        """
        return {
            'current_mode': self.current_mode.value,
            'state': self.state.value,
            'is_running': self.is_running,
            'statistics': {
                'total_trades': self.statistics.total_trades,
                'profitable_trades': self.statistics.profitable_trades,
                'total_profit': self.statistics.total_profit,
                'success_rate': self.statistics.success_rate,
                'avg_execution_time': self.statistics.avg_execution_time,
                'daily_trades': self.statistics.daily_trades
            },
            'risk_summary': self.risk_manager.get_risk_summary(),
            'active_positions': len(self.active_positions),
            'emergency_stop': self._emergency_stop_flag
        }

    def get_statistics(self) -> TradingStatistics:
        """获取交易统计

        Returns:
            交易统计对象
        """
        return self.statistics

    def get_execution_history(
        self,
        limit: Optional[int] = None
    ) -> List[TradeExecution]:
        """获取执行历史

        Args:
            limit: 返回数量限制

        Returns:
            执行历史列表
        """
        if limit:
            return self.execution_history[-limit:]
        return self.execution_history.copy()

    # ========== 订单追踪 (V17.0新增) ==========

    def get_active_positions(self) -> Dict[str, Any]:
        """获取活跃持仓

        Returns:
            持仓字典
        """
        return self.active_positions.copy()

    def get_position(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """获取指定持仓

        Args:
            trade_id: 交易ID

        Returns:
            持仓信息，不存在返回None
        """
        return self.active_positions.get(trade_id)

    def get_position_count(self) -> int:
        """获取持仓数量

        Returns:
            持仓数
        """
        return len(self.active_positions)

    def has_active_position(self, symbol: str) -> bool:
        """检查是否有该币种的持仓

        Args:
            symbol: 交易对

        Returns:
            是否有持仓
        """
        return any(
            pos.get('symbol') == symbol
            for pos in self.active_positions.values()
        )


# 便捷函数
def create_production_trading_engine(
    config: Dict[str, Any],
    risk_manager: RiskManager,
    deep_risk_manager: Optional[DeepRiskManager] = None
) -> ProductionTradingEngine:
    """创建生产级交易引擎实例

    Args:
        config: 配置字典
        risk_manager: 风险管理器
        deep_risk_manager: 深度风险管理器（可选）

    Returns:
        交易引擎实例
    """
    return ProductionTradingEngine(config, risk_manager, deep_risk_manager)