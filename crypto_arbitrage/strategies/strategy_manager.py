"""多策略组合管理器 V2.8

统一管理和协调多个套利策略的执行，包括：
- 策略注册和生命周期管理
- 资金分配和仓位限制
- 信号聚合和优先级排序
- 策略间风险隔离
- 综合性能监控
- 市场条件分析 (V2.0)
- 智能止损集成 (V2.1)
- 回测引擎集成 (V2.1)
- 智能决策引擎 (V2.2) - 基于Memo0的AI决策支持
- 市场模式识别 (V2.2) - 学习市场周期和异常检测
- 策略自适应优化 (V2.2) - A/B测试和参数自动调优
- Docker生产部署 (V2.3) - 容器化部署和监控告警
- 自动知识积累 (V2.8) - 完整知识循环激活
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StrategyManager:
    """多策略组合管理器"""

    def __init__(self, config: Dict[str, Any]):
        """初始化策略管理器

        Args:
            config: 管理器配置，包含:
                - max_total_capital: 总资金上限 ($)
                - max_strategy_allocation: 单策略最大分配比例 (%)
                - min_opportunity_score: 最低机会评分
                - signal_aggregation: 信号聚合方式 (best, weighted, consensus)
                - correlation_limit: 策略间相关性上限
                - enable_market_analysis: 是否启用市场条件分析 (V2.0)
                - enable_intelligent_stop_loss: 是否启用智能止损 (V2.1)
                - enable_intelligence: 是否启用智能决策引擎 (V2.2)
                - enable_monitoring: 是否启用监控告警 (V2.3)
        """
        self.config = config
        self.max_total_capital = config.get('max_total_capital', 10000)
        self.max_strategy_allocation = config.get('max_strategy_allocation', 0.4)  # 40%
        self.min_opportunity_score = config.get('min_opportunity_score', 60)
        self.signal_aggregation = config.get('signal_aggregation', 'weighted')
        self.enable_market_analysis = config.get('enable_market_analysis', True)  # V2.0: 默认启用
        self.enable_intelligent_stop_loss = config.get('enable_intelligent_stop_loss', True)  # V2.1: 默认启用
        self.enable_intelligence = config.get('enable_intelligence', True)  # V2.2: 默认启用
        self.enable_monitoring = config.get('enable_monitoring', True)  # V2.3: 默认启用

        # V2.0: 市场条件分析器
        self._market_analyzer = None
        if self.enable_market_analysis:
            try:
                from tools.risk_management import MarketConditionAnalyzer
                self._market_analyzer = MarketConditionAnalyzer()
                logger.info("市场条件分析器已启用")
            except Exception as e:
                logger.warning(f"市场条件分析器初始化失败: {e}")

        # V2.1: 智能止损系统
        self._intelligent_stop_loss = None
        if self.enable_intelligent_stop_loss:
            try:
                from tools.risk_management import IntelligentStopLoss
                # 获取风险管理配置
                risk_config = config.get('risk_management', {})
                self._intelligent_stop_loss = IntelligentStopLoss(risk_config)
                logger.info("智能止损系统已启用")
            except Exception as e:
                logger.warning(f"智能止损系统初始化失败: {e}")

        # V2.2: 智能决策引擎（延迟初始化，等待存储和积累器准备好）
        self._decision_engine = None

        # V2.2: 市场模式识别器
        self._pattern_recognizer = None
        if self.enable_intelligence:
            try:
                from storage.market_pattern_recognizer import MarketPatternRecognizer
                pattern_config = config.get('pattern_recognition', {})
                self._pattern_recognizer = MarketPatternRecognizer(pattern_config)
                logger.info("市场模式识别器已启用")
            except Exception as e:
                logger.warning(f"市场模式识别器初始化失败: {e}")

        # V2.2: 策略优化器
        self._strategy_optimizer = None
        if self.enable_intelligence:
            try:
                from storage.strategy_optimizer import StrategyOptimizer
                optimizer_config = config.get('strategy_optimization', {})
                self._strategy_optimizer = StrategyOptimizer(optimizer_config)
                logger.info("策略优化器已启用")
            except Exception as e:
                logger.warning(f"策略优化器初始化失败: {e}")

        # V2.8: 自动知识积累器
        self._knowledge_accumulator = None
        self._storage = None
        if self.enable_intelligence:
            try:
                from storage.mem0_storage import get_unified_storage
                from storage.auto_knowledge_accumulator import AutoKnowledgeAccumulator

                # 初始化统一存储
                self._storage = get_unified_storage()

                # 初始化自动知识积累器
                self._knowledge_accumulator = AutoKnowledgeAccumulator(self._storage)
                logger.info("✅ 自动知识积累器已启用 (V2.8)")

                # 现在可以初始化智能决策引擎了（需要 storage 和 auto_accumulator）
                from storage.intelligent_decision_engine import IntelligentDecisionEngine
                self._decision_engine = IntelligentDecisionEngine(
                    storage=self._storage,
                    auto_accumulator=self._knowledge_accumulator
                )
                logger.info("✅ 智能决策引擎已启用 (V2.2)")
            except Exception as e:
                logger.warning(f"⚠️  自动知识积累器初始化失败: {e}")
                logger.warning("系统将在无知识积累模式下运行")

        # 策略注册表
        self._strategies: Dict[str, Any] = {}
        self._strategy_allocations: Dict[str, float] = {}
        self._strategy_performance: Dict[str, Dict] = {}

        # 综合统计
        self._total_trades = 0
        self._total_profit = 0.0
        self._daily_profit = 0.0
        self._daily_trades = 0

        self._last_scan_time = 0

        logger.info("多策略组合管理器初始化完成")

    def register_strategy(self, name: str, strategy, allocation: float = 0.25) -> bool:
        """注册策略

        Args:
            name: 策略名称
            strategy: 策略实例（需实现 scan_opportunities, execute_arbitrage, get_performance_stats）
            allocation: 资金分配比例 (0-1)

        Returns:
            是否注册成功
        """
        if name in self._strategies:
            logger.warning(f"策略 {name} 已注册，更新配置")
            return False

        # V1.6.0 Fix: 验证策略接口（增加 execute_arbitrage 检查）
        required_methods = ['scan_opportunities', 'execute_arbitrage', 'get_performance_stats']
        for method in required_methods:
            if not hasattr(strategy, method):
                logger.error(f"策略 {name} 缺少必要方法: {method}")
                return False

        self._strategies[name] = strategy
        self._strategy_allocations[name] = min(allocation, self.max_strategy_allocation)
        self._strategy_performance[name] = {
            'total_trades': 0,
            'total_profit': 0.0,
            'win_rate': 0.0,
            'last_trade_time': 0,
            'consecutive_losses': 0,
        }

        logger.info(f"策略注册成功: {name} (分配: {allocation:.0%})")
        return True

    def unregister_strategy(self, name: str) -> bool:
        """注销策略

        Args:
            name: 策略名称

        Returns:
            是否注销成功
        """
        if name not in self._strategies:
            return False

        del self._strategies[name]
        self._strategy_allocations.pop(name, None)
        self._strategy_performance.pop(name, None)

        logger.info(f"策略已注销: {name}")
        return True

    def get_strategy(self, name: str):
        """获取策略实例

        Args:
            name: 策略名称

        Returns:
            策略实例或 None
        """
        return self._strategies.get(name)

    @property
    def registered_strategies(self) -> List[str]:
        """获取已注册策略列表"""
        return list(self._strategies.keys())

    async def scan_all_strategies(self, price_data: Optional[List[float]] = None) -> List[Dict[str, Any]]:
        """扫描所有策略的交易机会（V2.0 市场条件分析）

        Args:
            price_data: 可选的价格数据，用于市场条件分析

        Returns:
            聚合后的交易机会列表（已评分和排序）
        """
        # V2.0: 分析市场条件并调整策略
        market_recommendation = None
        if self._market_analyzer and price_data:
            try:
                self._market_analyzer.analyze_market_conditions(price_data)
                market_recommendation = self._market_analyzer.get_trading_recommendation()
                logger.info(f"市场条件: {market_recommendation.get('recommendation')}, 风险等级: {market_recommendation.get('risk_level')}")
            except Exception as e:
                logger.warning(f"市场条件分析失败: {e}")

        async def scan_one(name: str, strategy) -> tuple:
            """扫描单个策略"""
            try:
                scan_start = time.time()
                opportunities = await strategy.scan_opportunities()
                scan_time = time.time() - scan_start

                for opp in opportunities:
                    opp['_strategy_name'] = name
                    opp['_score'] = self._score_opportunity(opp, name)

                # 记录监控
                from tools.monitoring import get_monitoring
                monitoring = get_monitoring()
                if monitoring:
                    await monitoring.record_scan_metrics(len(opportunities), scan_time)

                return name, opportunities, None
            except Exception as e:
                logger.error(f"扫描策略 {name} 失败: {e}")
                return name, [], str(e)

        # V2.0: 并发扫描所有策略
        tasks = [scan_one(name, strategy) for name, strategy in self._strategies.items()]
        results = await asyncio.gather(*tasks)

        all_opportunities = []
        for name, opportunities, error in results:
            if error:
                self._record_strategy_error(name, error)
            all_opportunities.extend(opportunities)

        self._last_scan_time = time.time()

        # 过滤低评分机会
        filtered = [o for o in all_opportunities if o.get('_score', 0) >= self.min_opportunity_score]

        # V2.0: 根据市场条件调整评分
        if market_recommendation:
            position_multiplier = market_recommendation.get('max_position_multiplier', 1.0)
            for opp in filtered:
                # 根据市场条件调整仓位评分
                current_score = opp.get('_score', 0)
                opp['_score'] = current_score * position_multiplier

        # V2.8: 使用智能决策引擎调整评分（基于历史经验）
        if self._decision_engine and filtered:
            try:
                # 提取当前市场条件
                current_conditions = {
                    "volatility": 0,  # 可以从价格数据计算
                    "trend": "stable",
                    "liquidity": "normal",
                    "funding_rate": 0,
                    "spread": filtered[0].get('profit_rate', 0) if filtered else 0
                }

                # 获取可用策略列表
                available_strategies = [opp.get('_strategy_name') for opp in filtered]

                # 查询智能决策引擎
                recommendations = self._decision_engine.recommend_strategy(
                    current_market_conditions=current_conditions,
                    available_strategies=available_strategies,
                    top_k=3
                )

                # 根据智能推荐调整评分
                if recommendations.get('recommendations'):
                    for rec in recommendations['recommendations']:
                        strategy_name = rec['strategy']
                        confidence = rec.get('confidence', 0)
                        expected_win_rate = rec.get('expected_win_rate', 0.5)

                        # 找到该策略的所有机会并调整评分
                        for opp in filtered:
                            if opp.get('_strategy_name') == strategy_name:
                                # 基于历史胜率调整评分
                                adjustment_factor = 1.0 + (expected_win_rate - 0.5) * 0.5
                                opp['_score'] = opp.get('_score', 0) * adjustment_factor
                                opp['_ai_boost'] = confidence

                    logger.info(f"🤖 智能决策引擎已调整 {len(recommendations['recommendations'])} 个策略的评分")
            except Exception as e:
                logger.debug(f"智能决策引擎调用失败: {e}")

        # 排序
        filtered.sort(key=lambda x: x.get('_score', 0), reverse=True)

        logger.info(
            f"全策略扫描完成: {len(self._strategies)} 个策略, "
            f"{len(all_opportunities)} 个机会, "
            f"{len(filtered)} 个通过筛选"
        )

        return filtered

    def _record_strategy_error(self, name: str, error: str) -> None:
        """V2.0: 记录策略错误到 Memo0"""
        try:
            from storage.mem0_storage import add_trading_knowledge
            add_trading_knowledge('strategy_error', f"策略 {name} 扫描失败: {error}")
        except Exception:
            pass  # 静默失败

    def _score_opportunity(self, opportunity: Dict, strategy_name: str) -> float:
        """对交易机会进行评分 (0-100)

        Args:
            opportunity: 交易机会
            strategy_name: 策略名称

        Returns:
            评分
        """
        score = 50.0  # 基础分

        # 1. 收益率评分 (0-25分)
        profit_rate = abs(opportunity.get('profit_rate', 0))
        if profit_rate > 2.0:
            score += 25
        elif profit_rate > 1.0:
            score += 20
        elif profit_rate > 0.5:
            score += 15
        elif profit_rate > 0.3:
            score += 10
        elif profit_rate > 0.1:
            score += 5

        # 2. 策略历史表现评分 (0-15分)
        perf = self._strategy_performance.get(strategy_name, {})
        win_rate = perf.get('win_rate', 0.5)
        if win_rate > 0.8:
            score += 15
        elif win_rate > 0.6:
            score += 10
        elif win_rate > 0.4:
            score += 5

        # 3. 仓位大小合理性 (0-10分)
        position_cost = opportunity.get('buy_cost', opportunity.get('position_value', 0))
        allocation = self._strategy_allocations.get(strategy_name, 0.25)
        max_allowed = self.max_total_capital * allocation
        if position_cost <= max_allowed * 0.5:
            score += 10
        elif position_cost <= max_allowed:
            score += 5
        else:
            score -= 10  # 超出分配，扣分

        # 4. 策略连续亏损惩罚 (0-10分)
        consecutive = perf.get('consecutive_losses', 0)
        if consecutive == 0:
            score += 5
        elif consecutive >= 3:
            score -= 10
        elif consecutive >= 2:
            score -= 5

        return max(0, min(100, score))

    async def execute_best_opportunity(self, opportunities: List[Dict]) -> Optional[Dict]:
        """执行最佳交易机会

        Args:
            opportunities: 评分后的机会列表

        Returns:
            执行结果或 None
        """
        if not opportunities:
            return None

        best = opportunities[0]
        strategy_name = best.get('_strategy_name')

        strategy = self._strategies.get(strategy_name)
        if not strategy:
            logger.error(f"策略 {strategy_name} 未找到")
            return None

        # 检查资金分配
        position_cost = best.get('buy_cost', best.get('position_value', 0))
        if not self._check_allocation(strategy_name, position_cost):
            logger.warning(f"资金分配检查未通过: {strategy_name}")
            return None

        # 检查策略健康状态
        if not self._check_strategy_health(strategy_name):
            logger.warning(f"策略健康检查未通过: {strategy_name}")
            return None

        # V2.8: 记录交易决策
        if self._knowledge_accumulator:
            try:
                self._knowledge_accumulator.record_decision(
                    decision_type="trade_execution",
                    market_conditions={
                        "volatility": best.get('volatility', 0),
                        "trend": "stable",  # 可以从市场分析器获取
                        "liquidity": "high" if best.get('volume', 0) > 10000 else "normal",
                        "funding_rate": best.get('funding_rate', 0),
                        "spread": best.get('profit_rate', 0)
                    },
                    strategy=strategy_name,
                    reasoning=f"机会评分 {best.get('_score', 0):.0f}, 收益率 {best.get('profit_rate', 0):.2f}%",
                    parameters={
                        "position_size": best.get('position_size', best.get('amount', 0)),
                        "entry_price": best.get('entry_price', best.get('buy_price', 0)),
                        "expected_profit": best.get('expected_profit', 0)
                    }
                )
            except Exception as e:
                logger.debug(f"决策记录失败: {e}")

        # 执行
        logger.info(f"执行最佳机会: {strategy_name} 评分={best.get('_score', 0):.0f}")

        try:
            from tools.transaction_executor import get_transaction_executor
            from tools.monitoring import get_monitoring

            executor = get_transaction_executor()

            start_time = time.time()
            result = {'status': 'pending'}

            # V2.1: 计算智能止损和止盈价格
            if self._intelligent_stop_loss:
                try:
                    entry_price = best.get('entry_price', best.get('buy_price', 0))
                    position_size = best.get('position_size', best.get('amount', 0))
                    volatility = best.get('volatility')

                    if entry_price > 0 and position_size > 0:
                        # 计算止损
                        stop_loss_config = self._intelligent_stop_loss.calculate_stop_loss(
                            entry_price, position_size, volatility
                        )

                        # 计算止盈
                        take_profit_config = self._intelligent_stop_loss.calculate_take_profit(
                            entry_price,
                            stop_loss_config['stop_loss_rate'],
                            risk_reward_ratio=2.0
                        )

                        # 添加到机会信息中
                        best['_stop_loss'] = stop_loss_config
                        best['_take_profit'] = take_profit_config

                        logger.info(
                            f"智能止损: 止损价 ${stop_loss_config['stop_loss_price']:.2f} "
                            f"({stop_loss_config['stop_loss_rate']:.2f}%), "
                            f"止盈价 ${take_profit_config['take_profit_price']:.2f} "
                            f"({take_profit_config['take_profit_rate']:.2f}%)"
                        )
                except Exception as e:
                    logger.warning(f"智能止损计算失败: {e}")

            if executor and hasattr(strategy, 'execute_arbitrage'):
                # 使用交易执行引擎
                trade_record = await executor.execute_arbitrage(best, validate_risk=True)
                result = trade_record if trade_record else {'status': 'failed', 'error': '无返回结果'}
            elif hasattr(strategy, 'execute_arbitrage'):
                # 直接执行
                success = await strategy.execute_arbitrage(best)
                result = {
                    'status': 'completed' if success else 'failed',
                    'opportunity': best
                }

            execution_time = time.time() - start_time

            # V2.8: 记录交易结果学习
            if self._knowledge_accumulator:
                try:
                    self._knowledge_accumulator.record_trade_result(
                        strategy=strategy_name,
                        decision_id=best.get('_decision_id', f"trade_{int(time.time())}"),
                        result_status=result.get('status', 'unknown'),
                        expected_profit=best.get('expected_profit', 0),
                        actual_profit=result.get('actual_profit', 0),
                        execution_time=execution_time,
                        lessons_learned=self._generate_lessons(result, best)
                    )
                except Exception as e:
                    logger.debug(f"交易结果记录失败: {e}")

            # 记录结果
            self._update_performance(strategy_name, result)
            self._total_trades += 1
            self._daily_trades += 1

            if result.get('status') == 'completed':
                profit = result.get('actual_profit', best.get('expected_profit', 0))
                self._total_profit += profit
                self._daily_profit += profit

                # V2.8: 记录策略表现
                if self._knowledge_accumulator:
                    try:
                        perf = self._strategy_performance.get(strategy_name, {})
                        self._knowledge_accumulator.record_strategy_performance(
                            strategy=strategy_name,
                            market_state="bull" if profit > 0 else "bear",
                            win_rate=perf.get('win_rate', 0),
                            total_profit=perf.get('total_profit', 0),
                            total_trades=perf.get('total_trades', 0),
                            notes=f"最近交易收益: ${profit:.2f}"
                        )
                    except Exception as e:
                        logger.debug(f"策略表现记录失败: {e}")

            # 发送监控数据
            monitoring = get_monitoring()
            if monitoring:
                await monitoring.record_execution_metrics(
                    strategy_name,
                    result.get('status') == 'completed',
                    execution_time,
                    result.get('actual_profit', 0)
                )

            return result

        except Exception as e:
            logger.error(f"执行交易失败: {e}")
            self._update_performance(strategy_name, {'status': 'failed', 'error': str(e)})
            return None

    def _check_allocation(self, strategy_name: str, position_cost: float) -> bool:
        """检查资金分配是否合规

        Args:
            strategy_name: 策略名称
            position_cost: 仓位成本

        Returns:
            是否通过
        """
        allocation = self._strategy_allocations.get(strategy_name, 0.25)
        max_allowed = self.max_total_capital * allocation
        return position_cost <= max_allowed

    def _check_strategy_health(self, strategy_name: str) -> bool:
        """检查策略健康状态（V1.6.0: 支持 BaseStrategy.is_healthy）

        Args:
            strategy_name: 策略名称

        Returns:
            是否健康
        """
        strategy = self._strategies.get(strategy_name)
        if not strategy:
            return False

        # V1.6.0: 优先使用 BaseStrategy 内置健康检查
        if hasattr(strategy, 'is_healthy'):
            if not strategy.is_healthy:
                logger.warning(f"策略 {strategy_name} 不健康（is_healthy=False）")
                return False
            return True

        # 降级: 使用管理器自己的连续亏损检查
        perf = self._strategy_performance.get(strategy_name, {})
        consecutive = perf.get('consecutive_losses', 0)

        if consecutive >= 3:
            logger.warning(f"策略 {strategy_name} 连续亏损 {consecutive} 次，暂停执行")
            return False

        return True

    def _update_performance(self, strategy_name: str, result: Dict) -> None:
        """更新策略性能

        Args:
            strategy_name: 策略名称
            result: 执行结果
        """
        if strategy_name not in self._strategy_performance:
            return

        perf = self._strategy_performance[strategy_name]
        perf['total_trades'] += 1
        perf['last_trade_time'] = time.time()

        if result.get('status') == 'completed':
            profit = result.get('actual_profit', 0)
            perf['total_profit'] += profit
            perf['consecutive_losses'] = 0

            # 更新胜率
            completed = perf['total_trades']
            wins = perf.get('wins', 0) + (1 if profit > 0 else 0)
            perf['wins'] = wins
            perf['win_rate'] = wins / completed if completed > 0 else 0
        else:
            perf['consecutive_losses'] += 1

    def _generate_lessons(self, result: Dict, opportunity: Dict) -> List[str]:
        """V2.8: 生成交易经验教训

        Args:
            result: 交易结果
            opportunity: 交易机会

        Returns:
            经验教训列表
        """
        lessons = []

        status = result.get('status', 'unknown')

        if status == 'completed':
            actual_profit = result.get('actual_profit', 0)
            expected_profit = opportunity.get('expected_profit', 0)

            if actual_profit > 0:
                if actual_profit > expected_profit * 1.2:
                    lessons.append("收益超出预期20%以上，市场条件 favorable")
                elif actual_profit > expected_profit:
                    lessons.append("收益略超预期，策略执行良好")
                else:
                    lessons.append("收益低于预期，可能存在执行延迟")
            else:
                lessons.append("交易亏损，需要分析市场变化")

        elif status == 'failed':
            error = result.get('error', '未知错误')
            if 'liquidity' in error.lower():
                lessons.append("流动性不足导致失败，应提高流动性阈值")
            elif 'timeout' in error.lower():
                lessons.append("执行超时，网络或交易所响应慢")
            elif 'price' in error.lower():
                lessons.append("价格变动过快，需要更快的执行")
            else:
                lessons.append(f"失败原因: {error}")

        return lessons

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """获取综合性能统计

        Returns:
            综合统计字典
        """
        strategy_stats = {}
        for name, strategy in self._strategies.items():
            try:
                stats = strategy.get_performance_stats()
                perf = self._strategy_performance.get(name, {})
                strategy_stats[name] = {
                    **stats,
                    'allocation': self._strategy_allocations.get(name, 0),
                    'consecutive_losses': perf.get('consecutive_losses', 0),
                    # V1.6.0: 使用策略自身健康报告
                    'health': self._check_strategy_health(name),
                }
            except Exception as e:
                strategy_stats[name] = {'error': str(e)}

        return {
            'total_strategies': len(self._strategies),
            'active_strategies': len([
                name for name, stats in strategy_stats.items()
                if stats.get('health') is True
            ]),
            'total_trades': self._total_trades,
            'total_profit': self._total_profit,
            'daily_profit': self._daily_profit,
            'daily_trades': self._daily_trades,
            'strategies': strategy_stats
        }

    def reset_daily_stats(self) -> None:
        """重置日统计"""
        logger.info(f"重置日统计: 利润 ${self._daily_profit:.2f}, 交易 {self._daily_trades}")
        self._daily_profit = 0.0
        self._daily_trades = 0

    @property
    def strategies(self) -> Dict[str, Any]:
        """获取所有策略"""
        return self._strategies

    # -------------------- V2.1: 回测引擎集成 --------------------

    async def backtest_strategy(
        self,
        strategy_name: str,
        price_data: List[float],
        backtest_type: str = 'simple',
        **kwargs
    ) -> Dict[str, Any]:
        """对单个策略进行回测（V2.1）

        Args:
            strategy_name: 策略名称
            price_data: 价格历史数据
            backtest_type: 回测类型 (simple, statistical, cross_exchange)
            **kwargs: 其他回测参数

        Returns:
            回测结果字典
        """
        strategy = self._strategies.get(strategy_name)
        if not strategy:
            logger.error(f"策略 {strategy_name} 未注册")
            return {'error': '策略未注册'}

        try:
            from backtesting.engine import BacktestEngine, PriceBar
            import time

            engine = BacktestEngine(
                initial_capital=self.max_total_capital,
                commission_rate=0.001,
                slippage=0.0005
            )

            # 生成价格条数据
            start_timestamp = time.time() - len(price_data) * 3600
            price_bars = []
            for i, price in enumerate(price_data):
                price_bars.append(PriceBar(
                    timestamp=start_timestamp + i * 3600,
                    open=price * 0.999,
                    high=price * 1.001,
                    low=price * 0.999,
                    close=price,
                    volume=1000
                ))

            logger.info(f"开始回测策略 {strategy_name}, 数据点数: {len(price_bars)}")

            # 根据策略类型选择回测方法
            if backtest_type == 'statistical' and hasattr(strategy, 'lookback_period'):
                # 统计套利回测
                # 生成相关价格序列
                correlated_bars = engine.generate_correlated_pair(price_bars, correlation=0.8)
                result = engine.run_statistical_arbitrage_backtest(
                    price_bars,
                    correlated_bars,
                    lookback=kwargs.get('lookback', 100),
                    position_size=kwargs.get('position_size', 500)
                )
            else:
                # 简单套利回测（基于收益率阈值）
                result = engine.run_cross_exchange_backtest(
                    price_bars,
                    price_bars,  # 使用相同价格序列模拟跨交易所
                    min_spread=kwargs.get('min_spread', strategy.min_profit_rate / 100),
                    position_size=kwargs.get('position_size', 1000)
                )

            # 转换为字典
            from dataclasses import asdict
            result_dict = asdict(result)

            # 记录回测结果到 Memo0
            try:
                from storage.mem0_storage import add_trading_knowledge
                add_trading_knowledge(
                    'backtest_result',
                    f"策略 {strategy_name} 回测完成: "
                    f"总收益率 {result.total_return:.2f}%, "
                    f"夏普比率 {result.sharpe_ratio:.2f}, "
                    f"最大回撤 {result.max_drawdown:.2f}%, "
                    f"交易数 {result.total_trades}"
                )
            except Exception as e:
                logger.debug(f"回测结果记录失败: {e}")

            logger.info(
                f"策略 {strategy_name} 回测完成: "
                f"收益率 {result.total_return:.2f}%, "
                f"夏普 {result.sharpe_ratio:.2f}, "
                f"回撤 {result.max_drawdown:.2f}%"
            )

            return result_dict

        except Exception as e:
            logger.error(f"回测策略 {strategy_name} 失败: {e}")
            return {'error': str(e)}

    async def backtest_all_strategies(
        self,
        price_data: List[float],
        **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        """对所有策略进行回测（V2.1）

        Args:
            price_data: 价格历史数据
            **kwargs: 其他回测参数

        Returns:
            所有策略的回测结果字典
        """
        results = {}

        for strategy_name in self.registered_strategies:
            logger.info(f"回测策略: {strategy_name}")
            result = await self.backtest_strategy(
                strategy_name,
                price_data,
                **kwargs
            )
            results[strategy_name] = result

        # 生成汇总报告
        self._generate_backtest_summary(results)

        return results

    def _generate_backtest_summary(self, results: Dict[str, Dict[str, Any]]) -> str:
        """生成回测汇总报告（V2.1）

        Args:
            results: 所有策略的回测结果

        Returns:
            Markdown 格式的汇总报告
        """
        report = "# 策略回测汇总报告\n\n"

        for strategy_name, result in results.items():
            if 'error' in result:
                report += f"## {strategy_name}\n"
                report += f"**错误**: {result['error']}\n\n"
                continue

            report += f"## {strategy_name}\n"
            report += "| 指标 | 值 |\n"
            report += "|------|-----|\n"
            report += f"| 总收益率 | {result.get('total_return', 0):.2f}% |\n"
            report += f"| 年化收益率 | {result.get('annualized_return', 0):.2f}% |\n"
            report += f"| 最大回撤 | {result.get('max_drawdown', 0):.2f}% |\n"
            report += f"| 夏普比率 | {result.get('sharpe_ratio', 0):.2f} |\n"
            report += f"| 索提诺比率 | {result.get('sortino_ratio', 0):.2f} |\n"
            report += f"| 总交易数 | {result.get('total_trades', 0)} |\n"
            report += f"| 胜率 | {result.get('win_rate', 0):.1f}% |\n"
            report += f"| 盈亏比 | {result.get('profit_factor', 0):.2f} |\n"
            report += f"| 最大连续亏损 | {result.get('max_consecutive_losses', 0)} |\n\n"

        logger.info("回测汇总报告生成完成")
        return report

    def get_backtest_recommendations(self, results: Dict[str, Dict[str, Any]]) -> List[str]:
        """基于回测结果给出策略建议（V2.1）

        Args:
            results: 所有策略的回测结果

        Returns:
            策略建议列表
        """
        recommendations = []

        for strategy_name, result in results.items():
            if 'error' in result:
                continue

            sharpe = result.get('sharpe_ratio', 0)
            max_drawdown = result.get('max_drawdown', 100)
            win_rate = result.get('win_rate', 0)

            # 评估策略
            if sharpe > 2.0 and max_drawdown < 5 and win_rate > 60:
                recommendations.append(
                    f"✅ {strategy_name}: 优秀策略 (夏普={sharpe:.2f}, 回撤={max_drawdown:.1f}%, 胜率={win_rate:.1f}%)"
                )
            elif sharpe > 1.0 and max_drawdown < 10 and win_rate > 50:
                recommendations.append(
                    f"⚠️  {strategy_name}: 可用策略，建议优化 (夏普={sharpe:.2f}, 回撤={max_drawdown:.1f}%, 胜率={win_rate:.1f}%)"
                )
            else:
                recommendations.append(
                    f"❌ {strategy_name}: 不推荐实盘 (夏普={sharpe:.2f}, 回撤={max_drawdown:.1f}%, 胜率={win_rate:.1f}%)"
                )

        return recommendations

    # -------------------- V2.2: 智能决策功能 --------------------

    async def get_intelligent_recommendation(
        self,
        market_conditions: Dict[str, Any],
        price_data: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """获取智能决策建议（V2.2）

        Args:
            market_conditions: 当前市场条件
            price_data: 价格历史数据（可选）

        Returns:
            智能建议字典:
                - strategy_recommendation: 策略推荐
                - market_state: 市场状态
                - risk_assessment: 风险评估
                - optimization_suggestions: 优化建议
        """
        if not self._decision_engine:
            return {}

        try:
            available_strategies = list(self._strategies.keys())

            # 1. 策略推荐
            strategy_rec = await self._decision_engine.recommend_strategy(
                market_conditions, available_strategies
            )

            # 2. 市场状态识别
            market_state = {}
            if self._pattern_recognizer and price_data:
                # 基于价格数据识别市场状态
                market_data = self._extract_market_data(price_data, market_conditions)
                market_state = await self._pattern_recognizer.recognize_market_state(market_data)

            # 3. 综合建议
            return {
                "strategy_recommendation": strategy_rec,
                "market_state": market_state,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.warning(f"获取智能建议失败: {e}")
            return {}

    async def assess_opportunity_risk(
        self,
        strategy_name: str,
        opportunity: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """评估交易机会风险（V2.2）

        Args:
            strategy_name: 策略名称
            opportunity: 交易机会
            market_conditions: 市场条件

        Returns:
            风险评估结果
        """
        if not self._decision_engine:
            return {}

        try:
            return await self._decision_engine.assess_risk(
                strategy_name, opportunity, market_conditions
            )
        except Exception as e:
            logger.warning(f"风险评估失败: {e}")
            return {}

    async def detect_market_anomalies(
        self,
        current_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """检测市场异常（V2.2）

        Args:
            current_data: 当前市场数据

        Returns:
            异常列表
        """
        if not self._pattern_recognizer:
            return []

        try:
            return await self._pattern_recognizer.detect_market_anomalies(current_data)
        except Exception as e:
            logger.warning(f"异常检测失败: {e}")
            return []

    async def get_optimization_suggestions(
        self,
        strategy_name: str,
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取策略优化建议（V2.2）

        Args:
            strategy_name: 策略名称
            market_conditions: 市场条件

        Returns:
            优化建议
        """
        if not self._strategy_optimizer:
            return {}

        try:
            strategy = self._strategies.get(strategy_name)
            if not strategy:
                return {}

            current_params = {
                'min_profit_rate': strategy.min_profit_rate,
                'max_position_size': strategy.max_position_size
            }

            return await self._strategy_optimizer.get_optimization_suggestions(
                strategy_name, current_params
            )
        except Exception as e:
            logger.warning(f"获取优化建议失败: {e}")
            return {}

    async def auto_optimize_strategy(
        self,
        strategy_name: str,
        market_conditions: Dict[str, Any]
    ) -> bool:
        """自动优化策略参数（V2.2）

        Args:
            strategy_name: 策略名称
            market_conditions: 市场条件

        Returns:
            是否优化成功
        """
        if not self._strategy_optimizer:
            return False

        try:
            strategy = self._strategies.get(strategy_name)
            if not strategy:
                return False

            current_params = {
                'min_profit_rate': strategy.min_profit_rate,
                'max_position_size': strategy.max_position_size
            }

            optimized = await self._strategy_optimizer.auto_optimize_parameters(
                strategy_name, current_params, market_conditions
            )

            if optimized:
                # 应用优化参数
                strategy.min_profit_rate = optimized.get('min_profit_rate', strategy.min_profit_rate)
                strategy.max_position_size = optimized.get('max_position_size', strategy.max_position_size)

                logger.info(f"策略 {strategy_name} 参数已优化: {optimized}")
                return True

            return False
        except Exception as e:
            logger.warning(f"自动优化失败: {e}")
            return False

    def _extract_market_data(
        self,
        price_data: List[float],
        conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """从价格数据提取市场信息"""
        if not price_data:
            return {}

        return {
            'price': price_data[-1],
            'price_change_24h': conditions.get('volatility', 0),
            'volatility': conditions.get('volatility', 0),
            'volume': conditions.get('volume', 1000000),
            'volume_change': 0.0
        }
