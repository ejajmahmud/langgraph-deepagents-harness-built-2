"""增强策略管理器 V3.1 - 深度Memo0对接和智能优化

核心改进:
1. 集成智能策略增强器
2. 深度Memo0知识应用
3. 多层级决策机制
4. 自适应风险管理
"""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EnhancedStrategyManagerV31:
    """增强策略管理器 V3.1"""

    def __init__(
        self,
        strategies: Dict[str, Any],
        config: Dict[str, Any]
    ):
        """初始化增强策略管理器

        Args:
            strategies: 策略字典
            config: 配置字典
        """
        self.strategies = strategies
        self.config = config

        # 初始化智能策略增强器
        self.intelligent_enhancer = None
        if config.get('intelligent_enhancement', {}).get('enabled', True):
            try:
                from strategies.intelligent_strategy_enhancer import (
                    IntelligentStrategyEnhancer
                )
                enhancer_config = config.get('intelligent_enhancement', {})
                self.intelligent_enhancer = IntelligentStrategyEnhancer(enhancer_config)
                logger.info("✅ 智能策略增强器已启用")
            except Exception as e:
                logger.warning(f"智能策略增强器初始化失败: {e}")

        # 策略选择统计
        self._selection_stats: Dict[str, int] = {}

        # 执行历史
        self._execution_history: List[Dict] = []

        logger.info("增强策略管理器 V3.1 初始化完成")

    async def scan_all_strategies(
        self,
        enhanced: bool = True
    ) -> List[Dict[str, Any]]:
        """扫描所有策略的套利机会

        Args:
            enhanced: 是否使用智能增强

        Returns:
            机会列表
        """
        all_opportunities = []

        for strategy_name, strategy in self.strategies.items():
            if not hasattr(strategy, 'safe_scan'):
                continue

            try:
                opportunities = await strategy.safe_scan()
                logger.debug(
                    f"{strategy_name}: 扫描到 {len(opportunities)} 个机会"
                )
                all_opportunities.extend(opportunities)

            except Exception as e:
                logger.error(f"策略 {strategy_name} 扫描失败: {e}")

        if not all_opportunities:
            return []

        # 智能增强
        if enhanced and self.intelligent_enhancer:
            opportunities = await self.intelligent_enhancer.enhance_opportunities(
                all_opportunities
            )
            logger.debug(f"智能增强完成: {len(opportunities)} 个机会")

        return opportunities

    async def execute_best_opportunity(
        self,
        opportunities: List[Dict[str, Any]],
        enhanced: bool = True
    ) -> Optional[Dict[str, Any]]:
        """执行最佳套利机会

        Args:
            opportunities: 机会列表
            enhanced: 是否使用智能增强

        Returns:
            执行结果
        """
        if not opportunities:
            return None

        # 选择最佳机会
        best_opp = self._select_best_opportunity(opportunities, enhanced)
        if not best_opp:
            return None

        strategy_name = best_opp.get('strategy')
        if strategy_name not in self.strategies:
            logger.warning(f"策略 {strategy_name} 不存在")
            return None

        # 记录策略选择
        self._selection_stats[strategy_name] = (
            self._selection_stats.get(strategy_name, 0) + 1
        )

        # 执行交易
        strategy = self.strategies[strategy_name]
        if not hasattr(strategy, 'safe_execute'):
            logger.warning(f"策略 {strategy_name} 不支持执行")
            return None

        # 获取市场智能
        market_intel = None
        if enhanced and self.intelligent_enhancer:
            market_intel = await self.intelligent_enhancer.get_market_intelligence()
            logger.debug("市场智能已获取")

        # 执行交易
        result = await strategy.safe_execute(best_opp)

        # 记录执行历史
        execution_record = {
            'opportunity': best_opp,
            'result': result,
            'market_intel': market_intel,
            'timestamp': time.time()
        }
        self._execution_history.append(execution_record)

        # 记录策略结果用于学习
        if self.intelligent_enhancer:
            success = result.get('status') == 'completed'
            profit = result.get('profit', 0)
            self.intelligent_enhancer.record_strategy_result(
                strategy_name, success, profit
            )

        # 记录到Memo0
        self._record_execution_to_memory(best_opp, result, market_intel)

        return result

    def _select_best_opportunity(
        self,
        opportunities: List[Dict[str, Any]],
        enhanced: bool = True
    ) -> Optional[Dict[str, Any]]:
        """选择最佳机会

        Args:
            opportunities: 机会列表
            enhanced: 是否使用智能评分

        Returns:
            最佳机会
        """
        if not opportunities:
            return None

        # 如果已智能增强，直接取第一个（已排序）
        if enhanced:
            for opp in opportunities:
                if 'smart_score' in opp:
                    return opp

        # 否则按收益率选择
        return max(
            opportunities,
            key=lambda x: x.get('profit_rate', 0)
        )

    def _record_execution_to_memory(
        self,
        opportunity: Dict[str, Any],
        result: Dict[str, Any],
        market_intel: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录执行到Memo0

        Args:
            opportunity: 机会信息
            result: 执行结果
            market_intel: 市场智能
        """
        try:
            from storage.mem0_storage import add_trading_knowledge

            strategy = opportunity.get('strategy', 'unknown')
            symbol = opportunity.get('symbol', 'N/A')
            status = result.get('status', 'unknown')

            # 记录执行决策
            decision_content = (
                f"策略选择决策: 选择 {strategy} 策略执行 {symbol} 套利。"
                f"预期收益率 {opportunity.get('profit_rate', 0):.3f}%, "
                f"智能评分 {opportunity.get('smart_score', 0):.2f}"
            )
            add_trading_knowledge('decision', decision_content)

            # 记录执行结果
            if status == 'completed':
                profit = result.get('profit', 0)
                result_content = (
                    f"交易执行成功: {strategy} {symbol}, "
                    f"利润 ${profit:.2f}, "
                    f"执行时间 {result.get('execution_time', 0):.2f}s"
                )
                add_trading_knowledge('execution_success', result_content)
            elif status == 'failed':
                error = result.get('error', '未知错误')
                failure_content = (
                    f"交易执行失败: {strategy} {symbol}, "
                    f"错误: {error}"
                )
                add_trading_knowledge('execution_failure', failure_content)

            # 记录市场智能应用
            if market_intel and market_intel.get('market_conditions'):
                intel_content = f"市场智能应用: {len(market_intel['market_conditions'])} 条市场条件被考虑"
                add_trading_knowledge('market_intel', intel_content)

        except Exception as e:
            logger.debug(f"执行记录到Memo0失败: {e}")

    async def get_intelligent_recommendation(
        self,
        context: str = "trading"
    ) -> Dict[str, Any]:
        """获取智能推荐

        Args:
            context: 上下文类型

        Returns:
            推荐字典
        """
        if not self.intelligent_enhancer:
            return {
                'enabled': False,
                'message': '智能增强未启用'
            }

        # 获取策略表现报告
        performance = self.intelligent_enhancer.get_strategy_performance_report()

        # 获取自适应权重
        weights = self.intelligent_enhancer.get_adaptive_weights()

        # 获取市场智能
        market_intel = await self.intelligent_enhancer.get_market_intelligence(context)

        # 生成推荐
        recommendations = self._generate_recommendations(performance, market_intel)

        return {
            'enabled': True,
            'performance': performance,
            'adaptive_weights': weights,
            'market_intelligence': market_intel,
            'recommendations': recommendations
        }

    def _generate_recommendations(
        self,
        performance: Dict[str, Dict],
        market_intel: Dict[str, Any]
    ) -> List[str]:
        """生成策略推荐

        Args:
            performance: 策略表现
            market_intel: 市场智能

        Returns:
            推荐列表
        """
        recommendations = []

        # 基于表现的推荐
        for strategy, perf in performance.items():
            success_rate = perf.get('success_rate', 0)
            if success_rate > 0.7 and perf.get('total_trades', 0) > 5:
                recommendations.append(
                    f"策略 {strategy} 表现优异 (成功率 {success_rate:.1%})，建议增加权重"
                )
            elif success_rate < 0.3 and perf.get('total_trades', 0) > 5:
                recommendations.append(
                    f"策略 {strategy} 表现不佳 (成功率 {success_rate:.1%})，建议降低权重或暂停"
                )

        # 基于市场条件的推荐
        conditions = market_intel.get('market_conditions', [])
        if conditions:
            top_condition = max(conditions, key=lambda x: x.get('score', 0))
            recommendations.append(
                f"主要市场条件: {top_condition.get('content', '')[:80]}"
            )

        # 基于风险因素的推荐
        risk_factors = market_intel.get('risk_factors', [])
        if len(risk_factors) > 3:
            recommendations.append(
                f"检测到 {len(risk_factors)} 个风险因素，建议谨慎交易"
            )

        return recommendations[:5]  # 最多返回5条推荐

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """获取综合统计

        Returns:
            统计数据字典
        """
        # 基础策略统计
        total_trades = 0
        total_profit = 0.0
        strategy_stats = {}

        for name, strategy in self.strategies.items():
            if hasattr(strategy, 'get_performance_stats'):
                stats = strategy.get_performance_stats()
                total_trades += stats.get('total_trades', 0)
                total_profit += stats.get('total_profit', 0)
                strategy_stats[name] = stats

        # 智能增强统计
        intelligent_stats = {}
        if self.intelligent_enhancer:
            intelligent_stats = {
                'performance_report': (
                    self.intelligent_enhancer.get_strategy_performance_report()
                ),
                'adaptive_weights': (
                    self.intelligent_enhancer.get_adaptive_weights()
                ),
                'selection_stats': dict(self._selection_stats)
            }

        return {
            'total_strategies': len(self.strategies),
            'active_strategies': len([
                s for s in self.strategies.values()
                if hasattr(s, 'is_running') and s.is_running
            ]),
            'total_trades': total_trades,
            'total_profit': total_profit,
            'strategies': strategy_stats,
            'intelligent_enhancement': intelligent_stats,
            'execution_history_count': len(self._execution_history)
        }

    def reset_intelligent_weights(self) -> None:
        """重置智能权重"""
        if self.intelligent_enhancer:
            self.intelligent_enhancer.reset_weights()
            logger.info("智能策略权重已重置")

    def export_data(self) -> Dict[str, Any]:
        """导出管理器数据

        Returns:
            数据字典
        """
        data = {
            'selection_stats': dict(self._selection_stats),
            'execution_history': self._execution_history[-100:],  # 只保留最近100条
            'timestamp': time.time()
        }

        if self.intelligent_enhancer:
            data['intelligent_enhancer'] = (
                self.intelligent_enhancer.export_performance_data()
            )

        return data

    def import_data(self, data: Dict[str, Any]) -> None:
        """导入管理器数据

        Args:
            data: 数据字典
        """
        if 'selection_stats' in data:
            self._selection_stats = data['selection_stats']

        if 'execution_history' in data:
            self._execution_history.extend(data['execution_history'])
            # 保留最近100条
            self._execution_history = self._execution_history[-100:]

        if 'intelligent_enhancer' in data and self.intelligent_enhancer:
            self.intelligent_enhancer.import_performance_data(
                data['intelligent_enhancer']
            )

        logger.info("增强策略管理器数据已导入")