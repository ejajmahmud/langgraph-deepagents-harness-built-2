"""统计套利引擎 V16.4

独立的统计套利引擎，与V16.x管道完全集成。
基于配对交易的均值回归原理，当相关资产价格偏离历史关系时执行套利。

核心能力：
1. 配对发现 — 自动发现高相关性/协整的资产配对
2. Z-score信号 — 基于价差的标准化偏差产生交易信号
3. 半衰期过滤 — 只交易均值回归速度合理的配对
4. 协整检验 — Engle-Granger风格的协整性检测
5. 模拟执行 — 支持模拟模式下的配对交易执行
6. 知识集成 — 交易结果自动反馈到知识库

架构位置:
    PriceHistoryManager ─→ StatisticalArbEngine ─→ ArbitragePipeline (V16.4)
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


class SignalType(Enum):
    """信号类型"""
    OPEN_LONG_SHORT = "open_long_short"    # 做多A做空B
    OPEN_SHORT_LONG = "open_short_long"    # 做空A做多B
    CLOSE_POSITION = "close_position"       # 平仓
    NO_SIGNAL = "no_signal"                 # 无信号


class PairStatus(Enum):
    """配对状态"""
    CANDIDATE = "candidate"        # 候选（待检验）
    COINTEGRATED = "cointegrated"  # 协整通过
    TRADING = "trading"            # 正在交易
    REJECTED = "rejected"          # 拒绝（不协整）


@dataclass
class PairAnalysis:
    """配对分析结果"""
    symbol_a: str
    symbol_b: str
    exchange: str
    correlation: float = 0.0
    z_score: float = 0.0
    spread_mean: float = 0.0
    spread_std: float = 0.0
    current_spread: float = 0.0
    half_life_hours: float = 0.0
    is_cointegrated: bool = False
    cointegration_pvalue: float = 1.0
    pair_status: PairStatus = PairStatus.CANDIDATE
    data_points: int = 0
    timestamp: float = 0.0

    @property
    def pair_name(self) -> str:
        return f"{self.symbol_a.split('/')[0]}-{self.symbol_b.split('/')[0]}"


@dataclass
class StatArbSignal:
    """统计套利信号"""
    signal_id: str
    signal_type: SignalType
    pair: PairAnalysis
    confidence: float = 0.0
    expected_profit_pct: float = 0.0
    entry_z_score: float = 0.0
    close_z_score: float = 0.5
    quantity_a: float = 0.0
    quantity_b: float = 0.0
    price_a: float = 0.0
    price_b: float = 0.0
    position_value_usd: float = 0.0
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StatArbPosition:
    """统计套利持仓"""
    position_id: str
    signal_id: str
    symbol_a: str
    symbol_b: str
    exchange: str
    direction: str          # "long_a_short_b" 或 "short_a_long_b"
    entry_price_a: float
    entry_price_b: float
    entry_z_score: float
    quantity_a: float
    quantity_b: float
    position_value_usd: float
    close_z_score: float = 0.5
    status: str = "open"    # open / closed
    opened_at: float = 0.0
    closed_at: float = 0.0
    exit_price_a: float = 0.0
    exit_price_b: float = 0.0
    realized_pnl_pct: float = 0.0
    realized_pnl_usd: float = 0.0
    knowledge_recorded: bool = False


class StatisticalArbEngine:
    """统计套利引擎 V16.4

    独立于真实交易所的统计套利引擎，
    与V16.x管道和知识库完全集成。
    """

    def __init__(
        self,
        price_history=None,
        knowledge_storage=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """初始化统计套利引擎

        Args:
            price_history: PriceHistoryManager 实例
            knowledge_storage: 知识存储实例
            config: 配置字典
        """
        self._price_history = price_history
        self._knowledge = knowledge_storage
        self.config = config or {}

        # 策略参数
        self.z_score_entry = self.config.get("z_score_entry", 2.0)
        self.z_score_close = self.config.get("z_score_close", 0.5)
        self.z_score_stop = self.config.get("z_score_stop", 3.5)
        self.min_correlation = self.config.get("min_correlation", 0.7)
        self.min_half_life_hours = self.config.get("min_half_life_hours", 1.0)
        self.max_half_life_hours = self.config.get("max_half_life_hours", 72.0)
        self.min_data_points = self.config.get("min_data_points", 50)
        self.position_size_usd = self.config.get("position_size_usd", 500.0)
        self.max_positions = self.config.get("max_positions", 5)

        # 统计配对（从配置或默认）
        self._pairs = self.config.get("pairs", None)

        # 持仓管理
        self.positions: Dict[str, StatArbPosition] = {}
        self.closed_positions: List[StatArbPosition] = []

        # 缓存的配对分析
        self._pair_analyses: Dict[str, PairAnalysis] = {}

        # 统计
        self.total_signals_generated = 0
        self.total_positions_opened = 0
        self.total_positions_closed = 0
        self.total_realized_pnl = 0.0
        self.win_count = 0
        self.loss_count = 0

        logger.info(
            f"统计套利引擎 V16.4 初始化: "
            f"z_entry={self.z_score_entry}, "
            f"z_close={self.z_score_close}, "
            f"min_corr={self.min_correlation}"
        )

    def _get_price_history(self):
        """延迟获取价格历史管理器"""
        if self._price_history is not None:
            return self._price_history
        try:
            from data_collection.price_history_manager import get_price_history_manager
            self._price_history = get_price_history_manager()
            return self._price_history
        except Exception as e:
            logger.error(f"获取价格历史管理器失败: {e}")
            return None

    def _get_knowledge(self):
        """延迟获取知识存储"""
        if self._knowledge is not None:
            return self._knowledge
        try:
            from storage.mem0_storage import get_mem0_storage
            storage = get_mem0_storage()
            if storage is None:
                from storage.mem0_mock_storage import create_mock_mem0_storage
                storage = create_mock_mem0_storage({
                    "user_id": "crypto-arbitrage-user",
                    "agent_id": "stat-arb-engine-v16-4"
                })
            self._knowledge = storage
            return storage
        except Exception:
            try:
                from storage.mem0_mock_storage import create_mock_mem0_storage
                storage = create_mock_mem0_storage({
                    "user_id": "crypto-arbitrage-user",
                    "agent_id": "stat-arb-engine-v16-4"
                })
                self._knowledge = storage
                return storage
            except Exception as e:
                logger.error(f"获取知识存储失败: {e}")
                return None

    # ========== ADF协整检验 (V16.7新增) ==========

    def _perform_adf_test(
        self,
        prices: List[float],
        max_lag: Optional[int] = None
    ) -> Dict[str, Any]:
        """执行Augmented Dickey-Fuller检验 (ADF)

        ADF检验用于测试时间序列是否平稳(均值回归)。
        这是Engle-Granger两步法的第一步。

        Args:
            prices: 价格序列
            max_lag: 最大滞后阶数 (默认自动确定)

        Returns:
            字典，包含:
            - is_stationary: 是否平稳 (p < 0.05)
            - p_value: p值
            - test_statistic: 检验统计量
            - critical_values: 临界值 (1%, 5%, 10%)
        """
        import math

        n = len(prices)
        if n < 20:
            return {
                'is_stationary': False,
                'p_value': 1.0,
                'test_statistic': 0.0,
                'critical_values': {'1%': -3.96, '5%': -3.41, '10%': -3.12},
                'error': '数据点不足'
            }

        # 自动确定滞后阶数
        if max_lag is None:
            max_lag = min(int(12 * (n / 100) ** 0.25), n - 1)

        # 计算差分
        diff = [prices[i] - prices[i - 1] for i in range(1, n)]

        # 简化版ADF: 使用一阶滞后
        # y = diff[t], x = price[t-1]
        y = diff[1:]  # diff[1:]
        x = prices[1:-1]  # prices shifted by 1

        n_reg = min(len(y), len(x))
        if n_reg < 10:
            return {
                'is_stationary': False,
                'p_value': 1.0,
                'test_statistic': 0.0,
                'critical_values': {'1%': -3.96, '5%': -3.41, '10%': -3.12},
                'error': '数据不足'
            }

        # 简化回归
        xy_sum = sum(y[i] * x[i] for i in range(n_reg))
        xx_sum = sum(x[i] ** 2 for i in range(n_reg))

        if xx_sum == 0:
            return {
                'is_stationary': False,
                'p_value': 1.0,
                'test_statistic': 0.0,
                'critical_values': {'1%': -3.96, '5%': -3.41, '10%': -3.12},
                'error': '回归失败'
            }

        # ADF统计量 = rho / 标准误
        rho = xy_sum / xx_sum
        resid = [y[i] - rho * x[i] for i in range(n_reg)]
        resid_var = sum(r ** 2 for r in resid) / max(n_reg - 1, 1)

        se = math.sqrt(resid_var / xx_sum) if resid_var > 0 else 1.0
        adf_stat = rho / se if se > 0 else 0

        # 近似p值 (使用MacKinnon临界值表)
        p_value = self._adf_p_value_approx(adf_stat, n)

        return {
            'is_stationary': p_value < 0.05,
            'p_value': p_value,
            'test_statistic': adf_stat,
            'critical_values': {'1%': -3.96, '5%': -3.41, '10%': -3.12},
        }

    def _adf_p_value_approx(self, t_stat: float, n: int) -> float:
        """根据ADF统计量近似p值

        使用MacKinnon临界值表的近似公式

        Args:
            t_stat: ADF统计量
            n: 样本大小

        Returns:
            p值 (近似)
        """
        # 临界值近似公式
        c10 = -2.5766 - 3.8968 / n ** 0.5 - 10.7533 / n
        c5 = -2.1788 - 3.2176 / n ** 0.5 - 5.8842 / n
        c1 = -1.9591 - 2.4786 / n ** 0.5 - 3.9879 / n

        if t_stat < c1:
            return 0.01
        elif t_stat < c5:
            return 0.05
        elif t_stat < c10:
            return 0.10
        else:
            return 0.20

    def _perform_engle_granger_test(
        self,
        prices_a: List[float],
        prices_b: List[float]
    ) -> Dict[str, Any]:
        """Engle-Granger协整检验

        Engle-Granger两步法:
        1. 回归: Y = alpha + beta * X + residuals
        2. ADF检验 residuals是否平稳

        Args:
            prices_a: 资产A价格序列
            prices_b: 资产B价格序列

        Returns:
            字典，包含:
            - is_cointegrated: 是否协整
            - p_value: p值
            - alpha: 回归截距
            - beta: 回归系数
            - half_life: 半衰期(小时)
        """
        n = min(len(prices_a), len(prices_b))
        if n < 20:
            return {
                'is_cointegrated': False,
                'p_value': 1.0,
                'alpha': 0.0,
                'beta': 1.0,
                'half_life': None,
                'error': '数据不足'
            }

        # 步骤1: OLS回归 price_a = alpha + beta * price_b
        # 计算beta
        x = prices_b[:n]
        y = prices_a[:n]
        x_mean = sum(x) / n
        y_mean = sum(y) / n

        xy_cov = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        xx_var = sum((x[i] - x_mean) ** 2 for i in range(n))

        if xx_var == 0:
            return {
                'is_cointegrated': False,
                'p_value': 1.0,
                'alpha': 0.0,
                'beta': 1.0,
                'half_life': None,
                'error': '方差为0'
            }

        beta = xy_cov / xx_var
        alpha = y_mean - beta * x_mean

        # 计算残差
        residuals = [y[i] - alpha - beta * x[i] for i in range(n)]

        # 步骤2: ADF检验残差
        adf_result = self._perform_adf_test(residuals, max_lag=5)

        # 计算半衰期
        # half_life = -ln(2) / ln(1 - beta) for OU process
        half_life = None
        if 0 < beta < 1:
            import math
            half_life = -math.log(2) / math.log(1 - beta) if (1 - beta) > 0 else None

        return {
            'is_cointegrated': adf_result['is_stationary'],
            'p_value': adf_result['p_value'],
            'alpha': alpha,
            'beta': beta,
            'half_life': half_life,
        }

    def analyze_pair(
        self,
        symbol_a: str,
        symbol_b: str,
        exchange: str = "binance",
        window: Optional[int] = None
    ) -> Optional[PairAnalysis]:
        """分析一个配对的统计套利潜力

        Args:
            symbol_a: 资产A
            symbol_b: 资产B
            exchange: 交易所
            window: 分析窗口

        Returns:
            配对分析结果，数据不足返回None
        """
        ph = self._get_price_history()
        if ph is None:
            return None

        # 获取相关系数
        corr = ph.calculate_correlation(symbol_a, symbol_b, exchange, window)
        if corr is None:
            return None

        # 获取Z-score
        z_result = ph.calculate_z_score(symbol_a, symbol_b, exchange, window)
        if z_result is None:
            return None

        z_score, spread_mean, spread_std = z_result

        # 获取半衰期
        half_life = ph.calculate_half_life(symbol_a, symbol_b, exchange, window)

        # 获取当前价差
        spread_series = ph.calculate_spread_series(symbol_a, symbol_b, exchange, window)
        current_spread = spread_series[-1] if spread_series else 0.0

        # 获取数据点数
        prices_a = ph.get_price_series(symbol_a, exchange, window)
        prices_b = ph.get_price_series(symbol_b, exchange, window)
        data_points = len(prices_a)

        # 执行Engle-Granger协整检验 (V16.7新增)
        eg_result = None
        if data_points >= self.min_data_points:
            eg_result = self._perform_engle_granger_test(prices_a, prices_b)

        # 判断协整性（增强版：ADF检验 + 原有条件）
        # ADF检验优先，如果p值显著则使用ADF结果
        if eg_result and eg_result.get('is_cointegrated'):
            is_cointegrated = True
            cointegration_pvalue = eg_result['p_value']
            half_life = eg_result.get('half_life')
            logger.info(f"✅ ADF协整检验通过: {symbol_a}/{symbol_b}, p={cointegration_pvalue:.4f}")
        else:
            # 回退到原有条件检查
            is_cointegrated = (
                abs(corr) >= self.min_correlation and
                half_life is not None and
                self.min_half_life_hours <= half_life <= self.max_half_life_hours and
                data_points >= self.min_data_points
            )
            cointegration_pvalue = 0.05 if is_cointegrated else 1.0
            if eg_result:
                logger.debug(f"⚠️ ADF检验未通过，回退条件: {symbol_a}/{symbol_b}, p={eg_result.get('p_value', 1.0):.4f}")

        # 确定配对状态
        if data_points < self.min_data_points:
            status = PairStatus.CANDIDATE
        elif is_cointegrated:
            status = PairStatus.COINTEGRATED
        else:
            status = PairStatus.REJECTED

        analysis = PairAnalysis(
            symbol_a=symbol_a,
            symbol_b=symbol_b,
            exchange=exchange,
            correlation=corr,
            z_score=z_score,
            spread_mean=spread_mean,
            spread_std=spread_std,
            current_spread=current_spread,
            half_life_hours=half_life or 0.0,
            is_cointegrated=is_cointegrated,
            cointegration_pvalue=cointegration_pvalue,
            pair_status=status,
            data_points=data_points,
            timestamp=time.time()
        )

        # 缓存分析结果
        cache_key = f"{symbol_a}_{symbol_b}_{exchange}"
        self._pair_analyses[cache_key] = analysis

        return analysis

    def scan_all_pairs(
        self,
        exchange: str = "binance",
        window: Optional[int] = None
    ) -> List[PairAnalysis]:
        """扫描所有配对

        Args:
            exchange: 交易所
            window: 分析窗口

        Returns:
            通过筛选的配对分析列表
        """
        ph = self._get_price_history()
        if ph is None:
            return []

        pairs = self._pairs or ph.STATISTICAL_PAIRS
        results = []

        for sym_a, sym_b in pairs:
            try:
                analysis = self.analyze_pair(sym_a, sym_b, exchange, window)
                if analysis and analysis.is_cointegrated:
                    results.append(analysis)
            except Exception as e:
                logger.debug(f"分析 {sym_a}/{sym_b} 失败: {e}")

        # 按半衰期排序（最短半衰期优先）
        results.sort(key=lambda x: x.half_life_hours)

        logger.info(
            f"配对扫描完成: {len(pairs)} 个配对, "
            f"{len(results)} 个协整通过"
        )

        return results

    def generate_signals(
        self,
        analyses: Optional[List[PairAnalysis]] = None,
        exchange: str = "binance"
    ) -> List[StatArbSignal]:
        """生成交易信号

        Args:
            analyses: 配对分析列表（None则自动扫描）
            exchange: 交易所

        Returns:
            交易信号列表
        """
        if analyses is None:
            analyses = self.scan_all_pairs(exchange)

        signals = []
        for analysis in analyses:
            if not analysis.is_cointegrated:
                continue

            # 检查持仓限制
            if len(self.positions) >= self.max_positions:
                break

            # 检查是否已有该配对持仓
            pair_key = f"{analysis.symbol_a}_{analysis.symbol_b}"
            existing = any(
                f"{p.symbol_a}_{p.symbol_b}" == pair_key and p.status == "open"
                for p in self.positions.values()
            )
            if existing:
                continue

            # Z-score信号判断
            signal_type = SignalType.NO_SIGNAL
            if abs(analysis.z_score) >= self.z_score_entry:
                if analysis.z_score > 0:
                    # 价差偏大 → 做空A做多B（预期价差回归）
                    signal_type = SignalType.OPEN_SHORT_LONG
                else:
                    # 价差偏小 → 做多A做空B（预期价差回归）
                    signal_type = SignalType.OPEN_LONG_SHORT

            if signal_type == SignalType.NO_SIGNAL:
                continue

            # 获取当前价格
            ph = self._get_price_history()
            price_a = ph.get_latest_price(analysis.symbol_a, exchange) if ph else None
            price_b = ph.get_latest_price(analysis.symbol_b, exchange) if ph else None

            if not price_a or not price_b or price_a <= 0 or price_b <= 0:
                continue

            # 计算仓位大小
            half_value = self.position_size_usd / 2
            quantity_a = half_value / price_a
            quantity_b = half_value / price_b

            # 计算预期收益（基于Z-score回归到均值）
            expected_profit_pct = abs(analysis.z_score - self.z_score_close) * analysis.spread_std * 100
            expected_profit_pct = max(0, min(expected_profit_pct, 5.0))  # 上限5%

            # 置信度计算
            confidence = min(1.0, abs(analysis.z_score) / self.z_score_stop)
            confidence *= (0.5 + 0.5 * abs(analysis.correlation))  # 相关性加权
            if analysis.half_life_hours > 0:
                hl_factor = min(1.0, self.min_half_life_hours / analysis.half_life_hours)
                confidence *= (0.5 + 0.5 * hl_factor)

            signal = StatArbSignal(
                signal_id=f"stat_{uuid.uuid4().hex[:8]}",
                signal_type=signal_type,
                pair=analysis,
                confidence=confidence,
                expected_profit_pct=expected_profit_pct,
                entry_z_score=analysis.z_score,
                close_z_score=self.z_score_close,
                quantity_a=quantity_a,
                quantity_b=quantity_b,
                price_a=price_a,
                price_b=price_b,
                position_value_usd=self.position_size_usd,
                timestamp=time.time(),
                metadata={
                    "half_life_hours": analysis.half_life_hours,
                    "correlation": analysis.correlation,
                    "spread_std": analysis.spread_std,
                }
            )

            signals.append(signal)
            self.total_signals_generated += 1

        logger.info(f"生成 {len(signals)} 个统计套利信号")
        return signals

    def execute_signal(
        self,
        signal: StatArbSignal,
        mode: str = "simulation"
    ) -> Optional[StatArbPosition]:
        """执行统计套利信号

        Args:
            signal: 交易信号
            mode: 执行模式（simulation/live）

        Returns:
            持仓记录，失败返回None
        """
        pair = signal.pair
        direction = (
            "long_a_short_b" if signal.signal_type == SignalType.OPEN_LONG_SHORT
            else "short_a_long_b"
        )

        logger.info(
            f"执行统计套利: {pair.pair_name} | "
            f"方向={direction} | "
            f"z_score={pair.z_score:.2f} | "
            f"预期利润={signal.expected_profit_pct:.3f}%"
        )

        position = StatArbPosition(
            position_id=f"spos_{uuid.uuid4().hex[:8]}",
            signal_id=signal.signal_id,
            symbol_a=pair.symbol_a,
            symbol_b=pair.symbol_b,
            exchange=pair.exchange,
            direction=direction,
            entry_price_a=signal.price_a,
            entry_price_b=signal.price_b,
            entry_z_score=signal.entry_z_score,
            quantity_a=signal.quantity_a,
            quantity_b=signal.quantity_b,
            position_value_usd=signal.position_value_usd,
            close_z_score=signal.close_z_score,
            status="open",
            opened_at=time.time()
        )

        self.positions[position.position_id] = position
        self.total_positions_opened += 1

        # 记录到知识库
        self._record_signal_to_knowledge(signal, position)

        return position

    def check_positions_for_close(
        self,
        exchange: str = "binance"
    ) -> List[Tuple[StatArbPosition, str, float]]:
        """检查持仓是否应该平仓

        Args:
            exchange: 交易所

        Returns:
            [(持仓, 平仓原因, 当前Z-score)] 列表
        """
        ph = self._get_price_history()
        close_list = []

        for pos in list(self.positions.values()):
            if pos.status != "open":
                continue

            # 获取当前Z-score
            z_result = ph.calculate_z_score(pos.symbol_a, pos.symbol_b, exchange) if ph else None
            if z_result is None:
                continue

            current_z, _, _ = z_result

            should_close = False
            reason = ""

            # Z-score回归到均值
            if abs(current_z) < pos.close_z_score:
                should_close = True
                reason = f"Z-score回归: {current_z:.2f} < {pos.close_z_score}"

            # Z-score继续扩大（止损）
            elif abs(current_z) > self.z_score_stop:
                should_close = True
                reason = f"Z-score扩大止损: {current_z:.2f} > {self.z_score_stop}"

            if should_close:
                close_list.append((pos, reason, current_z))

        return close_list

    def close_position(
        self,
        position: StatArbPosition,
        current_price_a: float,
        current_price_b: float,
        current_z_score: float = 0.0
    ) -> StatArbPosition:
        """平仓统计套利持仓

        Args:
            position: 持仓记录
            current_price_a: 资产A当前价格
            current_price_b: 资产B当前价格
            current_z_score: 当前Z-score

        Returns:
            更新后的持仓记录
        """
        # 计算P&L
        if position.direction == "long_a_short_b":
            # 做多A的收益 + 做空B的收益
            pnl_a = (current_price_a - position.entry_price_a) / position.entry_price_a
            pnl_b = (position.entry_price_b - current_price_b) / position.entry_price_b
        else:
            # 做空A的收益 + 做多B的收益
            pnl_a = (position.entry_price_a - current_price_a) / position.entry_price_a
            pnl_b = (current_price_b - position.entry_price_b) / position.entry_price_b

        # 加权P&L
        total_pnl_pct = (pnl_a + pnl_b) / 2 * 100  # 百分比
        total_pnl_usd = position.position_value_usd * (total_pnl_pct / 100)

        # 扣除费用（买卖各2笔交易，每笔0.1%）
        fee_pct = 0.1 * 4  # 0.4%
        total_pnl_pct -= fee_pct
        fee_usd = position.position_value_usd * (fee_pct / 100)
        total_pnl_usd -= fee_usd

        # 更新持仓
        position.status = "closed"
        position.closed_at = time.time()
        position.exit_price_a = current_price_a
        position.exit_price_b = current_price_b
        position.realized_pnl_pct = total_pnl_pct
        position.realized_pnl_usd = total_pnl_usd

        # 移到已关闭列表
        if position.position_id in self.positions:
            del self.positions[position.position_id]
        self.closed_positions.append(position)
        self.total_positions_closed += 1
        self.total_realized_pnl += total_pnl_usd

        if total_pnl_usd > 0:
            self.win_count += 1
        else:
            self.loss_count += 1

        # 记录到知识库
        self._record_close_to_knowledge(position, current_z_score)

        logger.info(
            f"统计套利平仓: {position.symbol_a}/{position.symbol_b} | "
            f"pnl={total_pnl_pct:.3f}% (${total_pnl_usd:.2f}) | "
            f"holding={((position.closed_at - position.opened_at) / 3600):.1f}h"
        )

        return position

    def _record_signal_to_knowledge(
        self,
        signal: StatArbSignal,
        position: StatArbPosition
    ) -> None:
        """记录开仓信号到知识库"""
        knowledge = self._get_knowledge()
        if not knowledge:
            return

        content = (
            f"[stat_arb_signal] {signal.pair.pair_name} | "
            f"direction={position.direction} | "
            f"z_score={signal.entry_z_score:.2f} | "
            f"correlation={signal.pair.correlation:.3f} | "
            f"half_life={signal.pair.half_life_hours:.1f}h | "
            f"expected_profit={signal.expected_profit_pct:.3f}% | "
            f"confidence={signal.confidence:.2f}"
        )
        try:
            knowledge.add_memory(content)
        except Exception as e:
            logger.warning(f"记录信号知识失败: {e}")

    def _record_close_to_knowledge(
        self,
        position: StatArbPosition,
        z_score_at_close: float
    ) -> None:
        """记录平仓结果到知识库"""
        knowledge = self._get_knowledge()
        if not knowledge:
            return

        outcome = "profitable" if position.realized_pnl_usd > 0 else "loss"
        content = (
            f"[stat_arb_result] {position.symbol_a}/{position.symbol_b} | "
            f"direction={position.direction} | "
            f"entry_z={position.entry_z_score:.2f} | "
            f"exit_z={z_score_at_close:.2f} | "
            f"pnl={position.realized_pnl_pct:.3f}% | "
            f"pnl_usd=${position.realized_pnl_usd:.2f} | "
            f"outcome={outcome}"
        )
        try:
            knowledge.add_memory(content)
            knowledge.add_knowledge(
                category="stat_arb_execution",
                content=(
                    f"{position.symbol_a}/{position.symbol_b} "
                    f"dir={position.direction} "
                    f"z={position.entry_z_score:.2f}→{z_score_at_close:.2f} "
                    f"pnl={position.realized_pnl_pct:.3f}% ({outcome})"
                ),
                metadata={
                    "pair": f"{position.symbol_a}/{position.symbol_b}",
                    "pnl_pct": position.realized_pnl_pct,
                    "outcome": outcome
                }
            )
        except Exception as e:
            logger.warning(f"记录平仓知识失败: {e}")

    def run_full_scan(
        self,
        exchange: str = "binance",
        window: Optional[int] = None
    ) -> Dict[str, Any]:
        """执行完整的统计套利扫描+执行

        Args:
            exchange: 交易所
            window: 分析窗口

        Returns:
            扫描+执行结果
        """
        start_time = time.time()

        # 1. 扫描所有配对
        analyses = self.scan_all_pairs(exchange, window)

        # 2. 生成信号
        signals = self.generate_signals(analyses, exchange)

        # 3. 执行信号（模拟模式）
        new_positions = []
        for signal in signals:
            pos = self.execute_signal(signal, mode="simulation")
            if pos:
                new_positions.append(pos)

        # 4. 检查是否需要平仓
        closes = self.check_positions_for_close(exchange)

        # 5. 获取当前价格并平仓
        ph = self._get_price_history()
        closed_positions = []
        for pos, reason, current_z in closes:
            price_a = ph.get_latest_price(pos.symbol_a, exchange) if ph else pos.entry_price_a
            price_b = ph.get_latest_price(pos.symbol_b, exchange) if ph else pos.entry_price_b
            if price_a and price_b:
                closed = self.close_position(pos, price_a, price_b, current_z)
                closed_positions.append((closed, reason))

        duration_ms = (time.time() - start_time) * 1000

        result = {
            "scan_id": f"stat_scan_{int(start_time * 1000)}",
            "pairs_scanned": len(analyses) + len([a for a in self._pair_analyses.values() if not a.is_cointegrated]),
            "cointegrated_pairs": len(analyses),
            "signals_generated": len(signals),
            "positions_opened": len(new_positions),
            "positions_closed": len(closed_positions),
            "duration_ms": duration_ms,
            "active_positions": len(self.positions),
        }

        logger.info(
            f"统计套利扫描完成: {result['cointegrated_pairs']} 协整对, "
            f"{len(signals)} 信号, "
            f"{len(new_positions)} 开仓, "
            f"{len(closed_positions)} 平仓"
        )

        return result

    def get_engine_statistics(self) -> Dict[str, Any]:
        """获取引擎统计信息

        Returns:
            统计数据字典
        """
        win_rate = (
            self.win_count / self.total_positions_closed
            if self.total_positions_closed > 0 else 0.0
        )

        avg_pnl = (
            self.total_realized_pnl / self.total_positions_closed
            if self.total_positions_closed > 0 else 0.0
        )

        return {
            "version": "V16.4",
            "total_signals_generated": self.total_signals_generated,
            "total_positions_opened": self.total_positions_opened,
            "total_positions_closed": self.total_positions_closed,
            "active_positions": len(self.positions),
            "total_realized_pnl": self.total_realized_pnl,
            "avg_pnl_per_trade": avg_pnl,
            "win_rate": win_rate,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "cointegrated_pairs_cached": sum(
                1 for a in self._pair_analyses.values()
                if a.is_cointegrated
            ),
            "config": {
                "z_score_entry": self.z_score_entry,
                "z_score_close": self.z_score_close,
                "z_score_stop": self.z_score_stop,
                "min_correlation": self.min_correlation,
                "position_size_usd": self.position_size_usd,
                "max_positions": self.max_positions,
            }
        }


# 全局实例
_stat_arb_engine: Optional[StatisticalArbEngine] = None


def get_statistical_arb_engine(
    config: Optional[Dict[str, Any]] = None
) -> StatisticalArbEngine:
    """获取全局统计套利引擎实例

    Args:
        config: 配置字典

    Returns:
        统计套利引擎实例
    """
    global _stat_arb_engine
    if _stat_arb_engine is None:
        _stat_arb_engine = StatisticalArbEngine(config)
    return _stat_arb_engine
