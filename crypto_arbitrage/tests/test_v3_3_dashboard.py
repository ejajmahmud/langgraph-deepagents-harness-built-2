"""V3.3 仪表板集成测试

测试实时监控仪表板、Web API、实时推送和配置热更新功能。
"""

import pytest
import asyncio
import json
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from monitoring.dashboard import RealtimeDashboard, get_dashboard, initialize_dashboard
from monitoring.realtime_push import RealtimePushManager, DataStream, get_push_manager, initialize_push_manager
from config.hot_reload import ConfigHotReload, get_hot_reload, initialize_hot_reload


class TestRealtimeDashboard:
    """测试实时监控仪表板"""

    @pytest.fixture
    def dashboard(self):
        """创建仪表板实例"""
        return RealtimeDashboard(
            window_size=100,
            update_interval=1.0,
            history_limit=1000
        )

    def test_dashboard_initialization(self, dashboard):
        """测试仪表板初始化"""
        assert dashboard.window_size == 100
        assert dashboard.update_interval == 1.0
        assert dashboard.history_limit == 1000
        assert not dashboard.is_running
        assert dashboard.start_time is None

    def test_dashboard_start_stop(self, dashboard):
        """测试启动和停止"""
        dashboard.start()
        assert dashboard.is_running
        assert dashboard.start_time is not None

        time.sleep(0.1)  # 等待一点时间
        assert dashboard.uptime > 0

        dashboard.stop()
        assert not dashboard.is_running

    def test_record_metric(self, dashboard):
        """测试记录指标"""
        dashboard.record_metric('test_metric', 123.45)

        # 检查指标是否记录
        assert 'test_metric' in dashboard.metrics
        assert len(dashboard.metrics['test_metric']) == 1
        assert dashboard.metrics['test_metric'][0]['value'] == 123.45

        # 检查历史记录
        assert 'test_metric' in dashboard.history
        assert len(dashboard.history['test_metric']) == 1

    def test_update_risk_metrics(self, dashboard):
        """测试更新风险指标"""
        risk_metrics = {
            'exposure': 5000.0,
            'volatility': 0.02,
            'liquidity_score': 0.8,
            'drawdown': 0.01,
            'correlation_risk': 0.1,
            'concentration_risk': 0.1
        }

        dashboard.update_risk_metrics(risk_metrics)

        assert dashboard.risk_metrics['exposure'] == 5000.0
        assert dashboard.risk_metrics['volatility'] == 0.02
        assert dashboard.risk_metrics['risk_level'] == 'LOW'

    def test_evaluate_risk_level(self, dashboard):
        """测试风险等级评估"""
        # 低风险
        dashboard.risk_metrics['exposure'] = 3000.0
        dashboard.risk_metrics['volatility'] = 0.02
        dashboard.risk_metrics['liquidity_score'] = 0.8
        dashboard.risk_metrics['drawdown'] = 0.01
        dashboard._evaluate_risk_level()
        assert dashboard.risk_metrics['risk_level'] == 'LOW'

        # 高风险
        dashboard.risk_metrics['exposure'] = 9000.0
        dashboard.risk_metrics['volatility'] = 0.06
        dashboard.risk_metrics['liquidity_score'] = 0.4
        dashboard.risk_metrics['drawdown'] = 0.06
        dashboard._evaluate_risk_level()
        assert dashboard.risk_metrics['risk_level'] == 'CRITICAL'

    def test_record_trade(self, dashboard):
        """测试记录交易"""
        trade = {
            'strategy': 'cross_exchange',
            'symbol': 'BTC/USDT',
            'success': True,
            'profit': 100.50,
            'execution_time': 1.5,
            'risk_level': 'LOW'
        }

        dashboard.record_trade(trade)

        # 检查交易历史
        assert len(dashboard.trade_history) == 1
        assert dashboard.trade_history[0]['strategy'] == 'cross_exchange'
        assert dashboard.trade_history[0]['success'] == True

        # 检查交易统计
        assert dashboard.trade_stats['total_trades'] == 1
        assert dashboard.trade_stats['successful_trades'] == 1
        assert dashboard.trade_stats['total_profit'] == 100.50
        assert dashboard.trade_stats['win_rate'] == 100.0

    def test_add_alert(self, dashboard):
        """测试添加告警"""
        alert = {
            'severity': 'warning',
            'category': 'risk',
            'message': 'Risk threshold exceeded'
        }

        dashboard.add_alert(alert)

        # 检查告警列表
        assert len(dashboard.alerts) == 1
        assert dashboard.alerts[0]['severity'] == 'warning'

        # 检查系统状态
        assert dashboard.system_status['warning_count'] == 1

    def test_get_overview_data(self, dashboard):
        """测试获取总览数据"""
        dashboard.record_metric('test', 100.0)
        data = dashboard.get_overview_data()

        assert 'system_status' in data
        assert 'uptime' in data
        assert 'trade_stats' in data
        assert 'risk_metrics' in data
        assert 'performance_metrics' in data

    def test_get_risk_data(self, dashboard):
        """测试获取风险数据"""
        risk_metrics = {
            'exposure': 5000.0,
            'volatility': 0.02
        }
        dashboard.update_risk_metrics(risk_metrics)

        data = dashboard.get_risk_data()

        assert 'current_metrics' in data
        assert 'risk_history' in data
        assert 'alerts' in data
        assert data['current_metrics']['exposure'] == 5000.0

    def test_get_trade_data(self, dashboard):
        """测试获取交易数据"""
        trade = {
            'strategy': 'test',
            'success': True,
            'profit': 50.0
        }
        dashboard.record_trade(trade)

        data = dashboard.get_trade_data()

        assert 'trade_history' in data
        assert 'trade_stats' in data
        assert 'strategy_stats' in data
        assert len(data['trade_history']) == 1

    def test_export_data(self, dashboard):
        """测试数据导出"""
        dashboard.record_metric('test', 100.0)

        # JSON 导出
        json_data = dashboard.export_data('overview', 'json')
        assert isinstance(json_data, str)

        data = json.loads(json_data)
        assert 'system_status' in data

    def test_clear_history(self, dashboard):
        """测试清除历史"""
        dashboard.record_metric('test', 100.0)
        dashboard.record_trade({'strategy': 'test', 'success': True, 'profit': 50.0})

        assert len(dashboard.history) > 0
        assert len(dashboard.trade_history) > 0

        dashboard.clear_history()

        assert len(dashboard.history) == 0
        assert len(dashboard.trade_history) == 0
        assert dashboard.trade_stats['total_trades'] == 0

    def test_update_listeners(self, dashboard):
        """测试更新监听器"""
        listener_called = [False]

        def listener():
            listener_called[0] = True

        dashboard.register_update_listener(listener)
        dashboard._notify_update_listeners()

        assert listener_called[0] == True

        dashboard.unregister_update_listener(listener)
        listener_called[0] = False

        dashboard._notify_update_listeners()
        assert listener_called[0] == False


class TestRealtimePushManager:
    """测试实时推送管理器"""

    @pytest.fixture
    def push_manager(self):
        """创建推送管理器实例"""
        return RealtimePushManager(
            heartbeat_interval=10.0,
            max_message_size=1024 * 1024,
            compression_threshold=512
        )

    def test_push_manager_initialization(self, push_manager):
        """测试推送管理器初始化"""
        assert push_manager.heartbeat_interval == 10.0
        assert push_manager.max_message_size == 1024 * 1024
        assert push_manager.compression_threshold == 512
        assert len(push_manager.connections) == 0
        assert len(push_manager.streams) == 0

    def test_create_stream(self, push_manager):
        """测试创建数据流"""
        stream = push_manager.create_stream('test_stream', max_size=100)

        assert stream is not None
        assert stream.name == 'test_stream'
        assert 'test_stream' in push_manager.streams

    def test_get_stream(self, push_manager):
        """测试获取数据流"""
        push_manager.create_stream('test_stream')
        stream = push_manager.get_stream('test_stream')

        assert stream is not None
        assert stream.name == 'test_stream'

    def test_stream_publish(self, push_manager):
        """测试数据流发布"""
        stream = push_manager.create_stream('test_stream')

        data = {'test': 'data', 'value': 123}
        stream.publish(data)

        assert len(stream.data) == 1
        assert stream.data[0]['test'] == 'data'
        assert stream.data[0]['value'] == 123

    def test_stream_subscribe(self, push_manager):
        """测试数据流订阅"""
        stream = push_manager.create_stream('test_stream')

        stream.subscribe('client1')
        assert 'client1' in stream.subscribers

        stream.unsubscribe('client1')
        assert 'client1' not in stream.subscribers

    def test_get_stats(self, push_manager):
        """测试获取统计信息"""
        stream = push_manager.create_stream('test_stream')
        stream.subscribe('client1')

        stats = push_manager.get_stats()

        assert 'total_connections' in stats
        assert 'active_connections' in stats
        assert 'total_messages_sent' in stats
        assert 'stream_stats' in stats
        assert 'active_streams' in stats
        assert stats['active_streams'] == 1


class TestDataStream:
    """测试数据流"""

    def test_stream_initialization(self):
        """测试数据流初始化"""
        stream = DataStream('test_stream', max_size=100, retention_time=3600.0)

        assert stream.name == 'test_stream'
        assert stream.max_size == 100
        assert stream.retention_time == 3600.0
        assert len(stream.data) == 0
        assert len(stream.subscribers) == 0

    def test_stream_publish(self):
        """测试发布数据"""
        stream = DataStream('test_stream')

        data = {'key': 'value'}
        stream.publish(data)

        assert len(stream.data) == 1
        assert stream.data[0]['key'] == 'value'
        assert '_timestamp' in stream.data[0]
        assert '_stream' in stream.data[0]

    def test_stream_max_size(self):
        """测试数据流最大大小"""
        stream = DataStream('test_stream', max_size=3)

        for i in range(5):
            stream.publish({'index': i})

        assert len(stream.data) == 3
        assert stream.data[0]['index'] == 2
        assert stream.data[2]['index'] == 4

    def test_stream_get_recent_data(self):
        """测试获取最近数据"""
        stream = DataStream('test_stream')

        for i in range(10):
            stream.publish({'index': i})

        recent = stream.get_recent_data(5)

        assert len(recent) == 5
        assert recent[0]['index'] == 5
        assert recent[4]['index'] == 9


class TestConfigHotReload:
    """测试配置热更新"""

    @pytest.fixture
    def config_manager(self):
        """创建配置管理器模拟"""
        mock_config = {
            'strategies': {
                'cross_exchange': {'enabled': True, 'allocation': 0.3}
            },
            'risk_management': {
                'max_exposure': 10000,
                'max_drawdown': 0.05
            },
            'monitoring': {
                'update_interval': 2.0
            }
        }

        config_mgr = Mock()
        config_mgr.load_config.return_value = mock_config
        return config_mgr

    @pytest.fixture
    def hot_reload(self, config_manager):
        """创建配置热更新实例"""
        return ConfigHotReload(config_manager)

    def test_hot_reload_initialization(self, hot_reload):
        """测试热更新初始化"""
        assert hot_reload.config_manager is not None
        assert hot_reload.validator is not None
        assert len(hot_reload.config_history) == 0
        assert len(hot_reload.change_listeners) == 0

    def test_strategies_validation(self, hot_reload):
        """测试策略配置验证"""
        # 有效配置
        valid_config = {
            'cross_exchange': {'enabled': True, 'allocation': 0.3},
            'triangular': {'enabled': False, 'allocation': 0.2}
        }
        assert hot_reload.validator.validate('strategies', valid_config) == True

        # 无效配置
        invalid_config = {
            'cross_exchange': {'enabled': 'invalid', 'allocation': 'invalid'}
        }
        assert hot_reload.validator.validate('strategies', invalid_config) == False

    def test_risk_management_validation(self, hot_reload):
        """测试风险管理配置验证"""
        # 有效配置
        valid_config = {
            'max_exposure': 10000,
            'max_drawdown': 0.05
        }
        assert hot_reload.validator.validate('risk_management', valid_config) == True

        # 无效配置
        invalid_config = {
            'max_exposure': -100,
            'max_drawdown': 1.5
        }
        assert hot_reload.validator.validate('risk_management', invalid_config) == False

    def test_get_config_history(self, hot_reload):
        """测试获取配置历史"""
        assert len(hot_reload.get_config_history()) == 0

        # 模拟添加一些变更记录
        from config.hot_reload import ConfigChange
        change = ConfigChange(
            section='test',
            old_value={},
            new_value={'key': 'value'},
            changed_at=datetime.now().isoformat()
        )
        hot_reload.config_history.append(change)

        history = hot_reload.get_config_history()
        assert len(history) == 1
        assert history[0]['section'] == 'test'

    def test_get_current_config(self, hot_reload):
        """测试获取当前配置"""
        config = hot_reload.get_current_config()

        assert isinstance(config, dict)
        assert 'strategies' in config
        assert 'risk_management' in config
        assert 'monitoring' in config

    def test_change_listeners(self, hot_reload):
        """测试变更监听器"""
        listener_called = [False]

        def listener(changes):
            listener_called[0] = True

        hot_reload.register_change_listener(listener)
        assert listener in hot_reload.change_listeners

        hot_reload.unregister_change_listener(listener)
        assert listener not in hot_reload.change_listeners


class TestGlobalInstances:
    """测试全局实例"""

    def test_get_dashboard(self):
        """测试获取全局仪表板实例"""
        dashboard = get_dashboard()
        assert dashboard is None or isinstance(dashboard, RealtimeDashboard)

    def test_initialize_dashboard(self):
        """测试初始化全局仪表板"""
        dashboard = initialize_dashboard()
        assert isinstance(dashboard, RealtimeDashboard)

        # 再次调用应该返回同一个实例
        dashboard2 = initialize_dashboard()
        assert dashboard is dashboard2

    def test_get_push_manager(self):
        """测试获取全局推送管理器实例"""
        manager = get_push_manager()
        assert manager is None or isinstance(manager, RealtimePushManager)

    def test_initialize_push_manager(self):
        """测试初始化全局推送管理器"""
        manager = initialize_push_manager()
        assert isinstance(manager, RealtimePushManager)

        # 再次调用应该返回同一个实例
        manager2 = initialize_push_manager()
        assert manager is manager2


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_dashboard_and_push_manager_integration(self):
        """测试仪表板和推送管理器的集成"""
        dashboard = RealtimeDashboard(update_interval=0.5)
        push_manager = RealtimePushManager()

        # 创建数据流
        stream = push_manager.create_stream('overview')
        stream.subscribe('client1')

        # 记录指标
        dashboard.record_metric('test', 100.0)

        # 发布数据
        stream.publish(dashboard.get_overview_data())

        assert len(stream.data) == 1

        # 清理
        dashboard.stop()
        await push_manager.cleanup()

    def test_config_validation_and_dashboard_integration(self):
        """测试配置验证和仪表板的集成"""
        config_manager = Mock()
        config_manager.load_config.return_value = {
            'strategies': {'test': {'enabled': True, 'allocation': 0.5}},
            'risk_management': {'max_exposure': 5000, 'max_drawdown': 0.05}
        }

        hot_reload = ConfigHotReload(config_manager)
        dashboard = RealtimeDashboard()

        # 更新配置中的风险参数
        risk_config = {
            'exposure': 5000.0,
            'volatility': 0.02,
            'liquidity_score': 0.8,
            'drawdown': 0.01
        }
        dashboard.update_risk_metrics(risk_config)

        assert dashboard.risk_metrics['exposure'] == 5000.0
        assert dashboard.risk_metrics['risk_level'] == 'LOW'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
