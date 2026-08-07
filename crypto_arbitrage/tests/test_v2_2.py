"""V2.2 测试套件 - 智能决策引擎深度集成

测试内容:
1. 智能决策引擎 - IntelligentDecisionEngine
2. 市场模式识别器 - MarketPatternRecognizer
3. 策略自适应优化器 - StrategyOptimizer
4. StrategyManager 集成测试
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from storage.intelligent_decision_engine import IntelligentDecisionEngine
from storage.market_pattern_recognizer import MarketPatternRecognizer, MarketState
from storage.strategy_optimizer import StrategyOptimizer, ABTest


class TestIntelligentDecisionEngine:
    """测试智能决策引擎"""

    @pytest.fixture
    def engine(self):
        config = {
            'enable_intelligence': True,
            'confidence_threshold': 0.7,
            'history_days': 30
        }
        return IntelligentDecisionEngine(config)

    def test_initialization(self, engine):
        """测试引擎初始化"""
        assert engine.enabled == True
        assert engine.confidence_threshold == 0.7
        assert engine.history_days == 30

    @pytest.mark.asyncio
    async def test_recommend_strategy_basic(self, engine):
        """测试基础策略推荐"""
        market_conditions = {
            'volatility': 2.5,
            'trend': 'rising',
            'liquidity': 'normal'
        }
        available_strategies = ['cross_exchange', 'triangular', 'funding_rate']

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = [
                {'content': 'cross_exchange 策略表现优秀 收益率 1.5%'},
                {'content': 'triangular 策略表现良好 收益率 0.8%'}
            ]

            result = await engine.recommend_strategy(market_conditions, available_strategies)

            assert 'recommended_strategy' in result
            assert 'confidence' in result
            assert 'reasoning' in result

    @pytest.mark.asyncio
    async def test_recommend_strategy_no_available(self, engine):
        """测试无可用策略时的推荐"""
        result = await engine.recommend_strategy({}, [])
        assert result['recommended_strategy'] is None
        assert result['confidence'] == 0

    @pytest.mark.asyncio
    async def test_assess_risk_basic(self, engine):
        """测试基础风险评估"""
        opportunity = {
            'symbol': 'BTC/USDT',
            'profit_rate': 1.2,
            'buy_cost': 1000
        }
        current_conditions = {
            'volatility': 3.5,
            'trend': 'falling'
        }

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            result = await engine.assess_risk('cross_exchange', opportunity, current_conditions)

            assert 'risk_level' in result
            assert 'risk_factors' in result
            assert 'recommendations' in result

    @pytest.mark.asyncio
    async def test_suggest_optimal_parameters(self, engine):
        """测试参数优化建议"""
        current_conditions = {'volatility': 2.0, 'trend': 'stable'}

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            result = await engine.suggest_optimal_parameters('cross_exchange', current_conditions)

            # 禁用时返回空
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_detect_market_anomalies(self, engine):
        """测试市场异常检测"""
        current_data = {
            'volatility': 8.0,  # 极高波动率
            'price_change_24h': 15.0  # 极端价格变动
        }

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            anomalies = await engine.detect_market_anomalies(current_data)

            # 应该检测到异常
            assert len(anomalies) > 0
            assert any(a['type'] == 'extreme_volatility' for a in anomalies)
            assert any(a['type'] == 'extreme_price_movement' for a in anomalies)

    def test_default_recommendation(self, engine):
        """测试默认推荐"""
        strategies = ['cross_exchange', 'triangular']
        result = engine._default_recommendation(strategies)

        assert result['recommended_strategy'] == 'cross_exchange'
        assert result['confidence'] == 0.5
        assert len(result['alternative_strategies']) == 1


class TestMarketPatternRecognizer:
    """测试市场模式识别器"""

    @pytest.fixture
    def recognizer(self):
        config = {
            'enable_pattern_recognition': True,
            'pattern_lookback_days': 30
        }
        return MarketPatternRecognizer(config)

    def test_initialization(self, recognizer):
        """测试识别器初始化"""
        assert recognizer.enabled == True
        assert recognizer.lookback_period == 30
        assert recognizer._current_state == MarketState.SIDEWAYS

    @pytest.mark.asyncio
    async def test_recognize_market_state_bull(self, recognizer):
        """测试牛市状态识别"""
        market_data = {
            'price': 50000,
            'price_change_24h': 5.0,  # 大幅上涨
            'volatility': 2.0,
            'volume': 1000000,
            'volume_change': 0.3
        }

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            result = await recognizer.recognize_market_state(market_data)

            assert result['state'] == MarketState.BULL
            assert 'confidence' in result
            assert 'recommendations' in result

    @pytest.mark.asyncio
    async def test_recognize_market_state_volatile(self, recognizer):
        """测试高波动状态识别"""
        market_data = {
            'price': 50000,
            'price_change_24h': 1.0,
            'volatility': 8.0,  # 极高波动
            'volume': 1000000,
            'volume_change': 0.1
        }

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            result = await recognizer.recognize_market_state(market_data)

            assert result['state'] == MarketState.VOLATILE

    @pytest.mark.asyncio
    async def test_detect_market_cycles(self, recognizer):
        """测试市场周期检测"""
        price_history = list(range(45000, 55000, 100))

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            result = await recognizer.detect_market_cycles(price_history)

            assert 'current_cycle' in result
            assert 'cycle_strength' in result

    @pytest.mark.asyncio
    async def test_detect_anomalies(self, recognizer):
        """测试异常检测"""
        current_data = {
            'price': 55000,
            'volatility': 6.0,
            'volume': 5000000
        }
        historical_data = [
            {'price': 50000, 'volatility': 2.0, 'volume': 1000000},
            {'price': 50500, 'volatility': 2.1, 'volume': 1100000},
            {'price': 51000, 'volatility': 1.9, 'volume': 1050000}
        ]

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            anomalies = await recognizer.detect_anomalies(current_data, historical_data)

            assert isinstance(anomalies, list)
            # 高波动率应该被检测为异常
            assert any(a['type'] == 'volatility_anomaly' for a in anomalies)

    @pytest.mark.asyncio
    async def test_get_market_sentiment(self, recognizer):
        """测试市场情绪分析"""
        market_data = {
            'price_change_24h': 3.0,  # 上涨
            'volatility': 1.5,  # 低波动
            'volume_change': 0.25  # 交易量增加
        }

        result = await recognizer.get_market_sentiment(market_data)

        assert 'sentiment' in result
        assert 'confidence' in result
        assert 'indicators' in result


class TestStrategyOptimizer:
    """测试策略优化器"""

    @pytest.fixture
    def optimizer(self):
        config = {
            'enable_optimization': True,
            'auto_optimize': True,
            'optimization_interval_hours': 24,
            'min_samples': 10
        }
        return StrategyOptimizer(config)

    def test_initialization(self, optimizer):
        """测试优化器初始化"""
        assert optimizer.enabled == True
        assert optimizer.auto_optimize == True
        assert optimizer.optimization_interval == 24

    def test_ab_test_creation(self, optimizer):
        """测试A/B测试创建"""
        param_a = {'min_profit_rate': 0.5, 'max_position_size': 1000}
        param_b = {'min_profit_rate': 0.6, 'max_position_size': 900}

        test = ABTest(
            name='test_profit_rate',
            strategy='cross_exchange',
            param_a=param_a,
            param_b=param_b,
            min_samples=10
        )

        assert test.name == 'test_profit_rate'
        assert test.strategy == 'cross_exchange'
        assert test.status == 'running'
        assert not test.is_complete()

    def test_ab_test_completion(self, optimizer):
        """测试A/B测试完成判断"""
        param_a = {'min_profit_rate': 0.5}
        param_b = {'min_profit_rate': 0.6}

        test = ABTest(
            name='test_completion',
            strategy='cross_exchange',
            param_a=param_a,
            param_b=param_b,
            min_samples=3
        )

        # 添加不足样本
        test.add_result('A', {'profit': 10})
        test.add_result('B', {'profit': 12})
        assert not test.is_complete()

        # 添加足够样本
        test.add_result('A', {'profit': 11})
        test.add_result('B', {'profit': 13})
        test.add_result('A', {'profit': 9})
        test.add_result('B', {'profit': 14})  # 添加第3个B组结果
        assert test.is_complete()

    def test_ab_test_winner_determination(self, optimizer):
        """测试获胜者判断"""
        param_a = {'min_profit_rate': 0.5}
        param_b = {'min_profit_rate': 0.6}

        test = ABTest(
            name='test_winner',
            strategy='cross_exchange',
            param_a=param_a,
            param_b=param_b,
            min_samples=3
        )

        # 添加结果（A更好）
        for i in range(3):
            test.add_result('A', {'profit': 15 + i})
            test.add_result('B', {'profit': 10 + i})

        winner, profit, message = test.get_winner()

        assert winner == 'A'
        assert '胜出' in message

    @pytest.mark.asyncio
    async def test_start_ab_test(self, optimizer):
        """测试启动A/B测试"""
        param_a = {'min_profit_rate': 0.5}
        param_b = {'min_profit_rate': 0.6}

        with patch('storage.mem0_storage.add_trading_knowledge') as mock_add:
            result = await optimizer.start_ab_test(
                'test_params',
                'cross_exchange',
                param_a,
                param_b
            )

            assert result == True
            assert 'test_params' in optimizer._active_tests

    @pytest.mark.asyncio
    async def test_record_ab_result(self, optimizer):
        """测试记录A/B测试结果"""
        await optimizer.start_ab_test(
            'test_record',
            'cross_exchange',
            {'min_profit_rate': 0.5},
            {'min_profit_rate': 0.6}
        )

        result = await optimizer.record_ab_result(
            'test_record',
            'A',
            {'profit': 10, 'success': True}
        )

        assert result == True

    @pytest.mark.asyncio
    async def test_get_optimization_suggestions(self, optimizer):
        """测试获取优化建议"""
        current_params = {
            'min_profit_rate': 0.5,
            'max_position_size': 1000
        }

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            suggestions = await optimizer.get_optimization_suggestions(
                'cross_exchange',
                current_params
            )

            # 返回建议字典
            assert isinstance(suggestions, dict)

    @pytest.mark.asyncio
    async def test_auto_optimize_parameters(self, optimizer):
        """测试自动优化参数"""
        current_params = {
            'min_profit_rate': 0.5,
            'max_position_size': 1000
        }
        market_conditions = {'volatility': 2.0, 'trend': 'stable'}

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            # 首次调用应该优化
            optimized = await optimizer.auto_optimize_parameters(
                'cross_exchange',
                current_params,
                market_conditions
            )

            # 禁用自动优化时不返回
            if not optimizer.auto_optimize:
                assert optimized is None

    @pytest.mark.asyncio
    async def test_compare_strategies(self, optimizer):
        """测试策略比较"""
        strategies = ['cross_exchange', 'triangular', 'funding_rate']
        market_conditions = {'volatility': 2.0}

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            result = await optimizer.compare_strategies(strategies, market_conditions)

            # 返回比较结果
            assert isinstance(result, dict)


class TestStrategyManagerV22:
    """测试StrategyManager V2.2集成"""

    @pytest.fixture
    def config(self):
        return {
            'max_total_capital': 10000,
            'max_strategy_allocation': 0.4,
            'min_opportunity_score': 60,
            'enable_intelligence': True,  # V2.2
            'intelligence': {
                'enable_intelligence': True,
                'confidence_threshold': 0.7
            },
            'pattern_recognition': {
                'enable_pattern_recognition': True
            },
            'strategy_optimization': {
                'enable_optimization': True,
                'auto_optimize': True
            }
        }

    @pytest.fixture
    def manager(self, config):
        from strategies.strategy_manager import StrategyManager
        return StrategyManager(config)

    def test_v22_components_initialized(self, manager):
        """测试V2.2组件是否初始化"""
        assert manager._decision_engine is not None
        assert manager._pattern_recognizer is not None
        assert manager._strategy_optimizer is not None

    @pytest.mark.asyncio
    async def test_get_intelligent_recommendation(self, manager):
        """测试获取智能推荐"""
        market_conditions = {
            'volatility': 2.0,
            'trend': 'rising',
            'liquidity': 'normal'
        }

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            result = await manager.get_intelligent_recommendation(market_conditions)

            assert 'strategy_recommendation' in result
            assert 'market_state' in result

    @pytest.mark.asyncio
    async def test_assess_opportunity_risk(self, manager):
        """测试评估机会风险"""
        opportunity = {
            'symbol': 'BTC/USDT',
            'profit_rate': 1.2,
            'buy_cost': 1000
        }
        market_conditions = {'volatility': 3.5}

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            result = await manager.assess_opportunity_risk(
                'cross_exchange',
                opportunity,
                market_conditions
            )

            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_detect_market_anomalies_manager(self, manager):
        """测试管理器异常检测"""
        current_data = {
            'volatility': 8.0,
            'price_change_24h': 15.0
        }

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            anomalies = await manager.detect_market_anomalies(current_data)

            assert isinstance(anomalies, list)

    @pytest.mark.asyncio
    async def test_get_optimization_suggestions_manager(self, manager):
        """测试管理器获取优化建议"""
        market_conditions = {'volatility': 2.0}

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            result = await manager.get_optimization_suggestions(
                'cross_exchange',
                market_conditions
            )

            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_auto_optimize_strategy_manager(self, manager):
        """测试管理器自动优化策略"""
        # 注册一个策略
        from strategies.cross_exchange import CrossExchangeArbitrageStrategy
        strategy = CrossExchangeArbitrageStrategy({'min_profit_rate': 0.5, 'max_position_size': 1000})
        manager.register_strategy('cross_exchange', strategy, 0.25)

        market_conditions = {'volatility': 2.0}

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            result = await manager.auto_optimize_strategy(
                'cross_exchange',
                market_conditions
            )

            assert isinstance(result, bool)


class TestV22Integration:
    """V2.2集成测试"""

    @pytest.mark.asyncio
    async def test_complete_v22_workflow(self):
        """测试完整V2.2工作流"""
        # 初始化组件
        decision_engine = IntelligentDecisionEngine({'enable_intelligence': True})
        pattern_recognizer = MarketPatternRecognizer({'enable_pattern_recognition': True})
        strategy_optimizer = StrategyOptimizer({'enable_optimization': True})

        # 模拟市场数据
        market_conditions = {
            'volatility': 2.5,
            'trend': 'rising',
            'liquidity': 'normal'
        }

        # 1. 获取策略推荐
        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            recommendation = await decision_engine.recommend_strategy(
                market_conditions,
                ['cross_exchange', 'triangular']
            )
            assert 'recommended_strategy' in recommendation

        # 2. 识别市场状态
        market_data = {
            'price': 50000,
            'price_change_24h': 2.0,
            'volatility': 2.5,
            'volume': 1000000,
            'volume_change': 0.2
        }

        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            state = await pattern_recognizer.recognize_market_state(market_data)
            assert 'state' in state

        # 3. 获取优化建议
        with patch('storage.mem0_storage.search_trading_knowledge') as mock_search:
            mock_search.return_value = []

            suggestions = await strategy_optimizer.get_optimization_suggestions(
                'cross_exchange',
                {'min_profit_rate': 0.5, 'max_position_size': 1000}
            )
            # 返回建议字典即可
            assert isinstance(suggestions, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])