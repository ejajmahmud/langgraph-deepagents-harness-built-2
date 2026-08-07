"""V54.0 跨链套利与ML预测集成系统

V54.0 新增功能:
1. Cross-Chain Arbitrage Engine - 跨链套利引擎（ETH/BSC/SOL/Base等）
2. Bridge Arbitrage - 跨链桥套利
3. ML Price Predictor - ML价格预测
4. Arbitrage Opportunity Predictor - 套利机会预测
5. Signal Quality Predictor - 信号质量预测

创建时间：2026-05-08
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# 支持的区块链
class Blockchain(Enum):
    """区块链枚举"""
    ETHEREUM = "ethereum"
    BNB_CHAIN = "bnb"
    SOLANA = "solana"
    BASE = "base"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    POLYGON = "polygon"
    AVALANCHE = "avalanche"


# 跨链套利类型
class CrossChainArbitrageType(Enum):
    """跨链套利类型"""
    DIRECT = "direct"           # 直接跨链价差
    BRIDGE = "bridge"          # 跨链桥套利
    WRAPPED = "wrapped"         # 包装资产套利
    LIQUIDITY = "liquidity"      # 流动性套利


@dataclass
class CrossChainToken:
    """跨链代币"""
    symbol: str
    name: str
    blockchain: Blockchain
    contract_address: str
    decimals: int
    price_usd: float = 0.0
    liquidity: float = 0.0


@dataclass
class CrossChainOpportunity:
    """跨链套利机会"""
    opportunity_id: str
    arbitrage_type: CrossChainArbitrageType
    token: str
    source_chain: Blockchain
    target_chain: Blockchain
    source_price: float
    target_price: float
    spread: float
    spread_pct: float
    volume_available: float
    expected_profit: float
    bridge_time: int  # 跨链时间(秒)
    risk_score: float
    confidence: float
    ml_prediction: float = 0.0
    timestamp: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 60)


@dataclass
class MLPredictionResult:
    """ML预测结果"""
    prediction: float
    confidence: float
    model_name: str
    features_used: List[str]
    prediction_type: str
    timestamp: float = field(default_factory=time.time)


class CrossChainArbitrageEngine:
    """跨链套利引擎

    功能：
    - 多链价格监控
    - 跨链套利机会检测
    - 跨链桥费率计算
    - 利润优化
    - ML机会预测
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化跨链套利引擎

        Args:
            config: 配置字典
                - min_spread_pct: 最小价差百分比 (默认 0.5%)
                - min_volume: 最小成交量 (默认 1000)
                - max_bridge_time: 最大跨链时间(秒) (默认 600)
                - supported_chains: 支持的链列表
        """
        self.config = config or {}

        # 核心参数
        self.min_spread_pct = self.config.get('min_spread_pct', 0.5)
        self.min_volume = self.config.get('min_volume', 1000)
        self.max_bridge_time = self.config.get('max_bridge_time', 600)

        # 支持的链
        supported = self.config.get('supported_chains',
            ['ethereum', 'bnb', 'solana', 'base', 'arbitrum'])
        self.supported_chains = [Blockchain(c) for c in supported]

        # 代币数据库
        self.token_db: Dict[str, Dict[Blockchain, CrossChainToken]] = {}

        # 价格缓存
        self.price_cache: Dict[str, Dict[Blockchain, float]] = {}

        # 历史机会
        self.opportunity_history: List[CrossChainOpportunity] = []

        # ML预测器
        self.ml_predictor: Optional[MLPredictor] = None

        # 统计
        self.total_opportunities = 0
        self.executed_trades = 0

        logger.info(f"跨链套利引擎 V54.0 初始化完成，支持链: {supported}")

    def register_token(self, token: CrossChainToken) -> None:
        """注册跨链代币

        Args:
            token: 跨链代币
        """
        if token.symbol not in self.token_db:
            self.token_db[token.symbol] = {}

        self.token_db[token.symbol][token.blockchain] = token
        logger.info(f"注册代币: {token.symbol} on {token.blockchain.value}")

    def update_price(
        self,
        token_symbol: str,
        blockchain: Blockchain,
        price: float,
        liquidity: float = 0.0
    ) -> None:
        """更新代币价格

        Args:
            token_symbol: 代币符号
            blockchain: 区块链
            price: 价格(USD)
            liquidity: 流动性
        """
        if token_symbol not in self.price_cache:
            self.price_cache[token_symbol] = {}

        self.price_cache[token_symbol][blockchain] = {
            'price': price,
            'liquidity': liquidity,
            'timestamp': time.time()
        }

    def detect_opportunities(self) -> List[CrossChainOpportunity]:
        """检测跨链套利机会

        Returns:
            机会列表
        """
        opportunities = []

        # 遍历所有代币对
        for token_symbol, prices in self.price_cache.items():
            if len(prices) < 2:
                continue

            # 获取所有链的价格
            chain_prices = []
            for chain, data in prices.items():
                if chain in self.supported_chains:
                    chain_prices.append({
                        'chain': chain,
                        'price': data['price'],
                        'liquidity': data.get('liquidity', 0)
                    })

            if len(chain_prices) < 2:
                continue

            # 检测价差机会
            for i, source in enumerate(chain_prices):
                for target in chain_prices[i+1:]:
                    opp = self._check_arbitrage(
                        token_symbol,
                        source,
                        target
                    )
                    if opp:
                        opportunities.append(opp)

        # 更新统计
        self.total_opportunities += len(opportunities)
        self.opportunity_history.extend(opportunities)

        # 保留最近100个
        self.opportunity_history = self.opportunity_history[-100:]

        return opportunities

    def _check_arbitrage(
        self,
        token_symbol: str,
        source: Dict[str, Any],
        target: Dict[str, Any]
    ) -> Optional[CrossChainOpportunity]:
        """检查套利机会

        Args:
            token_symbol: 代币符号
            source: 源链数据
            target: 目标链数据

        Returns:
            套利机会或None
        """
        source_price = source['price']
        target_price = target['price']

        # 计算价差
        spread = abs(target_price - source_price)
        spread_pct = spread / source_price * 100

        # 检查是否满足条件
        if spread_pct < self.min_spread_pct:
            return None

        # 计算成交量限制
        volume = min(
            source.get('liquidity', float('inf')),
            target.get('liquidity', float('inf'))
        )
        if volume < self.min_volume:
            return None

        # 估计预期利润（扣除跨链费用）
        expected_profit = spread * min(volume, 10000) * 0.9  # 预留10%费用

        # 估计风险评分
        risk_score = self._estimate_risk(
            source['chain'],
            target['chain']
        )

        # ML预测
        ml_prediction = 0.0
        if self.ml_predictor:
            try:
                ml_prediction = self.ml_predictor.predict_opportunity(
                    token_symbol,
                    source['chain'].value,
                    target['chain'].value,
                    spread_pct
                )
            except Exception as e:
                logger.warning(f"ML预测失败: {e}")

        # 计算置信度
        confidence = self._calculate_confidence(
            spread_pct,
            volume,
            risk_score,
            ml_prediction
        )

        return CrossChainOpportunity(
            opportunity_id=f"cca_{int(time.time() * 1000)}",
            arbitrage_type=CrossChainArbitrageType.DIRECT,
            token=token_symbol,
            source_chain=source['chain'],
            target_chain=target['chain'],
            source_price=source_price,
            target_price=target_price,
            spread=spread,
            spread_pct=spread_pct,
            volume_available=volume,
            expected_profit=expected_profit,
            bridge_time=300,  # 默认5分钟
            risk_score=risk_score,
            confidence=confidence,
            ml_prediction=ml_prediction
        )

    def _estimate_risk(
        self,
        source_chain: Blockchain,
        target_chain: Blockchain
    ) -> float:
        """估计跨链风险

        Args:
            source_chain: 源链
            target_chain: 目标链

        Returns:
            风险评分 (0-1)
        """
        # 高风险链对
        high_risk_pairs = [
            (Blockchain.SOLANA, Blockchain.ETHEREUM),
            (Blockchain.SOLANA, Blockchain.BNB_CHAIN),
        ]

        # 中风险链对
        medium_risk_pairs = [
            (Blockchain.BASE, Blockchain.ETHEREUM),
            (Blockchain.ARBITRUM, Blockchain.ETHEREUM),
            (Blockchain.OPTIMISM, Blockchain.ETHEREUM),
        ]

        pair = (source_chain, target_chain)
        reverse_pair = (target_chain, source_chain)

        if pair in high_risk_pairs or reverse_pair in high_risk_pairs:
            return 0.7
        elif pair in medium_risk_pairs or reverse_pair in medium_risk_pairs:
            return 0.4

        return 0.2

    def _calculate_confidence(
        self,
        spread_pct: float,
        volume: float,
        risk_score: float,
        ml_prediction: float
    ) -> float:
        """计算置信度

        Args:
            spread_pct: 价差百分比
            volume: 成交量
            risk_score: 风险评分
            ml_prediction: ML预测

        Returns:
            置信度 (0-1)
        """
        # 价差评分
        spread_score = min(spread_pct / 3.0, 1.0)

        # 流动性评分
        volume_score = min(volume / 100000, 1.0)

        # 风险评分 (反向)
        risk_score = 1.0 - risk_score

        # ML评分
        ml_score = ml_prediction if ml_prediction > 0 else 0.5

        # 综合评分
        confidence = (
            spread_score * 0.4 +
            volume_score * 0.2 +
            risk_score * 0.2 +
            ml_score * 0.2
        )

        return min(confidence, 1.0)

    def set_ml_predictor(self, predictor: 'MLPredictor') -> None:
        """设置ML预测器

        Args:
            predictor: ML预测器
        """
        self.ml_predictor = predictor

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计字典
        """
        return {
            'total_opportunities': self.total_opportunities,
            'executed_trades': self.executed_trades,
            'supported_chains': [c.value for c in self.supported_chains],
            'tokens_tracked': len(self.token_db)
        }


class MLPredictor:
    """机器学习预测器

    功能：
    - 价格趋势预测
    - 套利机会预测
    - 信号质量评估
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化ML预测器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 模型配置
        self.model_type = self.config.get('model_type', 'simple')
        self.lookback_periods = self.config.get('lookback_periods', 20)

        # 价格历史
        self.price_history: Dict[str, Dict[Blockchain, List[float]]] = {}

        # 预测缓存
        self.prediction_cache: Dict[str, MLPredictionResult] = {}

        logger.info(f"ML预测器初始化完成，模型类型: {self.model_type}")

    def update_price_history(
        self,
        token_symbol: str,
        blockchain: Blockchain,
        price: float
    ) -> None:
        """更新价格历史

        Args:
            token_symbol: 代币符号
            blockchain: 区块链
            price: 价格
        """
        if token_symbol not in self.price_history:
            self.price_history[token_symbol] = {}

        if blockchain not in self.price_history[token_symbol]:
            self.price_history[token_symbol][blockchain] = []

        # 添加新价格，保留历史
        self.price_history[token_symbol][blockchain].append(price)

        # 保留最近N个
        self.price_history[token_symbol][blockchain] = \
            self.price_history[token_symbol][blockchain][-self.lookback_periods:]

    def predict_price(
        self,
        token_symbol: str,
        blockchain: Blockchain,
        periods: int = 1
    ) -> MLPredictionResult:
        """预测价格

        Args:
            token_symbol: 代币符号
            blockchain: 区块链
            periods: 预测周期数

        Returns:
            预测结果
        """
        if token_symbol not in self.price_history:
            return MLPredictionResult(
                prediction=0.0,
                confidence=0.0,
                model_name=self.model_type,
                features_used=[],
                prediction_type='price'
            )

        prices = self.price_history[token_symbol].get(blockchain, [])
        if len(prices) < 5:
            return MLPredictionResult(
                prediction=prices[-1] if prices else 0.0,
                confidence=0.0,
                model_name=self.model_type,
                features_used=[],
                prediction_type='price'
            )

        # 简单移动平均预测
        recent = prices[-min(5, len(prices)):]
        prediction = np.mean(recent)

        # 计算趋势
        if len(recent) >= 3:
            trend = (recent[-1] - recent[0]) / len(recent)
            prediction += trend * periods

        # V56.1增强：添加指数加权移动平均 (EWMA)
        if len(prices) >= 5:
            # 计算权重
            weights = np.exp(np.linspace(-1., 0., len(prices)))
            weights = weights / weights.sum()
            ewma = np.average(prices, weights=weights)
            # 结合SMA和EWMA
            prediction = 0.6 * prediction + 0.4 * ewma

        # V56.1增强：添加动量指标
        momentum = 0.0
        if len(prices) >= 10:
            # RSI风格动量
            gains = []
            losses = []
            for i in range(1, min(10, len(prices))):
                change = prices[-i] - prices[-(i+1)]
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))

            if gains and losses:
                avg_gain = np.mean(gains)
                avg_loss = np.mean(losses)
                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    # 将RSI动量添加到预测
                    momentum = (rsi - 50) / 100 * 0.1  # ±5%影响
                    prediction *= (1 + momentum)

        # 置信度基于历史数据量
        confidence = min(len(prices) / 20.0, 1.0)

        # V56.1增强：添加更多特征使用记录
        features = ['sma', 'trend']
        if len(prices) >= 5:
            features.append('ewma')
        if len(prices) >= 10:
            features.append('momentum')

        return MLPredictionResult(
            prediction=prediction,
            confidence=confidence,
            model_name=self.model_type,
            features_used=features,
            prediction_type='price'
        )

    def predict_opportunity(
        self,
        token_symbol: str,
        source_chain: str,
        target_chain: str,
        current_spread: float
    ) -> float:
        """预测套利机会

        Args:
            token_symbol: 代币符号
            source_chain: 源链
            target_chain: 目标链
            current_spread: 当前价差

        Returns:
            预测概率 (0-1)
        """
        # 简化的机会预测
        # 基于历史价差模式

        if token_symbol not in self.price_history:
            return 0.5

        # 默认预测概率
        base_probability = 0.5

        # 调整因子
        adjustment = 0.0

        # 检查数据量
        for chain, prices in self.price_history[token_symbol].items():
            if len(prices) >= 10:
                # 计算波动性
                volatility = np.std(prices) / np.mean(prices) if prices else 0
                adjustment += volatility * 10

        probability = min(base_probability + adjustment, 0.95)

        return probability

    def predict_signal_quality(
        self,
        opportunity_data: Dict[str, Any]
    ) -> MLPredictionResult:
        """预测信号质量

        Args:
            opportunity_data: 机会数据

        Returns:
            预测结果
        """
        # 简化实现
        spread = opportunity_data.get('spread_pct', 0)
        volume = opportunity_data.get('volume_available', 0)
        risk = opportunity_data.get('risk_score', 0.5)

        # 基础评分
        score = 0.0

        # 价差贡献
        score += min(spread / 3.0, 1.0) * 0.4

        # 流动性贡献
        score += min(volume / 50000, 1.0) * 0.3

        # 风险贡献 (反向)
        score += (1.0 - risk) * 0.3

        return MLPredictionResult(
            prediction=score,
            confidence=0.7,
            model_name=self.model_type,
            features_used=['spread', 'volume', 'risk'],
            prediction_type='signal_quality'
        )


# 全局单例
_cross_chain_engine: Optional[CrossChainArbitrageEngine] = None
_ml_predictor: Optional[MLPredictor] = None


def initialize_cross_chain_arbitrage_engine(
    config: Optional[Dict[str, Any]] = None
) -> CrossChainArbitrageEngine:
    """初始化跨链套利引擎

    Args:
        config: 配置字典

    Returns:
        跨链套利引擎实例
    """
    global _cross_chain_engine

    _cross_chain_engine = CrossChainArbitrageEngine(config)
    return _cross_chain_engine


def get_cross_chain_arbitrage_engine() -> Optional[CrossChainArbitrageEngine]:
    """获取跨链套利引擎

    Returns:
        跨链套利引擎实例
    """
    return _cross_chain_engine


def initialize_ml_predictor(
    config: Optional[Dict[str, Any]] = None
) -> MLPredictor:
    """初始化ML预测器

    Args:
        config: 配置字典

    Returns:
        ML预测器实例
    """
    global _ml_predictor

    _ml_predictor = MLPredictor(config)
    return _ml_predictor


def get_ml_predictor() -> Optional[MLPredictor]:
    """获取ML预测器

    Returns:
        ML预测器实例
    """
    return _ml_predictor