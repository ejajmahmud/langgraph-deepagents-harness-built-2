"""集成测试"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch

from agents.main_agent import CryptoArbitrageAgent
from storage.knowledge_base import KnowledgeBase
from storage.project_tracker import ProjectTracker
from tools.exchange_api import ExchangeManager
from tools.risk_management import RiskManager


@pytest.fixture
def test_config():
    """测试配置 fixture"""
    return {
        'model': 'anthropic:claude-sonnet-4-5-20250929',
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
def temp_knowledge_base(tmp_path):
    """临时知识库 fixture"""
    db_path = str(tmp_path / "test_knowledge.db")
    return KnowledgeBase(db_path)


class TestKnowledgeBase:
    """知识库测试"""

    def test_initialization(self, temp_knowledge_base):
        """测试知识库初始化"""
        assert temp_knowledge_base is not None

    def test_add_strategy(self, temp_knowledge_base):
        """测试添加策略"""
        strategy_id = temp_knowledge_base.add_strategy(
            name="Test Strategy",
            description="Test description",
            parameters={'param1': 'value1'},
            performance_metrics={'profit': 100.0}
        )

        assert strategy_id > 0

        # 验证策略可以获取
        strategy = temp_knowledge_base.get_strategy("Test Strategy")
        assert strategy is not None
        assert strategy['name'] == "Test Strategy"

    def test_add_trade_record(self, temp_knowledge_base):
        """测试添加交易记录"""
        trade_id = temp_knowledge_base.add_trade_record(
            strategy="cross_exchange",
            symbol="BTC/USDT",
            exchange="binance",
            entry_price=50000.0,
            exit_price=50200.0,
            quantity=0.1,
            profit=20.0,
            profit_rate=0.4,
            status="completed",
            execution_time=5.5,
            notes="Test trade"
        )

        assert trade_id > 0

        # 验证交易记录可以获取
        trades = temp_knowledge_base.get_recent_trades(limit=1)
        assert len(trades) == 1
        assert trades[0]['symbol'] == "BTC/USDT"

    def test_add_performance_metrics(self, temp_knowledge_base):
        """测试添加性能指标"""
        metrics_id = temp_knowledge_base.add_performance_metrics(
            strategy="cross_exchange",
            date="2026-04-14",
            total_trades=10,
            profitable_trades=7,
            total_profit=150.0,
            max_drawdown=2.5,
            sharpe_ratio=2.1,
            win_rate=0.7
        )

        assert metrics_id > 0

    def test_add_project_progress(self, temp_knowledge_base):
        """测试添加项目进度"""
        progress_id = temp_knowledge_base.add_project_progress(
            version="1.0.0",
            date="2026-04-14",
            completed_tasks=["task1", "task2"],
            in_progress_tasks=["task3"],
            planned_tasks=["task4", "task5"],
            notes="Test iteration"
        )

        assert progress_id > 0

    def test_get_statistics(self, temp_knowledge_base):
        """测试获取统计信息"""
        # 先添加一些测试数据
        temp_knowledge_base.add_trade_record(
            strategy="test",
            symbol="BTC/USDT",
            exchange="binance",
            entry_price=50000.0,
            exit_price=50100.0,
            quantity=0.1,
            profit=10.0,
            profit_rate=0.2,
            status="completed",
            execution_time=5.0
        )

        stats = temp_knowledge_base.get_statistics()
        assert stats['trades_count'] == 1
        assert stats['total_profit'] == 10.0


class TestProjectTracker:
    """项目追踪器测试"""

    @pytest.fixture
    def temp_project_tracker(self, tmp_path):
        """临时项目追踪器 fixture"""
        # 使用临时数据库
        db_path = str(tmp_path / "test_tracker.db")

        # 模拟知识库
        with patch('storage.project_tracker.get_knowledge_base') as mock_kb:
            mock_kb.return_value = KnowledgeBase(db_path)
            return ProjectTracker("TestProject")

    def test_initialization(self, temp_project_tracker):
        """测试项目追踪器初始化"""
        assert temp_project_tracker is not None
        assert temp_project_tracker.project_name == "TestProject"

    def test_record_iteration(self, temp_project_tracker):
        """测试记录迭代"""
        temp_project_tracker.record_iteration(
            version="1.0.0",
            completed_tasks=["task1"],
            in_progress_tasks=["task2"],
            planned_tasks=["task3"],
            summary="Test summary",
            achievements=["achievement1"],
            challenges=["challenge1"],
            next_steps=["step1"]
        )

        # 验证迭代记录
        iterations = temp_project_tracker.get_iteration_history(limit=1)
        assert len(iterations) == 1
        assert iterations[0]['version'] == "1.0.0"

    def test_generate_progress_report(self, temp_project_tracker):
        """测试生成进度报告"""
        report = temp_project_tracker.generate_progress_report()
        assert "TestProject" in report
        assert "进度报告" in report

    def test_analyze_progress(self, temp_project_tracker):
        """测试分析进度"""
        temp_project_tracker.record_iteration(
            version="1.0.0",
            completed_tasks=["task1", "task2"],
            in_progress_tasks=["task3"],
            planned_tasks=["task4"],
            summary="Test",
            achievements=["test"],
            challenges=["test"],
            next_steps=["test"]
        )

        analysis = temp_project_tracker.analyze_progress()
        assert analysis['total_iterations'] == 1
        assert analysis['latest_version'] == "1.0.0"
        assert analysis['is_progress_active'] is True


class TestRiskManager:
    """风险管理器测试"""

    @pytest.fixture
    def risk_manager(self):
        """风险管理器 fixture"""
        return RiskManager({
            'max_daily_loss': 500,
            'max_position_size': 1000,
            'max_total_exposure': 5000,
            'max_drawdown': 10.0
        })

    def test_initialization(self, risk_manager):
        """测试风险管理器初始化"""
        assert risk_manager.max_daily_loss == 500
        assert risk_manager.max_position_size == 1000
        assert risk_manager.max_total_exposure == 5000

    def test_check_position_risk_valid(self, risk_manager):
        """测试有效的仓位风险检查"""
        result = risk_manager.check_position_risk({
            'amount': 500,
            'symbol': 'BTC/USDT',
            'strategy': 'cross_exchange'
        })

        assert result is True

    def test_check_position_risk_too_large(self, risk_manager):
        """测试过大的仓位风险检查"""
        result = risk_manager.check_position_risk({
            'amount': 1500,  # 超过 max_position_size
            'symbol': 'BTC/USDT',
            'strategy': 'cross_exchange'
        })

        assert result is False

    def test_update_exposure(self, risk_manager):
        """测试更新敞口"""
        initial_exposure = risk_manager.current_exposure
        risk_manager.update_exposure(500, is_increase=True)
        assert risk_manager.current_exposure == initial_exposure + 500

        risk_manager.update_exposure(500, is_increase=False)
        assert risk_manager.current_exposure == initial_exposure

    def test_record_trade_result(self, risk_manager):
        """测试记录交易结果"""
        initial_pnl = risk_manager.daily_pnl
        risk_manager.record_trade_result({
            'profit': 10.0,
            'expected_profit': 10.0,
            'strategy': 'cross_exchange'
        })

        assert risk_manager.daily_pnl == initial_pnl + 10.0
        assert risk_manager.daily_trades == 1

    def test_get_risk_summary(self, risk_manager):
        """测试获取风险摘要"""
        summary = risk_manager.get_risk_summary()
        assert 'current_exposure' in summary
        assert 'daily_pnl' in summary
        assert 'max_drawdown' in summary
        assert 'is_risk_limit_reached' in summary


@pytest.mark.asyncio
class TestCryptoArbitrageAgent:
    """套利交易 Agent 测试"""

    @pytest.fixture
    def mock_agent(self, test_config):
        """模拟 Agent fixture"""
        # 模拟 DeepAgents 创建
        with patch('agents.main_agent.create_deep_agent') as mock_create:
            mock_agent = Mock()
            mock_create.return_value = mock_agent

            agent = CryptoArbitrageAgent(test_config)
            return agent

    async def test_agent_initialization(self, mock_agent):
        """测试 Agent 初始化"""
        assert mock_agent is not None
        assert len(mock_agent.strategies) > 0
        assert mock_agent.risk_manager is not None

    async def test_scan_opportunities_tool(self, mock_agent):
        """测试扫描套利机会工具"""
        # 由于没有实际的交易所连接，应该返回空列表
        result = await mock_agent.scan_arbitrage_opportunities_tool("cross_exchange")
        assert isinstance(result, str)
        assert "发现" in result or "当前没有发现" in result

    async def test_get_risk_status_tool(self, mock_agent):
        """测试获取风险状态工具"""
        result = mock_agent.get_risk_status_tool()
        assert isinstance(result, str)
        assert "风险状态" in result

    async def test_get_performance_stats_tool(self, mock_agent):
        """测试获取性能统计工具"""
        result = mock_agent.get_performance_stats_tool()
        assert isinstance(result, str)
        assert "性能统计" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
