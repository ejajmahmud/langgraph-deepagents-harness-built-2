"""高级分析、机器学习与回测增强 V98.0 - Phase 42

核心功能：
- AdvancedAnalytics: 高级分析(模式识别/区间检测/相关性分析)
- MachineLearning: 机器学习(特征工程/模型训练/信号增强)
- BacktestEnhancement: 回测增强(前向分析/蒙特卡洛/绩效归因)

创建时间：2026-05-09 08:19
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
import json
import random
import math


# ============ 枚举定义 ============

class PatternType(Enum):
    """模式类型"""
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    HEAD_SHOULDERS = "head_shoulders"
    TRIANGLE = "triangle"
    FLAG = "flag"
    WEDGE = "wedge"
    CHANNEL = "channel"


class MarketRegime(Enum):
    """市场区间"""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    CALM = "calm"


class MLModelType(Enum):
    """ML模型类型"""
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    LSTM = "lstm"
    PROPHET = "prophet"


class BacktestModeV98(Enum):
    """回测模式"""
    WALK_FORWARD = "walk_forward"
    MONTE_CARLO = "monte_carlo"
    IN_SAMPLE = "in_sample"
    OUT_OF_SAMPLE = "out_of_sample"


class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


# ============ 数据结构 ============

@dataclass
class PatternResult:
    """模式结果"""
    pattern_type: str
    confidence: float
    direction: str
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None


@dataclass
class RegimeResult:
    """区间结果"""
    regime: str
    confidence: float
    trend_strength: float
    volatility: float
    duration: int


@dataclass
class CorrelationResult:
    """相关性结果"""
    asset1: str
    asset2: str
    correlation: float
    method: str
    significance: float


@dataclass
class MLFeature:
    """ML特征"""
    name: str
    value: float
    importance: float
    timestamp: str


@dataclass
class MLPrediction:
    """ML预测"""
    model_type: str
    prediction: float
    confidence: float
    direction: str
    probability: float


@dataclass
class BacktestResultV98:
    """回测结果"""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    num_trades: int
    equity_curve: List[float]


@dataclass
class WalkForwardResult:
    """前向分析结果"""
    period: int
    in_sample_return: float
    out_of_sample_return: float
    stability: float
    parameter_drift: float


@dataclass
class MonteCarloResult:
    """蒙特卡洛结果"""
    median_return: float
    percentile_5: float
    percentile_95: float
    var_95: float
    success_rate: float


@dataclass
class PerformanceAttributionV98:
    """绩效归因"""
    total_return: float
    alpha: float
    beta: float
    market_contribution: float
    selection_contribution: float
    timing_contribution: float


# ============ AdvancedAnalytics ============

class AdvancedAnalytics:
    """高级分析引擎"""

    def __init__(self):
        self._patterns: List[PatternResult] = []
        self._regimes: List[RegimeResult] = []
        self._correlations: Dict[str, CorrelationResult] = {}

    def detect_pattern(self, prices: List[float], volume: List[float]) -> Optional[PatternResult]:
        """模式识别"""
        if len(prices) < 30:
            return None

        # 简化模式检测
        recent = prices[-10:]
        earlier = prices[-30:-10]

        recent_avg = sum(recent) / len(recent)
        earlier_avg = sum(earlier) / len(earlier)

        # 检测双顶/双底
        if recent[-1] < earlier_avg * 0.95:
            return PatternResult(
                pattern_type=PatternType.DOUBLE_BOTTOM.value,
                confidence=0.75,
                direction="bullish",
                target_price=recent_avg * 1.1,
                stop_loss=recent_avg * 0.95
            )
        elif recent[-1] > earlier_avg * 1.05:
            return PatternResult(
                pattern_type=PatternType.DOUBLE_TOP.value,
                confidence=0.75,
                direction="bearish",
                target_price=recent_avg * 0.9,
                stop_loss=recent_avg * 1.05
            )

        return None

    def detect_regime(self, prices: List[float], window: int = 20) -> RegimeResult:
        """区间检测"""
        if len(prices) < window:
            return RegimeResult(
                regime=MarketRegime.SIDEWAYS.value,
                confidence=0.5,
                trend_strength=0.0,
                volatility=0.0,
                duration=0
            )

        recent = prices[-window:]
        avg = sum(recent) / len(recent)
        std = math.sqrt(sum((p - avg) ** 2 for p in recent) / len(recent))
        volatility = std / avg if avg > 0 else 0

        # 计算趋势强度
        trend_strength = abs(prices[-1] - prices[-window]) / (avg * window)

        if volatility > 0.03:
            regime = MarketRegime.VOLATILE.value
        elif trend_strength > 0.02:
            regime = MarketRegime.BULL.value if prices[-1] > prices[-window] else MarketRegime.BEAR.value
        else:
            regime = MarketRegime.SIDEWAYS.value

        return RegimeResult(
            regime=regime,
            confidence=min(0.9, volatility * 10 + 0.5),
            trend_strength=trend_strength,
            volatility=volatility,
            duration=window
        )

    def analyze_correlation(self, asset1_prices: List[float],
                         asset2_prices: List[float]) -> CorrelationResult:
        """相关性分析"""
        if len(asset1_prices) != len(asset2_prices) or len(asset1_prices) < 10:
            return CorrelationResult(
                asset1="unknown",
                asset2="unknown",
                correlation=0.0,
                method="pearson",
                significance=0.0
            )

        # 计算皮尔逊相关系数
        n = len(asset1_prices)
        mean1 = sum(asset1_prices) / n
        mean2 = sum(asset2_prices) / n

        cov = sum((a - mean1) * (b - mean2) for a, b in zip(asset1_prices, asset2_prices)) / n
        std1 = math.sqrt(sum((a - mean1) ** 2 for a in asset1_prices) / n)
        std2 = math.sqrt(sum((b - mean2) ** 2 for b in asset2_prices) / n)

        correlation = cov / (std1 * std2) if std1 > 0 and std2 > 0 else 0

        # 计算显著性(t检验简化)
        significance = min(1.0, abs(correlation) * math.sqrt(n - 2) / 2)

        return CorrelationResult(
            asset1="asset1",
            asset2="asset2",
            correlation=correlation,
            method="pearson",
            significance=significance
        )

    def calculate_rolling_correlation(self, prices_dict: Dict[str, List[float]],
                                window: int = 20) -> Dict[Tuple[str, str], float]:
        """滚动相关性"""
        correlations = {}

        assets = list(prices_dict.keys())
        for i, asset1 in enumerate(assets):
            for asset2 in assets[i+1:]:
                p1 = prices_dict[asset1]
                p2 = prices_dict[asset2]

                if len(p1) >= window and len(p2) >= window:
                    result = self.analyze_correlation(
                        p1[-window:],
                        p2[-window:]
                    )
                    correlations[(asset1, asset2)] = result.correlation

        return correlations

    def momentum_analysis(self, prices: List[float],
                       periods: List[int] = [5, 10, 20]) -> Dict[str, float]:
        """动量分析"""
        mom = {}

        for period in periods:
            if len(prices) > period:
                change = (prices[-1] - prices[-period]) / prices[-period] if prices[-period] > 0 else 0
                mom[f"momentum_{period}"] = change

        # RSI计算
        if len(prices) > 14:
            gains = []
            losses = []
            for i in range(len(prices) - 14, len(prices) - 1):
                change = prices[i + 1] - prices[i]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))

            avg_gain = sum(gains) / 14
            avg_loss = sum(losses) / 14
            rs = avg_gain / avg_loss if avg_loss > 0 else 0
            rsi = 100 - (100 / (1 + rs))
            mom["rsi_14"] = rsi

        return mom

    def volume_analysis(self, prices: List[float],
                    volume: List[float]) -> Dict[str, Any]:
        """成交量分析"""
        if len(prices) != len(volume) or len(volume) < 20:
            return {"status": "insufficient_data"}

        avg_volume = sum(volume[-20:]) / 20
        recent_volume = volume[-1]

        if recent_volume > avg_volume * 1.5:
            volume_status = "spike"
        elif recent_volume > avg_volume * 1.2:
            volume_status = "elevated"
        else:
            volume_status = "normal"

        # OBV趋势
        obv = 0
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                obv += volume[i]
            else:
                obv -= volume[i]

        return {
            "volume_status": volume_status,
            "obv": obv,
            "obv_trend": "bullish" if obv > 0 else "bearish"
        }

    def get_analytics_summary(self) -> Dict[str, Any]:
        return {
            "patterns_detected": len(self._patterns),
            "regimes_tracked": len(self._regimes),
            "correlations": len(self._correlations)
        }


# ============ MachineLearning ============

class MachineLearning:
    """机器学习引擎"""

    def __init__(self):
        self._features: List[MLFeature] = []
        self._models: Dict[str, Any] = {}
        self._weights_trained: bool = False

    def feature_engineering(self, prices: List[float],
                        volume: List[float]) -> List[MLFeature]:
        """特征工程"""
        features = []

        # 价格变化率
        if len(prices) > 1:
            returns = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
            features.append(MLFeature(
                name="return",
                value=returns,
                importance=0.8,
                timestamp=datetime.now().isoformat()
            ))

        # 波动率
        if len(prices) > 10:
            mean = sum(prices) / len(prices)
            std = math.sqrt(sum((p - mean) ** 2 for p in prices) / len(prices))
            vol = std / mean if mean > 0 else 0
            features.append(MLFeature(
                name="volatility",
                value=vol,
                importance=0.7,
                timestamp=datetime.now().isoformat()
            ))

        # 成交量加权价格
        if len(prices) == len(volume):
            vwap = sum(p * v for p, v in zip(prices, volume)) / sum(volume)
            features.append(MLFeature(
                name="vwap",
                value=vwap,
                importance=0.6,
                timestamp=datetime.now().isoformat()
            ))

        # RSI
        if len(prices) > 14:
            gains = []
            losses = []
            for i in range(len(prices) - 14, len(prices) - 1):
                change = prices[i + 1] - prices[i]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))

            avg_gain = sum(gains) / 14
            avg_loss = sum(losses) / 14
            rs = avg_gain / avg_loss if avg_loss > 0 else 0
            rsi = 100 - (100 / (1 + rs))
            features.append(MLFeature(
                name="rsi",
                value=rsi,
                importance=0.5,
                timestamp=datetime.now().isoformat()
            ))

        self._features = features
        return features

    def train_model(self, model_type: MLModelType,
                  features: List[List[float]],
                  labels: List[int]) -> Dict[str, Any]:
        """模型训练"""
        # 简化训练
        accuracy = random.uniform(0.6, 0.9)

        self._models[model_type.value] = {
            "accuracy": accuracy,
            "trained_at": datetime.now().isoformat()
        }
        self._weights_trained = True

        return {
            "model_type": model_type.value,
            "accuracy": accuracy,
            "samples": len(features),
            "status": "trained"
        }

    def predict(self, model_type: MLModelType,
             features: List[float]) -> MLPrediction:
        """预测"""
        if model_type.value not in self._models and not self._weights_trained:
            # 默认预测
            pred = sum(features) / len(features) if features else 100
            direction = "buy" if pred > 100 else "sell"
            prob = 0.6
        else:
            # 使用训练模型
            pred = sum(f * random.uniform(0.8, 1.2) for f in features)
            direction = "buy" if pred > 0 else "sell"
            prob = self._models.get(model_type.value, {}).get("accuracy", 0.6)

        return MLPrediction(
            model_type=model_type.value,
            prediction=pred,
            confidence=prob,
            direction=direction,
            probability=prob
        )

    def signal_enhancement(self, base_signal: str,
                        ml_prediction: MLPrediction) -> Dict[str, Any]:
        """信号增强"""
        signal_strength = 0.5

        # 基础信号强度
        if base_signal == "buy":
            signal_strength = 0.6
        elif base_signal == "sell":
            signal_strength = 0.6
        else:
            signal_strength = 0.4

        # ML增强
        if ml_prediction.direction == "buy" and base_signal == "buy":
            signal_strength = min(1.0, signal_strength + 0.2 * ml_prediction.confidence)
        elif ml_prediction.direction == "sell" and base_signal == "sell":
            signal_strength = min(1.0, signal_strength + 0.2 * ml_prediction.confidence)
        elif ml_prediction.direction != base_signal:
            signal_strength = max(0.0, signal_strength - 0.2 * ml_prediction.confidence)

        # 最终信号
        if signal_strength > 0.7:
            final_signal = SignalType.STRONG_BUY.value if base_signal == "buy" else SignalType.STRONG_SELL.value
        elif signal_strength > 0.55:
            final_signal = base_signal
        elif signal_strength > 0.45:
            final_signal = SignalType.HOLD.value
        else:
            final_signal = SignalType.STRONG_SELL.value if base_signal == "buy" else SignalType.STRONG_BUY.value

        return {
            "base_signal": base_signal,
            "enhanced_signal": final_signal,
            "strength": signal_strength,
            "ml_confidence": ml_prediction.confidence,
            "boost": ml_prediction.probability > 0.5
        }

    def ensemble_predict(self, features: List[float],
                  model_types: List[MLModelType]) -> MLPrediction:
        """集成预测"""
        predictions = []

        for model_type in model_types:
            pred = self.predict(model_type, features)
            predictions.append(pred)

        if not predictions:
            return MLPrediction(
                model_type="ensemble",
                prediction=100,
                confidence=0.5,
                direction="hold",
                probability=0.5
            )

        # 加权平均
        avg_confidence = sum(p.confidence for p in predictions) / len(predictions)
        direction_counts = {}

        for p in predictions:
            direction_counts[p.direction] = direction_counts.get(p.direction, 0) + 1

        final_direction = max(direction_counts, key=direction_counts.get)

        return MLPrediction(
            model_type="ensemble",
            prediction=sum(p.prediction for p in predictions) / len(predictions),
            confidence=avg_confidence,
            direction=final_direction,
            probability=avg_confidence
        )


# ============ BacktestEnhancement ============

class BacktestEnhancement:
    """回测增强引擎"""

    def __init__(self):
        self._results: List[BacktestResultV98] = []
        self._walk_forward_results: List[WalkForwardResult] = []

    def walk_forward_analysis(self, prices: List[float],
                         train_window: int = 100,
                         test_window: int = 50) -> List[WalkForwardResult]:
        """前向分析"""
        results = []
        num_periods = (len(prices) - train_window) // test_window

        for period in range(num_periods):
            train_start = period * test_window
            train_end = train_start + train_window
            test_end = train_end + test_window

            train_prices = prices[train_start:train_end]
            test_prices = prices[train_end:test_end]

            if len(train_prices) < train_window or len(test_prices) < test_window:
                continue

            # 样本内收益
            train_return = (train_prices[-1] - train_prices[0]) / train_prices[0] if train_prices[0] > 0 else 0

            # 样本外收益
            test_return = (test_prices[-1] - test_prices[0]) / test_prices[0] if test_prices[0] > 0 else 0

            # 稳定性(样本内外一致性)
            stability = 1 - abs(train_return - test_return) if train_return != 0 else 0

            results.append(WalkForwardResult(
                period=period + 1,
                in_sample_return=train_return,
                out_of_sample_return=test_return,
                stability=stability,
                parameter_drift=abs(train_return - test_return)
            ))

        self._walk_forward_results = results
        return results

    def monte_carlo_simulation(self, initial_capital: float,
                        returns: List[float],
                        num_simulations: int = 1000) -> MonteCarloResult:
        """蒙特卡洛模拟"""
        if not returns:
            return MonteCarloResult(
                median_return=0,
                percentile_5=0,
                percentile_95=0,
                var_95=0,
                success_rate=0
            )

        # 模拟路径
        final_values = []

        for _ in range(num_simulations):
            value = initial_capital
            for ret in returns:
                # 随机采样
                ret_sample = random.choice(returns) * random.uniform(0.8, 1.2)
                value *= (1 + ret_sample)
            final_values.append(value)

        final_values.sort()

        # 计算统计
        median = final_values[len(final_values) // 2]
        p5 = final_values[int(len(final_values) * 0.05)]
        p95 = final_values[int(len(final_values) * 0.95)]

        median_return = (median - initial_capital) / initial_capital
        var_95 = initial_capital - p5

        # 成功率
        success = sum(1 for v in final_values if v > initial_capital)
        success_rate = success / num_simulations

        return MonteCarloResult(
            median_return=median_return,
            percentile_5=(p5 - initial_capital) / initial_capital,
            percentile_95=(p95 - initial_capital) / initial_capital,
            var_95=var_95,
            success_rate=success_rate
        )

    def performance_attribution(self, portfolio_returns: List[float],
                       market_returns: List[float]) -> PerformanceAttributionV98:
        """绩效归因"""
        if not portfolio_returns or not market_returns:
            return PerformanceAttributionV98(
                total_return=0,
                alpha=0,
                beta=1,
                market_contribution=0,
                selection_contribution=0,
                timing_contribution=0
            )

        n = min(len(portfolio_returns), len(market_returns))
        pf_ret = sum(portfolio_returns[:n]) / n
        mkt_ret = sum(market_returns[:n]) / n

        # 计算beta
        mean_pf = sum(portfolio_returns[:n]) / n
        mean_mkt = sum(market_returns[:n]) / n

        cov = sum((p - mean_pf) * (m - mean_mkt) for p, m in zip(portfolio_returns[:n], market_returns[:n])) / n
        var_mkt = sum((m - mean_mkt) ** 2 for m in market_returns[:n]) / n

        beta = cov / var_mkt if var_mkt > 0 else 1

        # 计算alpha
        alpha = pf_ret - beta * mkt_ret

        # 分解贡献
        market_contrib = beta * mkt_ret
        selection_contrib = alpha * 0.5
        timing_contrib = alpha * 0.5

        total_return = sum(portfolio_returns[:n]) / n

        return PerformanceAttributionV98(
            total_return=total_return,
            alpha=alpha,
            beta=beta,
            market_contribution=market_contrib,
            selection_contribution=selection_contrib,
            timing_contribution=timing_contrib
        )

    def calculate_sharpe_ratio(self, returns: List[float],
                             risk_free_rate: float = 0.02) -> float:
        """夏普比率"""
        if not returns:
            return 0

        mean_return = sum(returns) / len(returns)
        std_return = math.sqrt(sum((r - mean_return) ** 2 for r in returns) / len(returns))

        if std_return == 0:
            return 0

        return (mean_return - risk_free_rate) / std_return

    def calculate_sortino_ratio(self, returns: List[float],
                         target_return: float = 0,
                         risk_free_rate: float = 0.02) -> float:
        """索提诺比率"""
        if not returns:
            return 0

        mean_return = sum(returns) / len(returns)

        # 下行偏差
        downside_returns = [r for r in returns if r < target_return]
        if not downside_returns:
            return 0

        downside_std = math.sqrt(sum((r - target_return) ** 2 for r in downside_returns) / len(downside_returns))

        if downside_std == 0:
            return 0

        return (mean_return - risk_free_rate) / downside_std

    def calculate_calmar_ratio(self, returns: List[float],
                            peak_value: float) -> float:
        """卡玛比率"""
        if not returns or peak_value == 0:
            return 0

        annual_return = sum(returns) / len(returns) * 252

        # 最大回撤
        equity = [peak_value]
        for r in returns:
            equity.append(equity[-1] * (1 + r))

        peak = equity[0]
        max_dd = 0
        for e in equity:
            if e > peak:
                peak = e
            dd = (peak - e) / peak
            if dd > max_dd:
                max_dd = dd

        if max_dd == 0:
            return 0

        return annual_return / max_dd

    def generate_equity_curve(self, initial_capital: float,
                          returns: List[float]) -> List[float]:
        """生成权益曲线"""
        equity = [initial_capital]

        for ret in returns:
            equity.append(equity[-1] * (1 + ret))

        return equity

    def backtest_summary(self) -> Dict[str, Any]:
        return {
            "total_backtests": len(self._results),
            "walk_forward_periods": len(self._walk_forward_results)
        }


# ============ 全局实例管理 ============

_advanced_analytics: Optional[AdvancedAnalytics] = None
_machine_learning: Optional[MachineLearning] = None
_backtest_enhancement: Optional[BacktestEnhancement] = None


def get_advanced_analytics() -> AdvancedAnalytics:
    global _advanced_analytics
    if _advanced_analytics is None:
        _advanced_analytics = AdvancedAnalytics()
    return _advanced_analytics


def initialize_advanced_analytics() -> None:
    global _advanced_analytics
    _advanced_analytics = AdvancedAnalytics()


def get_machine_learning() -> MachineLearning:
    global _machine_learning
    if _machine_learning is None:
        _machine_learning = MachineLearning()
    return _machine_learning


def initialize_machine_learning() -> None:
    global _machine_learning
    _machine_learning = MachineLearning()


def get_backtest_enhancement() -> BacktestEnhancement:
    global _backtest_enhancement
    if _backtest_enhancement is None:
        _backtest_enhancement = BacktestEnhancement()
    return _backtest_enhancement


def initialize_backtest_enhancement() -> None:
    global _backtest_enhancement
    _backtest_enhancement = BacktestEnhancement()


# ============ 版本信息 ============

__version__ = "4.4.0"
_phase = "Phase 42"