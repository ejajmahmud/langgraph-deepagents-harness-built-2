"""网格交易策略 V36.0 - Grid Trading System

V36.0 核心功能：
1. Grid Trading - 网格交易策略
2. DCA Bot - 定时定额投资策略
3. Backtest Engine - 回测引擎
4. Performance Analytics - 性能分析增强

创建时间：2026-05-07 22:50
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class GridOrderType(Enum):
    """网格订单类型"""
    BUY = "buy"
    SELL = "sell"
    CLOSE = "close"


class GridStatus(Enum):
    """网格状态"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DCAMode(Enum):
    """DCA模式"""
    FIXED_AMOUNT = "fixed_amount"  # 固定金额
    FIXED_INTERVAL = "fixed_interval"  # 固定间隔
    VARIABLE_AMOUNT = "variable_amount"  # 可变金额
    Martingale = "martingale"  # 马丁格尔


@dataclass
class GridLevel:
    """网格级别

    Attributes:
        level_id: 级别ID
        price: 价格
        order_type: 订单类型
        filled: 是否已成交
        filled_price: 成交价格
        filled_time: 成交时间
    """
    level_id: int
    price: float
    order_type: GridOrderType
    filled: bool = False
    filled_price: float = 0.0
    filled_time: float = 0.0
    quantity: float = 0.0


@dataclass
class GridPosition:
    """网格持仓

    Attributes:
        position_id: 持仓ID
        symbol: 交易对
        grid_levels: 网格级别列表
        total_invested: 总投资额
        total_quantity: 总数量
        average_price: 平均价格
        current_profit: 当前盈亏
        status: 持仓状态
    """
    position_id: str
    symbol: str
    grid_levels: List[GridLevel] = field(default_factory=list)
    total_invested: float = 0.0
    total_quantity: float = 0.0
    average_price: float = 0.0
    current_profit: float = 0.0
    status: GridStatus = GridStatus.ACTIVE
    open_time: float = field(default_factory=time.time)


@dataclass
class DCAPlan:
    """DCA定投计划

    Attributes:
        plan_id: 计划ID
        symbol: 交易对
        mode: DCA模式
        amount: 投资金额
        interval: 投资间隔(秒)
        max_investments: 最大投资次数
        completed_investments: 已完成投资次数
        total_invested: 总投资额
        status: 状态
    """
    plan_id: str
    symbol: str
    mode: DCAMode
    amount: float
    interval: int
    max_investments: int
    completed_investments: int = 0
    total_invested: float = 0.0
    status: GridStatus = GridStatus.ACTIVE
    next_investment_time: float = 0.0


@dataclass
class GridBacktestResult:
    """网格回测结果

    Attributes:
        strategy_name: 策略名称
        symbol: 交易对
        start_price: 起始价格
        end_price: 结束价格
        total_invested: 总投资额
        final_value: 最终价值
        total_profit: 总利润
        profit_rate: 收益率(%)
        max_drawdown: 最大回撤(%)
        total_trades: 交易次数
        win_rate: 胜率(%)
        sharpe_ratio: 夏普比率
    """
    strategy_name: str
    symbol: str
    start_price: float
    end_price: float
    total_invested: float
    final_value: float
    total_profit: float
    profit_rate: float
    max_drawdown: float
    total_trades: int
    win_rate: float
    sharpe_ratio: float = 0.0
    duration: float = 0.0
    timestamp: float = field(default_factory=time.time)


class GridTradingStrategy:
    """网格交易策略 V36.0

    核心功能：
    1. 网格订单管理 - 在价格区间内创建多个买卖订单
    2. 自动补仓 - 价格下跌时自动买入
    3. 止盈止损 - 自动卖出获利
    4. 网格重置 - 价格突破网格时重置

    用法示例:
        strategy = GridTradingStrategy({
            'symbol': 'BTC/USDT',
            'lower_price': 45000,
            'upper_price': 55000,
            'grid_count': 10,
            'investment_per_grid': 100,
            'profit_target': 0.5  # 每格利润目标(%)
        })
    """

    STRATEGY_NAME = "Grid Trading V36.0"
    STRATEGY_DESCRIPTION = "网格交易策略"

    def __init__(self, config: Dict[str, Any]):
        """初始化网格交易策略

        Args:
            config: 配置字典
                - symbol: 交易对 (如 'BTC/USDT')
                - lower_price: 下限价格
                - upper_price: 上限价格
                - grid_count: 网格数量
                - investment_per_grid: 每格投资金额
                - profit_target: 利润目标(%)
                - stop_loss: 止损(%)
                - enable_dca: 启用DCA
        """
        self.config = config
        self.symbol = config.get('symbol', 'BTC/USDT')
        self.lower_price = config.get('lower_price', 45000)
        self.upper_price = config.get('upper_price', 55000)
        self.grid_count = config.get('grid_count', 10)
        self.investment_per_grid = config.get('investment_per_grid', 100)
        self.profit_target = config.get('profit_target', 0.5)
        self.stop_loss = config.get('stop_loss', 10.0)
        self.enable_dca = config.get('enable_dca', False)

        # 验证配置
        if self.lower_price >= self.upper_price:
            raise ValueError("下限价格必须小于上限价格")
        if self.grid_count < 2:
            raise ValueError("网格数量必须 >= 2")

        # 计算网格间距
        self.grid_spacing = (self.upper_price - self.lower_price) / (self.grid_count - 1)

        # 生成网格价格
        self.grid_prices = [
            self.lower_price + i * self.grid_spacing
            for i in range(self.grid_count)
        ]

        # 持仓管理
        self.positions: List[GridPosition] = []
        self.active_grids: Dict[int, GridLevel] = {}

        # 性能统计
        self.total_invested = 0.0
        self.total_quantity = 0.0  # 添加总数量
        self.total_profit = 0.0
        self.total_trades = 0
        self.wins = 0
        self.losses = 0

        # 状态
        self.is_running = False
        self.is_paused = False

        # DCA计划
        self.dca_plans: List[DCAPlan] = []

        logger.info(f"[OK] GridTradingStrategy V36.0 初始化完成")
        logger.info(f"     交易对: {self.symbol}")
        logger.info(f"     价格区间: {self.lower_price} - {self.upper_price}")
        logger.info(f"     网格数量: {self.grid_count}")
        logger.info(f"     网格间距: {self.grid_spacing:.2f}")

    def create_grid_levels(self) -> List[GridLevel]:
        """创建网格级别

        Returns:
            网格级别列表
        """
        levels = []
        for i in range(self.grid_count):
            # 偶数层买单，奇数层卖单
            order_type = GridOrderType.BUY if i % 2 == 0 else GridOrderType.SELL

            level = GridLevel(
                level_id=i,
                price=self.grid_prices[i],
                order_type=order_type,
                filled=False
            )
            levels.append(level)
            self.active_grids[i] = level

        logger.info(f"[OK] 创建了 {len(levels)} 个网格级别")
        return levels

    def get_grid_index(self, price: float) -> int:
        """获取价格对应的网格索引

        Args:
            price: 价格

        Returns:
            网格索引
        """
        if price < self.lower_price:
            return 0
        if price >= self.upper_price:
            return self.grid_count - 1

        index = int((price - self.lower_price) / self.grid_spacing)
        return min(max(index, 0), self.grid_count - 1)

    def calculate_profit(self, entry_price: float, exit_price: float) -> float:
        """计算利润

        Args:
            entry_price: 入场价
            exit_price: 出场价

        Returns:
            利润(%)
        """
        return ((exit_price - entry_price) / entry_price) * 100

    def calculate_position_profit(self, position: GridPosition, current_price: float) -> float:
        """计算持仓盈亏

        Args:
            position: 持仓
            current_price: 当前价格

        Returns:
            盈亏金额
        """
        if position.total_quantity == 0:
            return 0.0

        current_value = position.total_quantity * current_price
        profit = current_value - position.total_invested
        return profit

    def should_take_profit(self, position: GridPosition, current_price: float) -> bool:
        """检查是否应该止盈

        Args:
            position: 持仓
            current_price: 当前价格

        Returns:
            是否止盈
        """
        if position.average_price == 0:
            return False

        profit_rate = self.calculate_profit(position.average_price, current_price)
        return profit_rate >= self.profit_target

    def should_stop_loss(self, position: GridPosition, current_price: float) -> bool:
        """检查是否应该止损

        Args:
            position: 持仓
            current_price: 当前价格

        Returns:
            是否止损
        """
        if position.average_price == 0:
            return False

        profit_rate = self.calculate_profit(position.average_price, current_price)
        return profit_rate <= -self.stop_loss

    def execute_grid_order(self, level: GridLevel, execution_price: float) -> bool:
        """执行网格订单

        Args:
            level: 网格级别
            execution_price: 执行价格

        Returns:
            执行是否成功
        """
        try:
            level.filled = True
            level.filled_price = execution_price
            level.filled_time = time.time()
            level.filled_price = execution_price

            # 计算购买的币数量
            level.quantity = self.investment_per_grid / execution_price

            self.total_trades += 1

            # 移出活跃网格
            if level.level_id in self.active_grids:
                del self.active_grids[level.level_id]

            logger.info(f"[OK] 网格订单执行: 级别={level.level_id}, 价格={execution_price}")
            return True

        except Exception as e:
            logger.error(f"网格订单执行失败: {e}")
            return False

    def add_position(self, symbol: str) -> GridPosition:
        """添加新持仓

        Args:
            symbol: 交易对

        Returns:
            新持仓
        """
        position = GridPosition(
            position_id=f"grid_{int(time.time()*1000)}",
            symbol=symbol,
            grid_levels=self.create_grid_levels(),
            open_time=time.time()
        )
        self.positions.append(position)

        logger.info(f"[OK] 创建新持仓: {position.position_id}")
        return position

    def close_position(self, position: GridPosition, exit_price: float) -> float:
        """平仓

        Args:
            position: 持仓
            exit_price: 出场价格

        Returns:
            盈亏金额
        """
        try:
            # 计算最终价值
            final_value = position.total_quantity * exit_price
            profit = final_value - position.total_invested

            # 更新统计
            if profit > 0:
                self.wins += 1
            else:
                self.losses += 1

            self.total_profit += profit
            position.current_profit = profit
            position.status = GridStatus.COMPLETED

            logger.info(f"[OK] 平仓完成: 盈亏={profit:.2f}")
            return profit

        except Exception as e:
            logger.error(f"平仓失败: {e}")
            return 0.0

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计

        Returns:
            性能统计字典
        """
        win_rate = (self.wins / self.total_trades * 100) if self.total_trades > 0 else 0

        return {
            'strategy': self.STRATEGY_NAME,
            'symbol': self.symbol,
            'total_invested': self.total_invested,
            'total_profit': self.total_profit,
            'total_trades': self.total_trades,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': win_rate,
            'active_positions': len([p for p in self.positions if p.status == GridStatus.ACTIVE]),
            'active_grids': len(self.active_grids)
        }

    def start(self) -> bool:
        """启动策略

        Returns:
            是否成功
        """
        if self.is_running:
            logger.warning("策略已在运行")
            return False

        self.is_running = True
        self.is_paused = False
        logger.info(f"[OK] {self.STRATEGY_NAME} 启动")
        return True

    def stop(self) -> bool:
        """停止策略

        Returns:
            是否成功
        """
        if not self.is_running:
            logger.warning("策略未在运行")
            return False

        self.is_running = False

        # 平所有活跃持仓
        for position in self.positions:
            if position.status == GridStatus.ACTIVE:
                position.status = GridStatus.CANCELLED

        logger.info(f"[OK] {self.STRATEGY_NAME} 停止")
        return True

    def pause(self) -> bool:
        """暂停策略

        Returns:
            是否成功
        """
        if not self.is_running:
            return False

        self.is_paused = True
        logger.info(f"[OK] {self.STRATEGY_NAME} 暂停")
        return True

    def resume(self) -> bool:
        """恢复策略

        Returns:
            是否成功
        """
        if not self.is_paused:
            return False

        self.is_paused = False
        logger.info(f"[OK] {self.STRATEGY_NAME} 恢复")
        return True


class DCABot:
    """DCA定时定额投资机器人 V36.0

    核心功能：
    1. 固定金额定投 - 每次投入相同金额
    2. 固定间隔定投 - 按设定时间间隔投入
    3. 马丁格尔策略 - 亏损时加倍投入
    4. 自动复投 - 利润自动再投资

    用法示例:
        bot = DCABot({
            'symbol': 'BTC/USDT',
            'mode': 'fixed_amount',
            'amount': 100,
            'interval': 86400,  # 每天
            'max_investments': 30
        })
    """

    STRATEGY_NAME = "DCA Bot V36.0"

    def __init__(self, config: Dict[str, Any]):
        """初始化DCA机器人

        Args:
            config: 配置字典
                - symbol: 交易对
                - mode: DCA模式
                - amount: 投资金额
                - interval: 投资间隔(秒)
                - max_investments: 最大投资次数
                - martingale_multiplier: 马丁格尔倍数
                - martingale_max: 最大倍数
        """
        self.config = config
        self.symbol = config.get('symbol', 'BTC/USDT')
        self.mode = DCAMode(config.get('mode', 'fixed_amount'))
        self.base_amount = config.get('amount', 100)
        self.interval = config.get('interval', 86400)
        self.max_investments = config.get('max_investments', 30)
        self.martingale_multiplier = config.get('martingale_multiplier', 2.0)
        self.martingale_max = config.get('martingale_max', 8.0)

        # 状态
        self.is_running = False
        self.total_invested = 0.0
        self.total_quantity = 0.0
        self.completed_investments = 0
        self.average_price = 0.0

        # 马丁格尔状态
        self.current_multiplier = 1.0
        self.consecutive_losses = 0

        logger.info(f"[OK] DCABot V36.0 初始化完成")
        logger.info(f"     交易对: {self.symbol}")
        logger.info(f"     模式: {self.mode.value}")
        logger.info(f"     投资金额: {self.base_amount}")
        logger.info(f"     间隔: {self.interval}秒")

    def calculate_investment_amount(self) -> float:
        """计算下次投资金额

        Returns:
            投资金额
        """
        if self.mode == DCAMode.FIXED_AMOUNT:
            return self.base_amount

        elif self.mode == DCAMode.Martingale:
            amount = self.base_amount * self.current_multiplier

            # 限制最大倍数
            if self.current_multiplier < self.martingale_max:
                return amount
            else:
                return self.base_amount * self.martingale_max

        return self.base_amount

    def record_investment(self, amount: float, price: float) -> bool:
        """记录投资

        Args:
            amount: 投资金额
            price: 价格

        Returns:
            是否成功
        """
        try:
            quantity = amount / price

            self.total_invested += amount
            self.total_quantity += quantity
            self.completed_investments += 1

            # 更新平均价格
            if self.total_quantity > 0:
                self.average_price = self.total_invested / self.total_quantity

            logger.info(f"[OK] 记录投资: 金额={amount}, 价格={price}, 数量={quantity}")
            return True

        except Exception as e:
            logger.error(f"记录投资失败: {e}")
            return False

    def on_profit(self) -> None:
        """盈利回调 - 重置马丁格尔倍数"""
        self.consecutive_losses = 0
        self.current_multiplier = 1.0

    def on_loss(self) -> None:
        """亏损回调 - 增加马丁格尔倍数"""
        self.consecutive_losses += 1

        if self.mode == DCAMode.Martingale:
            self.current_multiplier = min(
                self.current_multiplier * self.martingale_multiplier,
                self.martingale_max
            )

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计

        Returns:
            性能统计字典
        """
        current_value = self.total_quantity * self.average_price
        profit = current_value - self.total_invested
        profit_rate = (profit / self.total_invested * 100) if self.total_invested > 0 else 0

        return {
            'strategy': self.STRATEGY_NAME,
            'symbol': self.symbol,
            'total_invested': self.total_invested,
            'total_quantity': self.total_quantity,
            'average_price': self.average_price,
            'completed_investments': self.completed_investments,
            'profit': profit,
            'profit_rate': profit_rate
        }

    def start(self) -> bool:
        """启动机器人

        Returns:
            是否成功
        """
        if self.is_running:
            return False

        self.is_running = True
        logger.info(f"[OK] {self.STRATEGY_NAME} 启动")
        return True

    def stop(self) -> bool:
        """停止机器人

        Returns:
            是否成功
        """
        if not self.is_running:
            return False

        self.is_running = False
        logger.info(f"[OK] {self.STRATEGY_NAME} 停止")
        return True


class GridBacktester:
    """网格交易回测引擎 V36.0

    核心功能：
    1. 历史数据回测
    2. 参数优化
    3. 性能指标计算
    4. 蒙特卡洛模拟

    用法示例:
        backtester = GridBacktester()
        result = backtester.run_backtest({
            'symbol': 'BTC/USDT',
            'prices': [45000, 46000, 47000, ...],
            'lower_price': 45000,
            'upper_price': 55000,
            'grid_count': 10,
            'investment_per_grid': 100
        })
    """

    STRATEGY_NAME = "Grid Backtest V36.0"

    def __init__(self):
        """初始化回测引擎"""
        self.results: List[GridBacktestResult] = []
        logger.info(f"[OK] GridBacktester V36.0 初始化完成")

    def run_backtest(self, config: Dict[str, Any]) -> GridBacktestResult:
        """运行回测

        Args:
            config: 配置字典
                - symbol: 交易对
                - prices: 价格历史
                - lower_price: 下限价格
                - upper_price: 上限价格
                - grid_count: 网格数量
                - investment_per_grid: 每格投资
                - profit_target: 利润目标

        Returns:
            回测结果
        """
        symbol = config.get('symbol', 'BTC/USDT')
        prices = config.get('prices', [])

        if not prices:
            raise ValueError("价格历史为空")

        # 初始化网格策略
        strategy = GridTradingStrategy(config)

        # 模拟交易
        positions = []
        current_position = None

        for i, price in enumerate(prices):
            if current_position is None:
                current_position = strategy.add_position(symbol)

            # 检查网格触发
            for level in current_position.grid_levels:
                if not level.filled:
                    # 买单触发
                    if level.order_type == GridOrderType.BUY and price <= level.price:
                        strategy.execute_grid_order(level, price)
                    # 卖单触发
                    elif level.order_type == GridOrderType.SELL and price >= level.price:
                        strategy.execute_grid_order(level, price)

            # 检查止盈止损
            if current_position and current_position.total_quantity > 0:
                profit_rate = strategy.calculate_profit(
                    current_position.average_price, price
                )

                # 止盈
                if profit_rate >= config.get('profit_target', 0.5):
                    profit = strategy.close_position(current_position, price)
                    positions.append(profit)
                    current_position = None

                # 止损
                elif profit_rate <= -config.get('stop_loss', 10.0):
                    profit = strategy.close_position(current_position, price)
                    positions.append(profit)
                    current_position = None

        # 计算结果
        total_invested = strategy.total_invested
        total_trades = strategy.total_trades
        wins = strategy.wins
        losses = strategy.losses

        # 计算最终价值
        total_quantity = strategy.total_quantity if hasattr(strategy, 'total_quantity') else 0
        final_price = prices[-1] if prices else 0
        final_value = total_quantity * final_price
        total_profit = final_value - total_invested

        # 计算最大回撤
        max_price = max(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_drawdown = ((max_price - min_price) / max_price * 100) if max_price > 0 else 0

        # 计算夏普比率
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)

        sharpe = 0.0
        if returns:
            mean_ret = np.mean(returns)
            std_ret = np.std(returns)
            if std_ret > 0:
                sharpe = mean_ret / std_ret * np.sqrt(252)

        result = GridBacktestResult(
            strategy_name=strategy.STRATEGY_NAME,
            symbol=symbol,
            start_price=prices[0] if prices else 0,
            end_price=final_price,
            total_invested=total_invested,
            final_value=final_value,
            total_profit=total_profit,
            profit_rate=(total_profit / total_invested * 100) if total_invested > 0 else 0,
            max_drawdown=max_drawdown,
            total_trades=total_trades,
            win_rate=(wins / total_trades * 100) if total_trades > 0 else 0,
            sharpe_ratio=sharpe,
            duration=len(prices)
        )

        self.results.append(result)

        logger.info(f"[OK] 回测完成: 收益率={result.profit_rate:.2f}%, 胜率={result.win_rate:.2f}%")

        return result

    def optimize_parameters(self, config: Dict[str, Any], param_range: Dict[str, List]) -> Dict[str, Any]:
        """参数优化

        Args:
            config: 基础配置
            param_range: 参数范围
                - grid_count: [5, 10, 15, 20]
                - profit_target: [0.3, 0.5, 0.8, 1.0]

        Returns:
            最优参数
        """
        best_params = config.copy()
        best_result = None
        best_score = -float('inf')

        # 简单网格搜索
        import itertools

        keys = list(param_range.keys())
        values = list(param_range.values())

        for combination in itertools.product(*values):
            params = best_params.copy()
            for key, value in zip(keys, combination):
                params[key] = value

            try:
                result = self.run_backtest(params)
                score = result.profit_rate - result.max_drawdown * 0.5

                if score > best_score:
                    best_score = score
                    best_result = result
                    best_params = params.copy()

            except Exception as e:
                logger.warning(f"参数组合失败: {combination}, {e}")

        logger.info(f"[OK] 参数优化完成: 最优收益={best_result.profit_rate:.2f}%")
        return best_params

    def monte_carlo_simulation(self, config: Dict[str, Any], n_sims: int = 100) -> Dict[str, Any]:
        """蒙特卡洛模拟

        Args:
            config: 配置
            n_sims: 模拟次数

        Returns:
            模拟结果统计
        """
        results = []

        for _ in range(n_sims):
            try:
                result = self.run_backtest(config)
                results.append(result.profit_rate)
            except Exception as e:
                logger.warning(f"模拟失败: {e}")

        if not results:
            return {'mean': 0, 'std': 0, 'percentile_5': 0, 'percentile_95': 0}

        results_array = np.array(results)

        return {
            'mean': float(np.mean(results_array)),
            'std': float(np.std(results_array)),
            'min': float(np.min(results_array)),
            'max': float(np.max(results_array)),
            'percentile_5': float(np.percentile(results_array, 5)),
            'percentile_95': float(np.percentile(results_array, 95)),
            'n_sims': len(results)
        }


# 工厂函数
def create_grid_trading_strategy(config: Dict[str, Any]) -> GridTradingStrategy:
    """创建网格交易策略

    Args:
        config: 配置字典

    Returns:
        网格交易策略实例
    """
    return GridTradingStrategy(config)


def create_dca_bot(config: Dict[str, Any]) -> DCABot:
    """创建DCA机器人

    Args:
        config: 配置字典

    Returns:
        DCA机器人实例
    """
    return DCABot(config)


def create_grid_backtester() -> GridBacktester:
    """创建回测引擎

    Returns:
        回测引擎实例
    """
    return GridBacktester()


__all__ = [
    'GridOrderType',
    'GridStatus',
    'DCAMode',
    'GridLevel',
    'GridPosition',
    'DCAPlan',
    'GridBacktestResult',
    'GridTradingStrategy',
    'DCABot',
    'GridBacktester',
    'create_grid_trading_strategy',
    'create_dca_bot',
    'create_grid_backtester',
]