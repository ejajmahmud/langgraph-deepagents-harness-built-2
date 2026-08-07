"""智能策略增强器 V3.1 - 基于Memo0深度知识的策略优化

核心功能:
1. 策略选择智能增强 - 基于历史成功率优化策略权重
2. 机会智能评分 - 结合市场知识和历史表现
3. 自适应参数调整 - 基于市场状态动态调参
4. 风险评估增强 - 结合历史风险事件评估
"""

import logging
import time
from typing import Any, Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class IntelligentStrategyEnhancer:
    """智能策略增强器 - 基于深度学习的策略优化"""

    def __init__(self, config: Dict[str, Any]):
        """初始化智能策略增强器

        Args:
            config: 配置字典
        """
        self.config = config
        self.enable_smart_scoring = config.get('enable_smart_scoring', True)
        self.enable_adaptive_weights = config.get('enable_adaptive_weights', True)
        self.learning_rate = config.get('learning_rate', 0.1)

        # 历史表现跟踪
        self._strategy_performance: Dict[str, Dict] = defaultdict(lambda: {
            'success_count': 0,
            'failure_count': 0,
            'total_profit': 0.0,
            'last_update': time.time()
        })

        # 基础策略权重
        self._base_weights: Dict[str, float] = config.get('base_weights', {
            'cross_exchange': 0.30,
            'triangular': 0.20,
            'basis_trading': 0.20,
            'funding_rate': 0.20,
            'statistical_arbitrage': 0.10,
        })

        # 当前策略权重
        self._current_weights = self._base_weights.copy()

        logger.info("✅ 智能策略增强器 V3.1 初始化完成")

    async def enhance_opportunities(
        self,
        opportunities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """增强套利机会 - 智能评分和排序

        Args:
            opportunities: 原始机会列表

        Returns:
            增强后的机会列表（包含智能评分）
        """
        if not opportunities or not self.enable_smart_scoring:
            return opportunities

        # 为每个机会计算智能评分
        for opp in opportunities:
            opp['smart_score'] = await self._calculate_smart_score(opp)

        # 按智能评分重新排序
        enhanced = sorted(
            opportunities,
            key=lambda x: x.get('smart_score', x.get('profit_rate', 0)),
            reverse=True
        )

        logger.debug(f"智能增强: {len(opportunities)} 个机会已评分")
        return enhanced

    async def _calculate_smart_score(self, opportunity: Dict[str, Any]) -> float:
        """计算机会的智能评分

        评分因子:
        1. 基础收益率 (40%)
        2. 策略历史表现 (30%)
        3. 市场风险评估 (20%)
        4. 时间因子 (10%)

        Args:
            opportunity: 套利机会

        Returns:
            智能评分 (0-100)
        """
        try:
            # 1. 基础收益率 (40%)
            base_score = min(100, opportunity.get('profit_rate', 0) * 10) * 0.4

            # 2. 策略历史表现 (30%)
            strategy = opportunity.get('strategy', '')
            performance_score = self._get_performance_score(strategy) * 30

            # 3. 市场风险评估 (20%)
            risk_score = await self._assess_market_risk(opportunity) * 20

            # 4. 时间因子 (10%) - 新机会更优
            timestamp = opportunity.get('timestamp', time.time())
            age_factor = max(0, 1 - (time.time() - timestamp) / 300)  # 5分钟内
            time_score = age_factor * 10

            total_score = base_score + performance_score + risk_score + time_score
            return round(total_score, 2)

        except Exception as e:
            logger.error(f"智能评分计算失败: {e}")
            return opportunity.get('profit_rate', 0)

    def _get_performance_score(self, strategy: str) -> float:
        """获取策略表现评分 (0-1)

        基于历史成功率和盈利能力

        Args:
            strategy: 策略名称

        Returns:
            表现评分
        """
        perf = self._strategy_performance.get(strategy, {})
        total = perf.get('success_count', 0) + perf.get('failure_count', 0)

        if total == 0:
            return 0.5  # 无历史数据，返回中性评分

        # 成功率权重 60%
        success_rate = perf.get('success_count', 0) / total
        success_score = success_rate * 0.6

        # 盈利能力权重 40% (归一化到0-1)
        total_profit = perf.get('total_profit', 0)
        profit_score = min(1.0, abs(total_profit) / 100) * 0.4

        return success_score + profit_score

    async def _assess_market_risk(self, opportunity: Dict[str, Any]) -> float:
        """评估市场风险 (0-1, 越低风险越小)

        结合历史风险事件和市场条件

        Args:
            opportunity: 套利机会

        Returns:
            风险评分 (0-1, 0表示低风险)
        """
        try:
            # 查询相关知识库
            from storage.mem0_storage import search_trading_knowledge

            symbol = opportunity.get('symbol', '')
            strategy = opportunity.get('strategy', '')

            # 搜索相关风险事件
            risk_queries = [
                f"风险 {symbol}",
                f"{strategy} 风险",
                "市场波动性",
                "流动性风险"
            ]

            risk_factors = 0
            for query in risk_queries:
                results = search_trading_knowledge(query, top_k=3)
                if results:
                    risk_factors += len(results)

            # 归一化风险因子
            risk_score = min(1.0, risk_factors / 10)
            return 1 - risk_score  # 返回安全评分

        except Exception as e:
            logger.debug(f"风险评估失败: {e}")
            return 0.5  # 默认中等风险

    def record_strategy_result(
        self,
        strategy: str,
        success: bool,
        profit: float = 0.0
    ) -> None:
        """记录策略执行结果，用于学习

        Args:
            strategy: 策略名称
            success: 是否成功
            profit: 利润
        """
        perf = self._strategy_performance[strategy]
        perf['last_update'] = time.time()

        if success:
            perf['success_count'] += 1
            perf['total_profit'] += profit
        else:
            perf['failure_count'] += 1

        # 自适应更新策略权重
        if self.enable_adaptive_weights:
            self._update_adaptive_weights(strategy, success, profit)

    def _update_adaptive_weights(
        self,
        strategy: str,
        success: bool,
        profit: float
    ) -> None:
        """自适应更新策略权重

        基于表现动态调整策略权重

        Args:
            strategy: 策略名称
            success: 是否成功
            profit: 利润
        """
        # 计算该策略的当前表现
        perf = self._strategy_performance[strategy]
        total = perf.get('success_count', 0) + perf.get('failure_count', 0)

        if total < 3:  # 样本太少，不调整权重
            return

        current_rate = perf.get('success_count', 0) / total
        current_weight = self._current_weights.get(strategy, 0)

        # 基于表现调整权重
        if success and profit > 0:
            # 成功且盈利，增加权重
            adjustment = self.learning_rate * (profit / 100)
            new_weight = min(0.5, current_weight + adjustment)
        elif not success:
            # 失败，降低权重
            adjustment = self.learning_rate * current_weight
            new_weight = max(0.05, current_weight - adjustment)
        else:
            return

        # 更新权重并归一化
        self._current_weights[strategy] = new_weight
        self._normalize_weights()

        logger.debug(
            f"权重更新: {strategy} {current_weight:.3f} -> {new_weight:.3f}"
        )

    def _normalize_weights(self) -> None:
        """归一化权重，确保总和为1.0"""
        total = sum(self._current_weights.values())
        if total > 0:
            for strategy in self._current_weights:
                self._current_weights[strategy] /= total

    def get_adaptive_weights(self) -> Dict[str, float]:
        """获取当前自适应权重

        Returns:
            策略权重字典
        """
        return self._current_weights.copy()

    def get_strategy_performance_report(self) -> Dict[str, Dict]:
        """获取策略表现报告

        Returns:
            各策略的表现统计
        """
        report = {}
        for strategy, perf in self._strategy_performance.items():
            total = perf.get('success_count', 0) + perf.get('failure_count', 0)
            report[strategy] = {
                'success_count': perf.get('success_count', 0),
                'failure_count': perf.get('failure_count', 0),
                'total_trades': total,
                'success_rate': (
                    perf.get('success_count', 0) / total if total > 0 else 0
                ),
                'total_profit': perf.get('total_profit', 0.0),
                'current_weight': self._current_weights.get(strategy, 0),
            }
        return report

    async def get_market_intelligence(
        self,
        context: str = "trading"
    ) -> Dict[str, Any]:
        """获取市场智能情报

        基于Memo0知识库提供市场洞察

        Args:
            context: 上下文类型

        Returns:
            市场情报字典
        """
        try:
            from storage.mem0_storage import search_trading_knowledge

            intelligence = {
                'market_conditions': [],
                'risk_factors': [],
                'opportunities': [],
                'warnings': []
            }

            # 查询市场条件知识
            market_queries = [
                "市场趋势",
                "波动性分析",
                "流动性状况",
                "市场情绪"
            ]

            for query in market_queries:
                results = search_trading_knowledge(query, top_k=2)
                for result in results:
                    intelligence['market_conditions'].append({
                        'content': result.get('content', ''),
                        'score': result.get('score', 0)
                    })

            # 查询风险因素
            risk_queries = [
                "近期风险事件",
                "系统性风险",
                "操作风险"
            ]

            for query in risk_queries:
                results = search_trading_knowledge(query, top_k=2)
                for result in results:
                    intelligence['risk_factors'].append({
                        'content': result.get('content', ''),
                        'score': result.get('score', 0)
                    })

            # 查询机会
            opportunity_queries = [
                "套利机会模式",
                "高收益策略",
                "最佳交易时段"
            ]

            for query in opportunity_queries:
                results = search_trading_knowledge(query, top_k=2)
                for result in results:
                    intelligence['opportunities'].append({
                        'content': result.get('content', ''),
                        'score': result.get('score', 0)
                    })

            return intelligence

        except Exception as e:
            logger.error(f"市场智能获取失败: {e}")
            return {
                'market_conditions': [],
                'risk_factors': [],
                'opportunities': [],
                'warnings': ['无法获取市场智能情报']
            }

    def reset_weights(self) -> None:
        """重置策略权重到基础值"""
        self._current_weights = self._base_weights.copy()
        logger.info("策略权重已重置到基础值")

    def export_performance_data(self) -> Dict[str, Any]:
        """导出性能数据用于持久化

        Returns:
            性能数据字典
        """
        return {
            'strategy_performance': dict(self._strategy_performance),
            'current_weights': self._current_weights,
            'base_weights': self._base_weights,
            'timestamp': time.time()
        }

    def import_performance_data(self, data: Dict[str, Any]) -> None:
        """导入性能数据

        Args:
            data: 性能数据字典
        """
        if 'strategy_performance' in data:
            self._strategy_performance = defaultdict(lambda: {
                'success_count': 0,
                'failure_count': 0,
                'total_profit': 0.0,
                'last_update': time.time()
            })
            self._strategy_performance.update(data['strategy_performance'])

        if 'current_weights' in data:
            self._current_weights = data['current_weights']
            self._normalize_weights()

        logger.info("性能数据已导入")