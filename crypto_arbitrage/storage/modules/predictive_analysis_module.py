"""预测分析模块 V5.8 - 专注基于历史模式的预测性分析

核心职责：
1. 历史模式识别 - 从历史知识中识别价格和交易模式
2. 趋势预测分析 - 基于模式预测市场趋势
3. 置信度评估 - 评估预测的可靠性和准确性
4. 套利机会预测 - 预测潜在的套利机会

预测类型：
- short_term: 短期预测（小时级别）
- medium_term: 中期预测（天级别）
- long_term: 长期预测（周级别）

设计原则：
- 单一职责：专注预测分析功能
- 高内聚性：所有方法都围绕预测展开
- 数据驱动：基于历史数据进行预测
- 可验证性：预测结果可验证和跟踪

基于：V5.7 Graphify架构优化分析
内聚性目标：0.48+
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class PredictiveAnalysisModule:
    """预测分析模块 - 专注基于历史模式的预测性分析

    提供智能的市场预测功能，基于历史知识模式识别
    和趋势分析，为交易决策提供预测性支持。
    """

    def __init__(self, config: Dict[str, Any], semantic_search_module):
        """初始化预测分析模块

        Args:
            config: 配置字典，包含：
                - enable_predictive_analysis: 是否启用预测分析
                - supported_time_horizons: 支持的时间视野
                - min_confidence_threshold: 最小置信度阈值
                - max_pattern_queries: 最大模式查询数量
                - prediction_cache_ttl: 预测缓存TTL
            semantic_search_module: 语义搜索模块实例
        """
        self.config = config
        self.enable_predictive_analysis = config.get('enable_predictive_analysis', True)
        self.semantic_search_module = semantic_search_module

        # 预测配置
        self._supported_time_horizons = config.get('supported_time_horizons', [
            'short_term',
            'medium_term',
            'long_term'
        ])

        self._min_confidence_threshold = config.get('min_confidence_threshold', 0.5)
        self._max_pattern_queries = config.get('max_pattern_queries', 10)

        # 预测缓存
        self._prediction_cache: Dict[str, Dict[str, Any]] = {}
        self._prediction_cache_ttl = config.get('prediction_cache_ttl', 600)  # 10分钟

        # 性能统计
        self._stats = {
            'total_predictions': 0,
            'predictions_by_horizon': defaultdict(int),
            'avg_confidence': 0.0,
            'high_confidence_count': 0,
            'pattern_discovery_rate': 0.0
        }

        logger.info("[OK] 预测分析模块 V5.8 初始化完成")

    async def predictive_analysis(
        self,
        symbol: str = "BTC/USDT",
        time_horizon: str = "short_term"
    ) -> Dict[str, Any]:
        """预测性分析 - 基于历史模式

        Args:
            symbol: 交易对
            time_horizon: 时间视野 [short_term, medium_term, long_term]

        Returns:
            预测分析字典
        """
        if not self.enable_predictive_analysis:
            return {
                'enabled': False,
                'message': '预测分析未启用'
            }

        # 验证时间视野
        if time_horizon not in self._supported_time_horizons:
            logger.warning(f"不支持的时间视野: {time_horizon}")
            return {
                'error': f'不支持的时间视野: {time_horizon}',
                'supported_horizons': self._supported_time_horizons
            }

        # 检查缓存
        cache_key = f"{symbol}:{time_horizon}"
        cached = self._get_prediction_from_cache(cache_key)
        if cached is not None:
            logger.debug(f"预测缓存命中: {cache_key}")
            return cached

        # 更新统计
        self._stats['total_predictions'] += 1
        self._stats['predictions_by_horizon'][time_horizon] += 1

        # 执行预测
        try:
            result = await self._execute_prediction(symbol, time_horizon)
            self._update_prediction_stats(result)

            # 缓存结果
            if result.get('enabled', False):
                self._cache_prediction(cache_key, result)

            return result
        except Exception as e:
            logger.error(f"预测分析失败: {e}")
            return {
                'error': str(e),
                'symbol': symbol,
                'time_horizon': time_horizon
            }

    async def _execute_prediction(
        self,
        symbol: str,
        time_horizon: str
    ) -> Dict[str, Any]:
        """执行预测

        Args:
            symbol: 交易对
            time_horizon: 时间视野

        Returns:
            预测结果
        """
        # 搜索相关历史模式
        patterns = await self._discover_historical_patterns(symbol, time_horizon)

        # 分析模式
        analysis = self._analyze_patterns(patterns, symbol)

        # 计算置信度
        confidence = self._calculate_confidence(patterns, analysis)

        # 生成预测
        prediction = self._generate_prediction(analysis, confidence, time_horizon)

        result = {
            'enabled': True,
            'symbol': symbol,
            'time_horizon': time_horizon,
            'pattern_count': len(patterns),
            'analysis': analysis,
            'confidence': confidence,
            'prediction': prediction,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'meets_threshold': confidence >= self._min_confidence_threshold
        }

        return result

    async def _discover_historical_patterns(
        self,
        symbol: str,
        time_horizon: str
    ) -> List[Dict[str, Any]]:
        """发现历史模式

        Args:
            symbol: 交易对
            time_horizon: 时间视野

        Returns:
            模式列表
        """
        # 根据时间视野生成不同的查询
        if time_horizon == "short_term":
            pattern_queries = [
                f"{symbol} 短期价格模式",
                f"{symbol} 小时级别波动",
                f"{symbol} 即时套利机会",
                "短期市场趋势"
            ]
        elif time_horizon == "medium_term":
            pattern_queries = [
                f"{symbol} 中期价格趋势",
                f"{symbol} 日级别波动规律",
                f"{symbol} 中期套利策略",
                "中期市场分析"
            ]
        else:  # long_term
            pattern_queries = [
                f"{symbol} 长期价格趋势",
                f"{symbol} 周级别波动模式",
                f"{symbol} 长期投资机会",
                "长期市场展望"
            ]

        # 限制查询数量
        pattern_queries = pattern_queries[:self._max_pattern_queries]

        # 并行搜索模式
        search_tasks = []
        for query in pattern_queries:
            task = self.semantic_search_module.semantic_search(query, top_k=3)
            search_tasks.append(task)

        # 等待所有搜索完成
        query_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # 收集有效结果
        patterns = []
        for results in query_results:
            if isinstance(results, list):
                patterns.extend(results)
            elif isinstance(results, Exception):
                logger.error(f"模式搜索失败: {results}")

        return patterns

    def _analyze_patterns(
        self,
        patterns: List[Dict[str, Any]],
        symbol: str
    ) -> Dict[str, Any]:
        """分析模式

        Args:
            patterns: 模式列表
            symbol: 交易对

        Returns:
            分析结果字典
        """
        analysis = {
            'trend': 'neutral',
            'volatility': 'medium',
            'opportunity': 'normal',
            'signals': [],
            'key_factors': [],
            'risk_level': 'medium'
        }

        # 统计信号
        signal_counts = defaultdict(int)

        for pattern in patterns:
            content = pattern.get('content', '').lower()

            # 趋势分析
            if any(keyword in content for keyword in ['上涨', 'bullish', '看涨', '突破']):
                signal_counts['bullish'] += 1
                analysis['signals'].append('上涨信号')
            elif any(keyword in content for keyword in ['下跌', 'bearish', '看跌', '跌破']):
                signal_counts['bearish'] += 1
                analysis['signals'].append('下跌信号')

            # 波动性分析
            if any(keyword in content for keyword in ['高波动', 'volatile', '剧烈波动']):
                analysis['volatility'] = 'high'
            elif any(keyword in content for keyword in ['低波动', 'stable', '稳定']):
                analysis['volatility'] = 'low'

            # 机会分析
            if any(keyword in content for keyword in ['机会', 'arbitrage', '套利', '利润']):
                analysis['opportunity'] = 'high'
                analysis['key_factors'].append('套利机会')

            # 风险分析
            if any(keyword in content for keyword in ['风险', '危险', '谨慎', '避险']):
                if analysis['risk_level'] != 'high':
                    analysis['risk_level'] = 'high'
                analysis['key_factors'].append('风险因素')

        # 确定主要趋势
        if signal_counts['bullish'] > signal_counts['bearish']:
            analysis['trend'] = 'bullish'
        elif signal_counts['bearish'] > signal_counts['bullish']:
            analysis['trend'] = 'bearish'

        # 如果没有明确信号，保持中性
        if not analysis['signals']:
            analysis['signals'].append('无明显信号')

        return analysis

    def _calculate_confidence(
        self,
        patterns: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> float:
        """计算预测置信度

        Args:
            patterns: 模式列表
            analysis: 分析结果

        Returns:
            置信度 (0-1)
        """
        if not patterns:
            return 0.0

        # 因素1: 模式数量 (最多10个模式得满分)
        pattern_factor = min(1.0, len(patterns) / 10)

        # 因素2: 平均相关性分数
        avg_score = sum(p.get('score', 0) for p in patterns) / len(patterns)

        # 因素3: 信号一致性
        signal_factor = self._calculate_signal_consistency(analysis)

        # 因素4: 机会明确性
        opportunity_factor = 1.0 if analysis.get('opportunity') == 'high' else 0.7

        # 综合计算
        confidence = (
            pattern_factor * 0.3 +
            avg_score * 0.3 +
            signal_factor * 0.2 +
            opportunity_factor * 0.2
        )

        return round(confidence, 3)

    def _calculate_signal_consistency(self, analysis: Dict[str, Any]) -> float:
        """计算信号一致性

        Args:
            analysis: 分析结果

        Returns:
            一致性分数 (0-1)
        """
        signals = analysis.get('signals', [])

        if not signals or len(signals) <= 1:
            return 0.5

        # 计算信号的一致性
        bullish_count = sum(1 for s in signals if '上涨' in s or 'bullish' in s.lower())
        bearish_count = sum(1 for s in signals if '下跌' in s or 'bearish' in s.lower())

        total_signals = bullish_count + bearish_count

        if total_signals == 0:
            return 0.5

        # 一致性高的情况
        if bullish_count == 0 or bearish_count == 0:
            return 1.0

        # 一致性低的情况
        max_count = max(bullish_count, bearish_count)
        consistency = max_count / total_signals

        return consistency

    def _generate_prediction(
        self,
        analysis: Dict[str, Any],
        confidence: float,
        time_horizon: str
    ) -> Dict[str, Any]:
        """生成预测

        Args:
            analysis: 分析结果
            confidence: 置信度
            time_horizon: 时间视野

        Returns:
            预测字典
        """
        prediction = {
            'trend_forecast': analysis['trend'],
            'volatility_forecast': analysis['volatility'],
            'opportunity_level': analysis['opportunity'],
            'actionable_insights': [],
            'risk_assessment': analysis['risk_level'],
            'recommended_actions': []
        }

        # 根据趋势生成建议
        if analysis['trend'] == 'bullish' and confidence > 0.6:
            prediction['recommended_actions'].append('考虑做多或等待回调买入')
        elif analysis['trend'] == 'bearish' and confidence > 0.6:
            prediction['recommended_actions'].append('考虑做空或减仓避险')

        # 根据机会生成建议
        if analysis['opportunity'] == 'high' and confidence > 0.7:
            prediction['actionable_insights'].append('检测到较高套利机会，建议关注')
            prediction['recommended_actions'].append('可考虑加大套利仓位')

        # 根据波动性生成建议
        if analysis['volatility'] == 'high':
            prediction['actionable_insights'].append('市场波动较大，注意风险控制')
            prediction['recommended_actions'].append('建议设置更严格的止损')

        # 根据时间视野调整建议
        if time_horizon == 'short_term':
            prediction['time_frame'] = '小时级别'
            prediction['actionable_insights'].append('短期预测，建议密切监控')
        elif time_horizon == 'medium_term':
            prediction['time_frame'] = '天级别'
            prediction['actionable_insights'].append('中期预测，可适度持仓')
        else:  # long_term
            prediction['time_frame'] = '周级别'
            prediction['actionable_insights'].append('长期预测，适合策略性布局')

        return prediction

    def _get_prediction_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取预测

        Args:
            cache_key: 缓存键

        Returns:
            缓存的预测或None
        """
        if cache_key not in self._prediction_cache:
            return None

        cached = self._prediction_cache[cache_key]

        # 检查是否过期
        import time
        if time.time() - cached['timestamp'] > self._prediction_cache_ttl:
            del self._prediction_cache[cache_key]
            return None

        return cached['prediction']

    def _cache_prediction(self, cache_key: str, prediction: Dict[str, Any]) -> None:
        """缓存预测

        Args:
            cache_key: 缓存键
            prediction: 预测结果
        """
        import time
        self._prediction_cache[cache_key] = {
            'prediction': prediction,
            'timestamp': time.time()
        }

    def _update_prediction_stats(self, result: Dict[str, Any]) -> None:
        """更新预测统计

        Args:
            result: 预测结果
        """
        confidence = result.get('confidence', 0.0)

        # 更新平均置信度
        total_predictions = self._stats['total_predictions']
        current_avg = self._stats['avg_confidence']
        self._stats['avg_confidence'] = (
            (current_avg * (total_predictions - 1) + confidence) / total_predictions
        )

        # 更新高置信度计数
        if confidence >= self._min_confidence_threshold:
            self._stats['high_confidence_count'] += 1

        # 更新模式发现率
        pattern_count = result.get('pattern_count', 0)
        max_patterns = self._max_pattern_queries * 3  # 每个查询最多3个结果
        discovery_rate = pattern_count / max_patterns if max_patterns > 0 else 0

        # 更新平均发现率
        current_rate = self._stats['pattern_discovery_rate']
        self._stats['pattern_discovery_rate'] = (
            (current_rate * (total_predictions - 1) + discovery_rate) / total_predictions
        )

    def get_prediction_stats(self) -> Dict[str, Any]:
        """获取预测统计

        Returns:
            预测统计数据
        """
        total_predictions = self._stats['total_predictions']
        high_conf_rate = (
            self._stats['high_confidence_count'] / total_predictions
            if total_predictions > 0 else 0
        )

        return {
            'total_predictions': total_predictions,
            'predictions_by_horizon': dict(self._stats['predictions_by_horizon']),
            'avg_confidence': self._stats['avg_confidence'],
            'high_confidence_rate': high_conf_rate,
            'high_confidence_count': self._stats['high_confidence_count'],
            'pattern_discovery_rate': self._stats['pattern_discovery_rate']
        }

    def clear_cache(self) -> None:
        """清除预测缓存"""
        self._prediction_cache.clear()
        logger.info("预测分析缓存已清除")

    def reset_stats(self) -> None:
        """重置统计"""
        self._stats = {
            'total_predictions': 0,
            'predictions_by_horizon': defaultdict(int),
            'avg_confidence': 0.0,
            'high_confidence_count': 0,
            'pattern_discovery_rate': 0.0
        }
        logger.info("预测分析统计已重置")


def create_predictive_analysis_module(
    config: Dict[str, Any],
    semantic_search_module
) -> PredictiveAnalysisModule:
    """创建预测分析模块

    Args:
        config: 配置字典
        semantic_search_module: 语义搜索模块实例

    Returns:
        预测分析模块实例
    """
    return PredictiveAnalysisModule(config, semantic_search_module)
