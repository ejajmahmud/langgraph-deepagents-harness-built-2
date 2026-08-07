"""资金费率套利引擎 V16.5

捕获永续合约资金费率异常，通过同时持有现货多头和永续合约空头（或反之），
赚取资金费率收益，同时保持delta中性（市场风险对冲）。

核心原理：
1. 当资金费率为正时，多头支付给空头 — 做空永续+做多现货赚取费率
2. 当资金费率为负时，空头支付给多头 — 做多永续+做空现货赚取费率
3. 现货和合约头寸对冲，价格波动风险极低
4. 收益来源：资金费率收入 - 交易手续费 - 滑点 - 基差变化

核心能力：
1. 资金费率监控 — 多交易所多币种实时费率扫描
2. 年化收益计算 — 费率 → 8小时收益 → 年化收益
3. 基差跟踪 — 合约价格 vs 现货价格的基差分析
4. Delta中性执行 — 现货+合约对冲开仓/平仓
5. 成本模型 — 手续费/滑点/资金成本精确计算
6. 知识闭环 — 交易结果反馈到知识库

架构位置:
    CcxtPriceFeed ─→ FundingRateEngine ─→ ArbitragePipeline (V16.5)
                            ↕
                    Memo0 Knowledge Base

创建时间：2026-05-05
"""

import logging
import math
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FundingDirection(Enum):
    """资金费率方向"""
    POSITIVE = "positive"   # 多付空 → 做空合约+做多现货
    NEGATIVE = "negative"   # 空付多 → 做多合约+做空现货
    NEUTRAL = "neutral"     # 接近零，无套利空间


class PositionSide(Enum):
    """持仓方向"""
    SHORT_PERP_LONG_SPOT = "short_perp_long_spot"  # 做空永续+做多现货
    LONG_PERP_SHORT_SPOT = "long_perp_short_spot"   # 做多永续+做空现货


@dataclass
class FundingRateSnapshot:
    """资金费率快照"""
    symbol: str
    exchange: str
    funding_rate: float          # 当前资金费率 (如 0.0001 = 0.01%)
    next_funding_time: float     # 下次结算时间戳
    mark_price: float            # 标记价格（永续合约）
    index_price: float           # 指数价格（现货参考）
    basis_pct: float             # 基差百分比 (mark - index) / index * 100
    annualized_rate: float       # 年化费率
    direction: FundingDirection  # 费率方向
    timestamp: float = 0.0
    is_simulated: bool = True

    @property
    def eight_hour_yield(self) -> float:
        """8小时收益率"""
        return self.funding_rate * 100

    @property
    def daily_yield(self) -> float:
        """日收益率（假设每日3次结算）"""
        return self.funding_rate * 3 * 100

    @property
    def annualized_yield(self) -> float:
        """年化收益率"""
        return self.funding_rate * 3 * 365 * 100


@dataclass
class FundingRateCost:
    """资金费率套利成本模型"""
    spot_taker_fee: float = 0.001          # 现货买入手续费 0.1%
    perp_taker_fee: float = 0.0006         # 永续合约手续费 0.06%
    spot_slippage: float = 0.0002          # 现货滑点 0.02%
    perp_slippage: float = 0.0002          # 合约滑点 0.02%
    # 开仓+平仓各一笔 = 4笔交易
    # total_open_cost = spot_taker + perp_taker + spot_slippage + perp_slippage
    # total_close_cost = same
    # total_cost = total_open_cost * 2

    @property
    def total_open_cost_pct(self) -> float:
        """开仓总成本百分比"""
        return (self.spot_taker_fee + self.perp_taker_fee +
                self.spot_slippage + self.perp_slippage) * 100

    @property
    def total_close_cost_pct(self) -> float:
        """平仓总成本百分比"""
        return self.total_open_cost_pct

    @property
    def total_round_trip_cost_pct(self) -> float:
        """往返总成本百分比"""
        return self.total_open_cost_pct + self.total_close_cost_pct

    def calculate_break_even_funding(self, settlement_count: int = 3) -> float:
        """计算盈亏平衡资金费率

        Args:
            settlement_count: 持仓期间的结算次数

        Returns:
            盈亏平衡所需的最小费率
        """
        # 每次结算需要覆盖: total_round_trip_cost / settlement_count
        return (self.total_round_trip_cost_pct / 100) / settlement_count


@dataclass
class FundingRatePosition:
    """资金费率套利持仓"""
    position_id: str
    symbol: str
    exchange: str
    side: PositionSide
    spot_price: float            # 现货入场价
    perp_price: float            # 合约入场价
    quantity: float              # 数量
    position_value_usd: float    # 持仓价值
    entry_funding_rate: float    # 入场时资金费率
    entry_basis_pct: float       # 入场时基差
    target_settlements: int      # 目标结算次数
    settlements_collected: int   # 已收取结算次数
    accumulated_funding_usd: float  # 累计资金费收入
    status: str = "open"         # open / closing / closed
    opened_at: float = 0.0
    closed_at: float = 0.0
    close_reason: str = ""
    exit_spot_price: float = 0.0
    exit_perp_price: float = 0.0
    realized_pnl_usd: float = 0.0
    realized_pnl_pct: float = 0.0
    knowledge_recorded: bool = False


@dataclass
class FundingRateSignal:
    """资金费率套利信号"""
    signal_id: str
    symbol: str
    exchange: str
    funding_rate: float
    annualized_yield: float
    direction: FundingDirection
    side: PositionSide
    confidence: float
    estimated_net_apy: float     # 扣除成本后的净年化收益
    settlement_count_target: int # 建议持仓结算次数
    cost_breakdown: Dict[str, float] = field(default_factory=dict)
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class FundingRateEngine:
    """资金费率套利引擎 V16.5

    捕获永续合约资金费率异常，
    通过delta中性策略赚取资金费率收益。
    """

    # 默认监控币种
    DEFAULT_SYMBOLS = [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT",
        "XRP/USDT", "ADA/USDT", "DOGE/USDT", "AVAX/USDT"
    ]

    DEFAULT_EXCHANGES = ["binance", "okex", "bybit"]

    # 模拟资金费率基准（年化）
    SIMULATED_BASE_RATES = {
        "BTC/USDT": 0.0001,      # 0.01% per 8h → ~10.95% APY
        "ETH/USDT": 0.00012,     # 0.012% → ~13.14% APY
        "SOL/USDT": 0.00015,     # 0.015% → ~16.43% APY
        "BNB/USDT": 0.00008,     # 0.008% → ~8.76% APY
        "XRP/USDT": 0.00005,     # 0.005% → ~5.48% APY
        "ADA/USDT": 0.00006,     # 0.006% → ~6.57% APY
        "DOGE/USDT": 0.00003,    # 0.003% → ~3.29% APY
        "AVAX/USDT": 0.00010,    # 0.01% → ~10.95% APY
    }

    def __init__(
        self,
        knowledge_storage=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化资金费率套利引擎

        Args:
            knowledge_storage: 知识存储实例
            config: 配置字典
        """
        self._knowledge = knowledge_storage
        self.config = config or {}

        # 策略参数
        self.min_annualized_yield = self.config.get("min_annualized_yield", 5.0)  # 最低5% APY
        self.min_funding_rate = self.config.get("min_funding_rate", 0.00005)       # 最低0.005%
        self.max_position_per_symbol = self.config.get("max_position_per_symbol", 1)
        self.max_total_positions = self.config.get("max_total_positions", 5)
        self.position_size_usd = self.config.get("position_size_usd", 1000.0)
        self.default_settlements = self.config.get("default_settlements", 6)  # 默认持仓6次结算(2天)
        self.basis_threshold_pct = self.config.get("basis_threshold_pct", 0.5)  # 基差阈值

        # 成本模型
        self.cost_model = FundingRateCost()

        # 持仓管理
        self.positions: Dict[str, FundingRatePosition] = {}
        self.closed_positions: List[FundingRatePosition] = []

        # 费率缓存
        self._rate_cache: Dict[str, FundingRateSnapshot] = {}

        # 统计
        self.total_signals_generated = 0
        self.total_positions_opened = 0
        self.total_positions_closed = 0
        self.total_funding_collected = 0.0
        self.total_pnl = 0.0
        self.win_count = 0
        self.loss_count = 0

        logger.info(
            f"资金费率引擎 V16.5 初始化: "
            f"min_apy={self.min_annualized_yield}%, "
            f"max_pos={self.max_total_positions}, "
            f"size=${self.position_size_usd}"
        )

    def _get_knowledge(self):
        """延迟获取知识存储"""
        if self._knowledge is not None:
            return self._knowledge
        try:
            from storage.mem0_mock_storage import create_mock_mem0_storage
            storage = create_mock_mem0_storage({
                "user_id": "crypto-arbitrage-user",
                "agent_id": "funding-rate-engine-v16-5"
            })
            self._knowledge = storage
            return storage
        except Exception as e:
            logger.error(f"获取知识存储失败: {e}")
            return None

    def generate_simulated_rates(self) -> Dict[str, Dict[str, FundingRateSnapshot]]:
        """生成模拟资金费率数据

        Returns:
            {symbol: {exchange: FundingRateSnapshot}}
        """
        import random

        snapshots = {}
        current_time = time.time()

        for symbol in self.DEFAULT_SYMBOLS:
            snapshots[symbol] = {}
            base_rate = self.SIMULATED_BASE_RATES.get(symbol, 0.00005)

            for exchange in self.DEFAULT_EXCHANGES:
                # 模拟费率波动 (base ± 50%)
                rate_variation = random.uniform(-0.5, 0.5)
                funding_rate = base_rate * (1 + rate_variation)

                # 随机翻转方向（10%概率负费率）
                if random.random() < 0.1:
                    funding_rate = -abs(funding_rate)

                # 模拟价格
                base_prices = {
                    "BTC/USDT": 94500, "ETH/USDT": 3780,
                    "SOL/USDT": 175, "BNB/USDT": 625,
                    "XRP/USDT": 2.42, "ADA/USDT": 0.75,
                    "DOGE/USDT": 0.185, "AVAX/USDT": 38.5,
                }
                index_price = base_prices.get(symbol, 100)
                # 基差（合约通常略高于现货）
                basis = random.uniform(-0.1, 0.3)
                mark_price = index_price * (1 + basis / 100)

                # 方向
                if funding_rate > self.min_funding_rate:
                    direction = FundingDirection.POSITIVE
                elif funding_rate < -self.min_funding_rate:
                    direction = FundingDirection.NEGATIVE
                else:
                    direction = FundingDirection.NEUTRAL

                snapshot = FundingRateSnapshot(
                    symbol=symbol,
                    exchange=exchange,
                    funding_rate=funding_rate,
                    next_funding_time=current_time + 28800,  # 8小时后
                    mark_price=mark_price,
                    index_price=index_price,
                    basis_pct=basis,
                    annualized_rate=abs(funding_rate) * 3 * 365 * 100,
                    direction=direction,
                    timestamp=current_time,
                    is_simulated=True
                )

                snapshots[symbol][exchange] = snapshot
                self._rate_cache[f"{symbol}_{exchange}"] = snapshot

        return snapshots

    def scan_funding_rates(
        self,
        snapshots: Optional[Dict[str, Dict[str, FundingRateSnapshot]]] = None
    ) -> List[FundingRateSnapshot]:
        """扫描资金费率，筛选有套利价值的机会

        Args:
            snapshots: 费率快照（None则生成模拟数据）

        Returns:
            有套利价值的费率快照列表
        """
        if snapshots is None:
            snapshots = self.generate_simulated_rates()

        opportunities = []

        for symbol, exchange_rates in snapshots.items():
            for exchange, snapshot in exchange_rates.items():
                # 过滤：年化收益太低
                if snapshot.annualized_yield < self.min_annualized_yield:
                    continue

                # 过滤：基差太大（基差侵蚀利润）
                if abs(snapshot.basis_pct) > self.basis_threshold_pct:
                    continue

                # 过滤：方向不明确
                if snapshot.direction == FundingDirection.NEUTRAL:
                    continue

                opportunities.append(snapshot)

        # 按年化收益排序
        opportunities.sort(key=lambda x: x.annualized_yield, reverse=True)

        logger.info(
            f"资金费率扫描: {len(opportunities)}/{sum(len(v) for v in snapshots.values())} 个机会"
        )

        return opportunities

    def generate_signals(
        self,
        opportunities: Optional[List[FundingRateSnapshot]] = None
    ) -> List[FundingRateSignal]:
        """生成资金费率套利信号

        Args:
            opportunities: 筛选后的费率机会

        Returns:
            交易信号列表
        """
        if opportunities is None:
            opportunities = self.scan_funding_rates()

        signals = []

        for opp in opportunities:
            # 检查持仓限制
            if len(self.positions) >= self.max_total_positions:
                break

            # 检查同币种持仓限制
            same_symbol_count = sum(
                1 for p in self.positions.values()
                if p.symbol == opp.symbol and p.status == "open"
            )
            if same_symbol_count >= self.max_position_per_symbol:
                continue

            # 确定持仓方向
            if opp.direction == FundingDirection.POSITIVE:
                side = PositionSide.SHORT_PERP_LONG_SPOT
            else:
                side = PositionSide.LONG_PERM_SHORT_SPOT

            # 计算净年化收益（扣除成本）
            cost_per_settlement = self.cost_model.total_open_cost_pct
            settlements_to_break_even = math.ceil(
                self.cost_model.total_round_trip_cost_pct /
                max(opp.eight_hour_yield, 0.001)
            )
            # 建议至少持仓到盈亏平衡点+2次结算
            target_settlements = max(self.default_settlements, settlements_to_break_even + 2)

            # 净收益 = 总费率收入 - 开平仓成本
            gross_yield = opp.eight_hour_yield * target_settlements
            net_yield = gross_yield - self.cost_model.total_round_trip_cost_pct
            net_apy = (net_yield / target_settlements) * 3 * 365  # 年化

            # 置信度
            confidence = min(1.0, opp.annualized_yield / 20.0)  # 20% APY = 满置信度
            confidence *= (1.0 - abs(opp.basis_pct) / self.basis_threshold_pct * 0.3)

            # 净年化为负 → 跳过
            if net_apy < self.min_annualized_yield:
                continue

            signal = FundingRateSignal(
                signal_id=f"fr_{uuid.uuid4().hex[:8]}",
                symbol=opp.symbol,
                exchange=opp.exchange,
                funding_rate=opp.funding_rate,
                annualized_yield=opp.annualized_yield,
                direction=opp.direction,
                side=side,
                confidence=max(0.0, min(1.0, confidence)),
                estimated_net_apy=net_apy,
                settlement_count_target=target_settlements,
                cost_breakdown={
                    "open_cost_pct": self.cost_model.total_open_cost_pct,
                    "close_cost_pct": self.cost_model.total_close_cost_pct,
                    "round_trip_cost_pct": self.cost_model.total_round_trip_cost_pct,
                    "break_even_settlements": settlements_to_break_even,
                    "gross_yield_pct": gross_yield,
                    "net_yield_pct": net_yield,
                },
                timestamp=time.time(),
                metadata={
                    "mark_price": opp.mark_price,
                    "index_price": opp.index_price,
                    "basis_pct": opp.basis_pct,
                }
            )

            signals.append(signal)
            self.total_signals_generated += 1

        logger.info(f"资金费率信号: {len(signals)} 个")
        return signals

    def execute_signal(
        self,
        signal: FundingRateSignal,
        mode: str = "simulation"
    ) -> Optional[FundingRatePosition]:
        """执行资金费率套利信号

        Args:
            signal: 交易信号
            mode: 执行模式

        Returns:
            持仓记录
        """
        logger.info(
            f"执行资金费率套利: {signal.symbol} @ {signal.exchange} | "
            f"side={signal.side.value} | "
            f"funding_rate={signal.funding_rate:.6f} | "
            f"APY={signal.annualized_yield:.2f}%"
        )

        position = FundingRatePosition(
            position_id=f"fpos_{uuid.uuid4().hex[:8]}",
            symbol=signal.symbol,
            exchange=signal.exchange,
            side=signal.side,
            spot_price=signal.metadata.get("index_price", 0),
            perp_price=signal.metadata.get("mark_price", 0),
            quantity=self.position_size_usd / max(signal.metadata.get("index_price", 1), 0.001),
            position_value_usd=self.position_size_usd,
            entry_funding_rate=signal.funding_rate,
            entry_basis_pct=signal.metadata.get("basis_pct", 0),
            target_settlements=signal.settlement_count_target,
            settlements_collected=0,
            accumulated_funding_usd=0.0,
            status="open",
            opened_at=time.time()
        )

        self.positions[position.position_id] = position
        self.total_positions_opened += 1

        # 记录到知识库
        self._record_signal_to_knowledge(signal, position)

        return position

    def simulate_funding_settlement(
        self,
        position: FundingRatePosition,
        funding_rate: Optional[float] = None
    ) -> FundingRatePosition:
        """模拟资金费率结算

        每次结算，按当前资金费率计算收入。

        Args:
            position: 持仓
            funding_rate: 当前费率（None则用入场费率模拟）

        Returns:
            更新后的持仓
        """
        if position.status != "open":
            return position

        rate = funding_rate if funding_rate is not None else position.entry_funding_rate

        # 结算金额 = 持仓价值 × 资金费率
        settlement_usd = position.position_value_usd * abs(rate)

        # 如果方向对（正费率做空合约），收入为正
        if position.side == PositionSide.SHORT_PERP_LONG_SPOT:
            if rate > 0:
                position.accumulated_funding_usd += settlement_usd
            else:
                position.accumulated_funding_usd -= settlement_usd
        else:
            if rate < 0:
                position.accumulated_funding_usd += settlement_usd
            else:
                position.accumulated_funding_usd -= settlement_usd

        position.settlements_collected += 1
        self.total_funding_collected += max(0, settlement_usd)

        return position

    def check_positions_for_close(self) -> List[Tuple[FundingRatePosition, str]]:
        """检查持仓是否应该平仓

        Returns:
            [(持仓, 平仓原因)] 列表
        """
        close_list = []

        for pos in list(self.positions.values()):
            if pos.status != "open":
                continue

            reasons = []

            # 达到目标结算次数
            if pos.settlements_collected >= pos.target_settlements:
                reasons.append(f"目标结算次数达标: {pos.settlements_collected}/{pos.target_settlements}")

            # 累计收入为负（费率反转）
            if pos.accumulated_funding_usd < -pos.position_value_usd * 0.01:
                reasons.append(f"累计资金费亏损: ${pos.accumulated_funding_usd:.2f}")

            # 持仓超过72小时
            holding_hours = (time.time() - pos.opened_at) / 3600
            if holding_hours > 72:
                reasons.append(f"持仓超时: {holding_hours:.1f}h > 72h")

            if reasons:
                close_list.append((pos, "; ".join(reasons)))

        return close_list

    def close_position(
        self,
        position: FundingRatePosition,
        current_spot_price: float,
        current_perp_price: float,
        reason: str = ""
    ) -> FundingRatePosition:
        """平仓资金费率套利持仓

        Args:
            position: 持仓
            current_spot_price: 当前现货价格
            current_perp_price: 当前合约价格
            reason: 平仓原因

        Returns:
            更新后的持仓
        """
        # 计算基差P&L（合约价格变化 - 现货价格变化 → delta中性时接近零）
        basis_pnl_pct = 0.0
        if position.side == PositionSide.SHORT_PERP_LONG_SPOT:
            # 空合约P&L + 多现货P&L
            perp_pnl = (position.perp_price - current_perp_price) / position.perp_price
            spot_pnl = (current_spot_price - position.spot_price) / position.spot_price
        else:
            perp_pnl = (current_perp_price - position.perp_price) / position.perp_price
            spot_pnl = (position.spot_price - current_spot_price) / position.spot_price

        basis_pnl_pct = (perp_pnl + spot_pnl) * 100

        # 扣除开平仓成本
        total_cost_pct = self.cost_model.total_round_trip_cost_pct

        # 总P&L = 基差P&L + 累计资金费率 - 成本
        funding_pnl_pct = (position.accumulated_funding_usd / position.position_value_usd) * 100
        total_pnl_pct = basis_pnl_pct + funding_pnl_pct - total_cost_pct
        total_pnl_usd = position.position_value_usd * (total_pnl_pct / 100)

        # 更新持仓
        position.status = "closed"
        position.closed_at = time.time()
        position.close_reason = reason
        position.exit_spot_price = current_spot_price
        position.exit_perp_price = current_perp_price
        position.realized_pnl_pct = total_pnl_pct
        position.realized_pnl_usd = total_pnl_usd

        # 移到已关闭列表
        if position.position_id in self.positions:
            del self.positions[position.position_id]
        self.closed_positions.append(position)
        self.total_positions_closed += 1
        self.total_pnl += total_pnl_usd

        if total_pnl_usd > 0:
            self.win_count += 1
        else:
            self.loss_count += 1

        # 记录到知识库
        self._record_close_to_knowledge(position)

        logger.info(
            f"资金费率平仓: {position.symbol} | "
            f"settlements={position.settlements_collected} | "
            f"funding=${position.accumulated_funding_usd:.2f} | "
            f"pnl={total_pnl_pct:.3f}% (${total_pnl_usd:.2f}) | "
            f"reason={reason}"
        )

        return position

    def run_full_scan(
        self,
        mode: str = "simulation"
    ) -> Dict[str, Any]:
        """执行完整的资金费率扫描+执行

        Args:
            mode: 执行模式

        Returns:
            扫描结果
        """
        start_time = time.time()

        # 1. 生成/获取费率数据
        snapshots = self.generate_simulated_rates()

        # 2. 扫描机会
        opportunities = self.scan_funding_rates(snapshots)

        # 3. 生成信号
        signals = self.generate_signals(opportunities)

        # 4. 执行信号
        new_positions = []
        for signal in signals:
            pos = self.execute_signal(signal, mode)
            if pos:
                new_positions.append(pos)

        # 5. 模拟结算已持仓
        for pos in list(self.positions.values()):
            if pos.status == "open":
                self.simulate_funding_settlement(pos)

        # 6. 检查平仓
        close_list = self.check_positions_for_close()
        closed = []
        for pos, reason in close_list:
            # 使用缓存的最新价格
            cache_key = f"{pos.symbol}_{pos.exchange}"
            snapshot = self._rate_cache.get(cache_key)
            spot_price = snapshot.index_price if snapshot else pos.spot_price
            perp_price = snapshot.mark_price if snapshot else pos.perp_price
            closed_pos = self.close_position(pos, spot_price, perp_price, reason)
            closed.append(closed_pos)

        duration_ms = (time.time() - start_time) * 1000

        result = {
            "scan_id": f"fr_scan_{int(start_time * 1000)}",
            "rates_scanned": sum(len(v) for v in snapshots.values()),
            "opportunities_found": len(opportunities),
            "signals_generated": len(signals),
            "positions_opened": len(new_positions),
            "positions_closed": len(closed),
            "active_positions": len(self.positions),
            "total_funding_collected": self.total_funding_collected,
            "duration_ms": duration_ms,
        }

        logger.info(
            f"资金费率扫描完成: {result['opportunities_found']} 机会, "
            f"{len(signals)} 信号, "
            f"{len(new_positions)} 开仓, "
            f"{len(closed)} 平仓"
        )

        return result

    def _record_signal_to_knowledge(
        self,
        signal: FundingRateSignal,
        position: FundingRatePosition
    ) -> None:
        """记录开仓信号到知识库"""
        knowledge = self._get_knowledge()
        if not knowledge:
            return

        content = (
            f"[funding_rate_signal] {signal.symbol} @ {signal.exchange} | "
            f"side={signal.side.value} | "
            f"rate={signal.funding_rate:.6f} | "
            f"APY={signal.annualized_yield:.2f}% | "
            f"net_APY={signal.estimated_net_apy:.2f}% | "
            f"confidence={signal.confidence:.2f}"
        )
        try:
            knowledge.add_memory(content)
        except Exception as e:
            logger.warning(f"记录信号知识失败: {e}")

    def _record_close_to_knowledge(self, position: FundingRatePosition) -> None:
        """记录平仓结果到知识库"""
        knowledge = self._get_knowledge()
        if not knowledge:
            return

        outcome = "profitable" if position.realized_pnl_usd > 0 else "loss"
        content = (
            f"[funding_rate_result] {position.symbol} @ {position.exchange} | "
            f"side={position.side.value} | "
            f"settlements={position.settlements_collected}/{position.target_settlements} | "
            f"funding=${position.accumulated_funding_usd:.2f} | "
            f"pnl={position.realized_pnl_pct:.3f}% (${position.realized_pnl_usd:.2f}) | "
            f"outcome={outcome}"
        )
        try:
            knowledge.add_memory(content)
            knowledge.add_knowledge(
                category="funding_rate_execution",
                content=(
                    f"{position.symbol} {position.side.value}: "
                    f"settlements={position.settlements_collected} "
                    f"funding=${position.accumulated_funding_usd:.2f} "
                    f"pnl={position.realized_pnl_pct:.3f}% ({outcome})"
                ),
                metadata={
                    "symbol": position.symbol,
                    "pnl_usd": position.realized_pnl_usd,
                    "outcome": outcome
                }
            )
        except Exception as e:
            logger.warning(f"记录平仓知识失败: {e}")

    def get_engine_statistics(self) -> Dict[str, Any]:
        """获取引擎统计"""
        win_rate = (
            self.win_count / self.total_positions_closed
            if self.total_positions_closed > 0 else 0.0
        )
        avg_pnl = (
            self.total_pnl / self.total_positions_closed
            if self.total_positions_closed > 0 else 0.0
        )

        return {
            "version": "V16.5",
            "total_signals": self.total_signals_generated,
            "total_positions_opened": self.total_positions_opened,
            "total_positions_closed": self.total_positions_closed,
            "active_positions": len(self.positions),
            "total_funding_collected": self.total_funding_collected,
            "total_pnl": self.total_pnl,
            "avg_pnl_per_position": avg_pnl,
            "win_rate": win_rate,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "config": {
                "min_annualized_yield": self.min_annualized_yield,
                "position_size_usd": self.position_size_usd,
                "max_positions": self.max_total_positions,
                "default_settlements": self.default_settlements,
            }
        }


# 全局实例
_funding_rate_engine: Optional[FundingRateEngine] = None


def get_funding_rate_engine(
    config: Optional[Dict[str, Any]] = None
) -> FundingRateEngine:
    """获取全局资金费率引擎实例"""
    global _funding_rate_engine
    if _funding_rate_engine is None:
        _funding_rate_engine = FundingRateEngine(config)
    return _funding_rate_engine
