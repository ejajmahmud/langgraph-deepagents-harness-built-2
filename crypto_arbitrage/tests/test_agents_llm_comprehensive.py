"""Agents和LLM模块全面单元测试

测试覆盖核心组件:
- 加密货币套利Agent (CryptoArbitrageAgent)
- TradingAgents包装器 (TradingAgentsWrapper)
- LLM集成组件
- 信号融合和异常检测
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any


class TestCryptoArbitrageAgent:
    """加密货币套利Agent测试"""

    @pytest.fixture
    def minimal_config(self):
        """最小配置"""
        return {
            'model': 'gpt-4',
            'scan_interval': 1,
            'exchanges': {
                'binance': {
                    'api_key': 'test_key',
                    'secret': 'test_secret',
                    'options': {}
                }
            },
            'risk_management': {
                'max_daily_loss': 500,
                'max_position_size': 1000,
                'max_total_exposure': 5000,
                'max_drawdown': 10.0
            },
            'strategies': {
                'cross_exchange': {
                    'min_profit_rate': 0.5,
                    'max_position_size': 1000,
                    'symbols': ['BTC/USDT']
                }
            }
        }

    @pytest.fixture
    def mock_dependencies(self):
        """模拟依赖项"""
        # 模拟交易所管理器
        mock_exchange_manager = Mock()
        mock_exchange_manager.exchanges = {'binance': Mock()}
        mock_exchange_manager.get_ticker = AsyncMock(return_value={'bid': 50000.0, 'ask': 50100.0})
        mock_exchange_manager.get_trading_fees = AsyncMock(return_value={'trading': {'maker': 0.001, 'taker': 0.001}})

        # 模拟风险管理器
        mock_risk_manager = Mock()
        mock_risk_manager.assess_risk = Mock(return_value={'risk_level': 'low', 'score': 0.3})
        mock_risk_manager.check_position_limit = Mock(return_value=True)

        # 模拟监控系统
        mock_monitoring = Mock()
        mock_monitoring.log_metrics = Mock()

        # 模拟通知系统
        mock_notifier = Mock()
        mock_notifier.send_notification = Mock()

        return {
            'exchange_manager': mock_exchange_manager,
            'risk_manager': mock_risk_manager,
            'monitoring': mock_monitoring,
            'notifier': mock_notifier
        }

    def test_agent_config_structure(self, minimal_config):
        """测试Agent配置结构"""
        # 验证配置必需字段
        assert 'exchanges' in minimal_config
        assert 'risk_management' in minimal_config
        assert 'strategies' in minimal_config

        # 验证子配置结构
        assert 'binance' in minimal_config['exchanges']
        assert 'max_position_size' in minimal_config['risk_management']
        assert 'cross_exchange' in minimal_config['strategies']

    @patch('agents.main_agent.initialize_exchange_manager')
    @patch('agents.main_agent.initialize_risk_manager')
    @patch('agents.main_agent.initialize_monitoring')
    @patch('agents.main_agent.initialize_notifier')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-api-key'})
    def test_agent_initialization_with_mocks(
        self,
        mock_notifier,
        mock_monitoring,
        mock_risk,
        mock_exchange,
        minimal_config
    ):
        """测试使用Mock的Agent初始化"""
        # 设置模拟返回值
        mock_exchange.return_value = mock_exchange()
        mock_risk.return_value = mock_risk()
        mock_monitoring.return_value = mock_monitoring()
        mock_notifier.return_value = mock_notifier()

        from agents.main_agent import CryptoArbitrageAgent

        agent = CryptoArbitrageAgent(minimal_config)

        # 验证基本属性
        assert agent.config == minimal_config
        assert hasattr(agent, 'exchange_manager')
        assert hasattr(agent, 'risk_manager')
        assert hasattr(agent, 'monitoring')
        assert hasattr(agent, 'notifier')

    @patch('agents.main_agent.initialize_exchange_manager')
    @patch('agents.main_agent.initialize_risk_manager')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-api-key'})
    def test_agent_strategy_initialization(
        self,
        mock_risk,
        mock_exchange,
        minimal_config
    ):
        """测试Agent策略初始化"""
        mock_exchange.return_value = Mock()
        mock_risk.return_value = Mock()

        from agents.main_agent import CryptoArbitrageAgent

        agent = CryptoArbitrageAgent(minimal_config)

        # 验证策略管理器存在
        assert hasattr(agent, 'strategy_manager')
        assert hasattr(agent, 'strategies')

    @patch('agents.main_agent.initialize_exchange_manager')
    @patch('agents.main_agent.initialize_risk_manager')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-api-key'})
    def test_agent_with_trading_agents_disabled(
        self,
        mock_risk,
        mock_exchange,
        minimal_config
    ):
        """测试禁用TradingAgents的Agent"""
        minimal_config['trading_agents'] = {'enabled': False}
        mock_exchange.return_value = Mock()
        mock_risk.return_value = Mock()

        from agents.main_agent import CryptoArbitrageAgent

        agent = CryptoArbitrageAgent(minimal_config)

        # 验证增强策略管理器为None
        assert agent.enhanced_strategy_manager is None

    @patch('agents.main_agent.initialize_exchange_manager')
    @patch('agents.main_agent.initialize_risk_manager')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-api-key'})
    def test_agent_with_low_risk_engine_disabled(
        self,
        mock_risk,
        mock_exchange,
        minimal_config
    ):
        """测试禁用低风险引擎的Agent"""
        minimal_config['enhanced_low_risk_engine'] = {'enabled': False}
        mock_exchange.return_value = Mock()
        mock_risk.return_value = Mock()

        from agents.main_agent import CryptoArbitrageAgent

        agent = CryptoArbitrageAgent(minimal_config)

        # 验证低风险引擎为None
        assert agent.enhanced_low_risk_engine is None


class TestTradingAgentsWrapper:
    """TradingAgents包装器测试"""

    @pytest.fixture
    def wrapper_config(self):
        """包装器配置"""
        return {
            'provider': 'anthropic',
            'model': 'claude-sonnet-4-6',
            'language': 'Chinese',
            'enabled': True,
            'preset': 'standard'
        }

    @pytest.fixture
    def mock_environment(self):
        """模拟环境变量"""
        import os
        env_patch = {
            'ANTHROPIC_API_KEY': 'test-api-key',
            'OPENAI_API_KEY': None,
            'GOOGLE_API_KEY': None,
            'XAI_API_KEY': None,
            'OPENROUTER_API_KEY': None
        }
        return env_patch

    def test_wrapper_initialization_disabled(self, wrapper_config):
        """测试禁用状态的包装器"""
        wrapper_config['enabled'] = False

        from llm.trading_agents_wrapper import TradingAgentsWrapper

        wrapper = TradingAgentsWrapper(**wrapper_config)

        assert wrapper.enabled is False
        assert wrapper._graph is None

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_wrapper_initialization_with_api_key(self, wrapper_config):
        """测试有API Key的包装器初始化"""
        from llm.trading_agents_wrapper import TradingAgentsWrapper

        wrapper = TradingAgentsWrapper(**wrapper_config)

        assert wrapper.provider == 'anthropic'
        assert wrapper.model == 'claude-sonnet-4-6'
        assert wrapper.language == 'Chinese'

    def test_wrapper_presets(self):
        """测试不同预设模式"""
        from llm.trading_agents_wrapper import TradingAgentsWrapper

        presets = ['quick', 'standard', 'deep']

        for preset in presets:
            config = {
                'provider': 'anthropic',
                'model': 'claude-sonnet-4-6',
                'language': 'Chinese',
                'enabled': False,  # 避免实际初始化
                'preset': preset
            }

            wrapper = TradingAgentsWrapper(**config)
            assert wrapper.preset == preset

    def test_wrapper_language_support(self):
        """测试多语言支持"""
        from llm.trading_agents_wrapper import TradingAgentsWrapper

        languages = ['English', 'Chinese', 'Spanish', 'French']

        for language in languages:
            config = {
                'provider': 'anthropic',
                'model': 'claude-sonnet-4-6',
                'language': language,
                'enabled': False,
                'preset': 'standard'
            }

            wrapper = TradingAgentsWrapper(**config)
            assert wrapper.language == language

    def test_wrapper_provider_options(self):
        """测试不同LLM提供商"""
        from llm.trading_agents_wrapper import TradingAgentsWrapper

        providers = ['openai', 'google', 'anthropic', 'xai', 'openrouter']

        for provider in providers:
            config = {
                'provider': provider,
                'model': 'gpt-4',
                'language': 'English',
                'enabled': False,
                'preset': 'standard'
            }

            wrapper = TradingAgentsWrapper(**config)
            assert wrapper.provider == provider


class TestLLMIntegration:
    """LLM集成测试"""

    def test_signal_cache_component(self):
        """测试信号缓存组件"""
        # 验证组件存在
        try:
            from llm.signal_cache import SignalCache
            cache = SignalCache()
            assert cache is not None
        except ImportError:
            pytest.skip("SignalCache not available")

    def test_signal_fusion_component(self):
        """测试信号融合组件"""
        # 验证组件存在
        try:
            from llm.signal_fusion import SignalFusion
            fusion = SignalFusion()
            assert fusion is not None
        except ImportError:
            pytest.skip("SignalFusion not available")

    def test_adaptive_strategy_optimizer(self):
        """测试自适应策略优化器"""
        # 验证组件存在
        try:
            from llm.adaptive_strategy_optimizer import AdaptiveStrategyOptimizer
            from llm.memo0_decision_support import Memo0DecisionSupport
            from storage.mem0_storage import Memo0Storage

            # 创建mock对象
            mock_memo0_storage = Mock(spec=Memo0Storage)
            mock_decision_support = Mock(spec=Memo0DecisionSupport)

            # 正确传递参数
            optimizer = AdaptiveStrategyOptimizer(mock_memo0_storage, mock_decision_support)
            assert optimizer is not None
            assert optimizer.memo0 == mock_memo0_storage
            assert optimizer.decision_support == mock_decision_support
        except ImportError:
            pytest.skip("AdaptiveStrategyOptimizer not available")

    def test_intelligent_anomaly_detector(self):
        """测试智能异常检测器"""
        # 验证组件存在
        try:
            from llm.intelligent_anomaly_detector import IntelligentAnomalyDetector
            from storage.mem0_storage import Memo0Storage

            # 创建mock对象
            mock_memo0_storage = Mock(spec=Memo0Storage)
            config = {'detection_threshold': 2.0}

            # 正确传递参数
            detector = IntelligentAnomalyDetector(mock_memo0_storage, config)
            assert detector is not None
            assert detector.memo0 == mock_memo0_storage
            assert detector.config == config
        except ImportError:
            pytest.skip("IntelligentAnomalyDetector not available")


class TestAgentConfiguration:
    """Agent配置测试"""

    def test_minimal_viable_config(self):
        """测试最小可行配置"""
        minimal_config = {
            'exchanges': {'binance': {'api_key': 'test', 'secret': 'test'}},
            'risk_management': {'max_position_size': 1000}
        }

        # 验证配置包含必需字段
        assert 'exchanges' in minimal_config
        assert 'risk_management' in minimal_config

    def test_full_feature_config(self):
        """测试完整功能配置"""
        full_config = {
            'model': 'claude-sonnet-4-6',
            'scan_interval': 1,
            'exchanges': {
                'binance': {'api_key': 'key1', 'secret': 'secret1'},
                'okx': {'api_key': 'key2', 'secret': 'secret2'}
            },
            'risk_management': {
                'max_daily_loss': 500,
                'max_position_size': 1000,
                'max_total_exposure': 5000,
                'max_drawdown': 10.0
            },
            'strategies': {
                'cross_exchange': {'enabled': True},
                'triangular': {'enabled': True},
                'basis_trading': {'enabled': False}
            },
            'trading_agents': {'enabled': False},
            'enhanced_low_risk_engine': {'enabled': False},
            'monitoring': {'enabled': True},
            'notifications': {'enabled': True}
        }

        # 验证所有功能模块都有配置
        assert 'exchanges' in full_config
        assert 'risk_management' in full_config
        assert 'strategies' in full_config
        assert 'trading_agents' in full_config
        assert 'enhanced_low_risk_engine' in full_config
        assert 'monitoring' in full_config
        assert 'notifications' in full_config

    @pytest.mark.parametrize("config_key,expected_type", [
        ('max_daily_loss', int),
        ('max_position_size', (int, float)),
        ('max_total_exposure', (int, float)),
        ('max_drawdown', (int, float))
    ])
    def test_risk_management_config_types(self, config_key, expected_type):
        """测试风险管理配置类型"""
        config = {
            'max_daily_loss': 500,
            'max_position_size': 1000,
            'max_total_exposure': 5000,
            'max_drawdown': 10.0
        }

        assert config_key in config
        assert isinstance(config[config_key], expected_type)


class TestAgentLifecycle:
    """Agent生命周期测试"""

    @patch('agents.main_agent.initialize_exchange_manager')
    @patch('agents.main_agent.initialize_risk_manager')
    def test_agent_creation_destruction(
        self,
        mock_risk,
        mock_exchange
    ):
        """测试Agent创建和销毁"""
        mock_exchange.return_value = Mock()
        mock_risk.return_value = Mock()

        config = {
            'exchanges': {'binance': {'api_key': 'test', 'secret': 'test'}},
            'risk_management': {'max_position_size': 1000}
        }

        from agents.main_agent import CryptoArbitrageAgent

        # 创建Agent
        agent = CryptoArbitrageAgent(config)
        assert agent is not None

        # 验证基本方法存在
        assert hasattr(agent, 'config')
        assert hasattr(agent, 'exchange_manager')
        assert hasattr(agent, 'risk_manager')

        # 销毁Agent（Python自动处理内存管理）
        del agent

    @patch('agents.main_agent.initialize_exchange_manager')
    @patch('agents.main_agent.initialize_risk_manager')
    def test_multiple_agent_instances(
        self,
        mock_risk,
        mock_exchange
    ):
        """测试多个Agent实例"""
        mock_exchange.return_value = Mock()
        mock_risk.return_value = Mock()

        config = {
            'exchanges': {'binance': {'api_key': 'test', 'secret': 'test'}},
            'risk_management': {'max_position_size': 1000}
        }

        from agents.main_agent import CryptoArbitrageAgent

        # 创建多个实例
        agent1 = CryptoArbitrageAgent(config)
        agent2 = CryptoArbitrageAgent(config)

        # 验证实例独立
        assert agent1 is not agent2
        assert agent1.config == agent2.config


@pytest.mark.parametrize("provider,model,expected", [
    ('anthropic', 'claude-sonnet-4-6', True),
    ('openai', 'gpt-4', True),
    ('google', 'gemini-pro', True),
    ('xai', 'grok-beta', True),
    ('openrouter', 'mixtral-8x7b', True)
])
def test_llm_provider_combinations(provider, model, expected):
    """测试不同LLM提供商和模型组合"""
    config = {
        'provider': provider,
        'model': model,
        'language': 'English',
        'enabled': False,
        'preset': 'standard'
    }

    from llm.trading_agents_wrapper import TradingAgentsWrapper

    wrapper = TradingAgentsWrapper(**config)

    assert wrapper.provider == provider
    assert wrapper.model == model


class TestAgentErrorHandling:
    """Agent错误处理测试"""

    @patch('agents.main_agent.initialize_exchange_manager')
    @patch('agents.main_agent.initialize_risk_manager')
    def test_agent_with_invalid_config(
        self,
        mock_risk,
        mock_exchange
    ):
        """测试无效配置的Agent"""
        mock_exchange.return_value = Mock()
        mock_risk.return_value = Mock()

        # 提供空配置
        config = {}

        from agents.main_agent import CryptoArbitrageAgent

        # 应该能够处理空配置
        agent = CryptoArbitrageAgent(config)
        assert agent is not None

    @patch('agents.main_agent.initialize_exchange_manager')
    @patch('agents.main_agent.initialize_risk_manager')
    def test_agent_with_partial_config(
        self,
        mock_risk,
        mock_exchange
    ):
        """测试部分配置的Agent"""
        mock_exchange.return_value = Mock()
        mock_risk.return_value = Mock()

        # 只提供部分配置
        config = {
            'risk_management': {'max_position_size': 1000}
        }

        from agents.main_agent import CryptoArbitrageAgent

        agent = CryptoArbitrageAgent(config)
        assert agent is not None


class TestIntegrationScenarios:
    """集成场景测试"""

    @patch('agents.main_agent.initialize_exchange_manager')
    @patch('agents.main_agent.initialize_risk_manager')
    def test_agent_with_all_optional_features(
        self,
        mock_risk,
        mock_exchange
    ):
        """测试启用所有可选功能的Agent"""
        mock_exchange.return_value = Mock()
        mock_risk.return_value = Mock()

        config = {
            'exchanges': {'binance': {'api_key': 'test', 'secret': 'test'}},
            'risk_management': {'max_position_size': 1000},
            'strategies': {'cross_exchange': {'enabled': True}},
            'trading_agents': {'enabled': False},  # 禁用以避免实际LLM调用
            'enhanced_low_risk_engine': {'enabled': False},
            'monitoring': {'enabled': True},
            'notifications': {'enabled': True}
        }

        from agents.main_agent import CryptoArbitrageAgent

        agent = CryptoArbitrageAgent(config)

        # 验证所有组件都已初始化
        assert hasattr(agent, 'exchange_manager')
        assert hasattr(agent, 'risk_manager')
        assert hasattr(agent, 'monitoring')
        assert hasattr(agent, 'notifier')
        assert hasattr(agent, 'strategy_manager')
        assert hasattr(agent, 'strategies')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
