"""V55.0 测试套件

测试 V55.0 统一套利系统的所有功能

创建时间：2026-05-08
"""

import asyncio
import logging
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, '..'))

import pytest

from trading.unified_arbitrage_system_v55 import (
    UnifiedArbitrageSystemV55,
    LiveExchangeConnector,
    BridgeFeeMonitor,
    AdvancedRiskManager,
    V55ExecutionMode,
    Exchange,
    ExchangeConfig,
    V55ArbitrageSignal,
    V55ArbitrageDecision,
    initialize_v55_system,
    get_v55_system
)
from strategies.cross_chain_arbitrage import Blockchain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========== V55.1 基础系统测试 ==========

@pytest.mark.asyncio
async def test_v55_1_system_initialization():
    """V55.1 系统初始化测试"""
    logger.info("测试 V55.1: 系统初始化")

    config = {
        'execution_mode': 'fusion',
        'exchange_config': {
            'binance': {'enabled': False}
        }
    }

    system = UnifiedArbitrageSystemV55(config)

    assert system is not None
    assert system.execution_mode == V55ExecutionMode.FUSION
    assert system.config == config

    logger.info("✅ V55.1 系统初始化测试通过")


# ========== V55.2 交易所连接器测试 ==========

@pytest.mark.asyncio
async def test_v55_2_exchange_connector():
    """V55.2 交易所连接器测试"""
    logger.info("测试 V55.2: 交易所连接器")

    config = {
        'binance': {
            'enabled': True,
            'api_key': 'test_key',
            'api_secret': 'test_secret',
            'testnet': True
        }
    }

    connector = LiveExchangeConnector(config)

    assert connector is not None
    assert len(connector.exchange_configs) > 0
    assert Exchange.BINANCE in connector.exchange_configs

    binance_config = connector.exchange_configs[Exchange.BINANCE]
    assert binance_config.enabled is True
    assert binance_config.testnet is True

    logger.info("✅ V55.2 交易所连接器测试通过")


# ========== V55.3 跨链桥费率监控测试 ==========

def test_v55_3_bridge_fee_monitor():
    """V55.3 跨链桥费率监控测试"""
    logger.info("测试 V55.3: 跨链桥费率监控")

    monitor = BridgeFeeMonitor()

    assert monitor is not None

    # 测试ETH->BNB费率
    fee = monitor.get_bridge_fee(Blockchain.ETHEREUM, Blockchain.BNB_CHAIN)
    assert fee > 0

    # 测试ETH->SOL费率
    fee_sol = monitor.get_bridge_fee(Blockchain.ETHEREUM, Blockchain.SOLANA)
    assert fee_sol > 0

    # 测试跨链时间
    bridge_time = monitor.get_bridge_time(Blockchain.ETHEREUM, Blockchain.BNB_CHAIN)
    assert bridge_time > 0

    logger.info("✅ V55.3 跨链桥费率监控测试通过")


# ========== V55.4 高级风险管理器测试 ==========

def test_v55_4_risk_manager():
    """V55.4 高级风险管理器测试"""
    logger.info("测试 V55.4: 高级风险管理器")

    config = {
        'max_position_pct': 0.1,
        'max_leverage': 3,
        'max_daily_loss_pct': 0.05,
        'max_risk_score': 0.7,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.05,
    }

    manager = AdvancedRiskManager(config)

    assert manager is not None
    assert manager.max_position_pct == 0.1
    assert manager.max_leverage == 3

    # 测试头寸计算
    position = manager.calculate_position_size(
        capital=10000,
        risk_pct=0.01,
        entry_price=50000,
        stop_loss=49000
    )
    assert position > 0

    # 测试止损计算
    stop_loss = manager.calculate_stop_loss(entry_price=50000, direction='long')
    assert stop_loss < 50000

    # 测试止盈计算
    take_profit = manager.calculate_take_profit(entry_price=50000, direction='long')
    assert take_profit > 50000

    logger.info("✅ V55.4 高级风险管理器测试通过")


# ========== V55.5 信号检查测试 ==========

def test_v55_5_signal_risk_check():
    """V55.5 信号风险检查测试"""
    logger.info("测试 V55.5: 信号风险检查")

    config = {
        'max_risk_score': 0.7,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.05,
    }

    manager = AdvancedRiskManager(config)

    # 创建测试信号
    signal = V55ArbitrageSignal(
        signal_id='test_001',
        opportunity_type='cross_chain',
        token='BTC',
        source='ethereum',
        target='bnb',
        spread_pct=1.5,
        expected_profit=2.0,
        confidence=0.8,
        risk_score=0.3,
        ml_prediction=0.7,
        bridge_fee_pct=0.1
    )

    # 风险检查
    result = manager.check_risk(signal)

    assert result is not None
    assert result['passed'] is True
    assert result['action'] == 'execute'

    # 测试高风险信号
    high_risk_signal = V55ArbitrageSignal(
        signal_id='test_002',
        opportunity_type='cross_chain',
        token='BTC',
        source='ethereum',
        target='bnb',
        spread_pct=0.5,
        expected_profit=0.3,
        confidence=0.3,
        risk_score=0.9,
        ml_prediction=0.2,
        bridge_fee_pct=0.5
    )

    result_high_risk = manager.check_risk(high_risk_signal)
    assert result_high_risk['passed'] is False
    assert result_high_risk['action'] == 'skip'

    logger.info("✅ V55.5 信号风险检查测试通过")


# ========== V55.6 机会扫描测试 ==========

@pytest.mark.asyncio
async def test_v55_6_opportunity_scan():
    """V55.6 机会扫描测试"""
    logger.info("测试 V55.6: 机会扫描")

    config = {
        'execution_mode': 'backtest',
        'cross_chain_config': {
            'min_spread_pct': 0.5,
            'supported_chains': ['ethereum', 'bnb', 'solana']
        }
    }

    system = UnifiedArbitrageSystemV55(config)

    # 扫描机会
    signals = await system.scan_opportunities()

    assert system is not None
    assert isinstance(signals, list)

    logger.info(f"✅ V55.6 机会扫描测试通过，发现 {len(signals)} 个信号")


# ========== V55.7 信号分析测试 ==========

@pytest.mark.asyncio
async def test_v55_7_signal_analysis():
    """V55.7 信号分析测试"""
    logger.info("测试 V55.7: 信号分析")

    system = UnifiedArbitrageSystemV55({'execution_mode': 'backtest'})

    # 创建测试信号
    signal = V55ArbitrageSignal(
        signal_id='test_analyze_001',
        opportunity_type='cross_chain',
        token='ETH',
        source='ethereum',
        target='bnb',
        spread_pct=2.0,
        expected_profit=3.0,
        confidence=0.85,
        risk_score=0.25,
        ml_prediction=0.8,
        bridge_fee_pct=0.1
    )

    # 分析信号
    analysis = await system.analyze_signal(signal)

    assert analysis is not None
    assert 'signal' in analysis
    assert 'ml_analysis' in analysis
    assert 'risk_result' in analysis
    assert 'execution_recommendation' in analysis

    logger.info("✅ V55.7 信号分析测试通过")


# ========== V55.8 交易执行测试 ==========

@pytest.mark.asyncio
async def test_v55_8_trade_execution():
    """V55.8 交易执行测试"""
    logger.info("测试 V55.8: 交易执行")

    system = UnifiedArbitrageSystemV55({'execution_mode': 'backtest'})

    # 创建测试信号
    signal = V55ArbitrageSignal(
        signal_id='test_exec_001',
        opportunity_type='cross_chain',
        token='BTC',
        source='ethereum',
        target='bnb',
        spread_pct=2.0,
        expected_profit=500,
        confidence=0.85,
        risk_score=0.25,
        ml_prediction=0.8,
        bridge_fee_pct=0.1
    )

    # 创建决策
    decision = V55ArbitrageDecision(
        decision_id='dec_001',
        signal=signal,
        position_size=0.1,
        entry_price=50000,
        exit_price=51000,
        stop_loss=49000,
        expected_profit=500,
        risk_adjusted_profit=400
    )

    # 执行交易
    result = await system.execute(decision)

    assert result is not None
    assert result.decision_id == 'dec_001'
    assert result.executed is True

    logger.info("✅ V55.8 交易执行测试通过")


# ========== V55.9 统计功能测试 ==========

def test_v55_9_statistics():
    """V55.9 统计功能测试"""
    logger.info("测试 V55.9: 统计功能")

    system = UnifiedArbitrageSystemV55({'execution_mode': 'backtest'})

    stats = system.get_statistics()

    assert stats is not None
    assert 'total_trades' in stats
    assert 'successful_trades' in stats
    assert 'failed_trades' in stats
    assert 'success_rate' in stats
    assert 'components_initialized' in stats

    components = stats['components_initialized']
    assert isinstance(components, dict)

    logger.info(f"✅ V55.9 统计功能测试通过，组件状态: {components}")


# ========== V55.10 完整集成测试 ==========

@pytest.mark.asyncio
async def test_v55_10_full_integration():
    """V55.10 完整集成测试"""
    logger.info("测试 V55.10: 完整集成")

    # 初始化完整系统
    config = {
        'execution_mode': 'fusion',
        'cross_chain_config': {
            'min_spread_pct': 0.3,
            'supported_chains': ['ethereum', 'bnb', 'solana', 'base']
        },
        'exchange_config': {
            'binance': {'enabled': True, 'testnet': True}
        },
        'bridge_config': {},
        'risk_config': {
            'max_risk_score': 0.7,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.05
        }
    }

    system = initialize_v55_system(config)

    assert system is not None

    # 扫描机会
    signals = await system.scan_opportunities()

    # 分析信号(如果有)
    if signals:
        analysis = await system.analyze_signal(signals[0])
        assert analysis is not None

    # 获取统计
    stats = system.get_statistics()
    assert stats is not None
    assert stats['total_trades'] >= 0

    logger.info("✅ V55.10 完整集成测试通过")


# ========== 运行测试 ==========

def run_v55_tests():
    """运行所有V55测试"""
    logger.info("=" * 50)
    logger.info("开始运行 V55.0 测试套件")
    logger.info("=" * 50)

    # 同步测试
    logger.info("\n--- 同步测试 ---")
    test_v55_3_bridge_fee_monitor()
    test_v55_4_risk_manager()
    test_v55_5_signal_risk_check()
    test_v55_9_statistics()

    # 异步测试
    logger.info("\n--- 异步测试 ---")
    asyncio.run(test_v55_1_system_initialization())
    asyncio.run(test_v55_2_exchange_connector())
    asyncio.run(test_v55_6_opportunity_scan())
    asyncio.run(test_v55_7_signal_analysis())
    asyncio.run(test_v55_8_trade_execution())
    asyncio.run(test_v55_10_full_integration())

    logger.info("=" * 50)
    logger.info("V55.0 测试套件全部通过! ✅")
    logger.info("=" * 50)


if __name__ == '__main__':
    run_v55_tests()