"""V4.2 集成测试 - 增强版引擎集成"""

import asyncio
from agents.main_agent import CryptoArbitrageAgent


async def test_enhanced_engine_initialization():
    """测试增强版引擎初始化"""
    config = {
        'model': 'anthropic:claude-sonnet-4-5-20250929',
        'exchanges': {},
        'mem0': {},
        'monitoring': {'enabled': True, 'alert_methods': ['console']},
        'enhanced_low_risk_engine': {
            'enabled': True,
            'enable_risk_prediction': True,
            'enable_health_monitoring': True,
            'enable_intelligent_decision': True
        }
    }

    print("=== V4.2 集成测试 ===")

    # 测试 1: 增强版引擎初始化
    print("\n测试 1: 增强版引擎初始化")
    agent = CryptoArbitrageAgent(config)

    assert agent.enhanced_low_risk_engine is not None, "增强版引擎未初始化"
    print("   OK: 增强版引擎已初始化")

    # 测试 2: 工具列表包含新工具
    print("\n测试 2: 工具列表验证")
    tools = agent._get_agent_tools()
    tool_names = [tool.name for tool in tools]

    assert 'scan_with_enhanced_engine_tool' in tool_names, "增强版扫描工具未在列表中"
    print("   OK: 增强版扫描工具已在列表中")

    # 测试 3: 标准扫描工具仍然工作
    print("\nTest 3: Standard scan tool")
    result = await agent.scan_arbitrage_opportunities_tool.coroutine(agent, "all")
    assert result is not None, "标准扫描失败"
    print(f"   OK: 标准扫描成功: {len(result)} 字符")

    # 测试 4: 增强版扫描工具
    print("\nTest 4: Enhanced scan tool")
    result = await agent.scan_with_enhanced_engine_tool.coroutine(agent, "BTC/USDT")
    assert result is not None, "增强版扫描失败"
    print(f"   OK: 增强版扫描成功: {len(result)} 字符")

    # 测试 5: 向后兼容性（不启用增强版引擎）
    print("\nTest 5: Backward compatibility")
    config_no_enhanced = {
        'model': 'anthropic:claude-sonnet-4-5-20250929',
        'exchanges': {},
        'mem0': {},
        'monitoring': {'enabled': True, 'alert_methods': ['console']},
        'enhanced_low_risk_engine': {'enabled': False}
    }

    agent_no_enhanced = CryptoArbitrageAgent(config_no_enhanced)
    assert agent_no_enhanced.enhanced_low_risk_engine is None, "增强版引擎应该未初始化"

    # 标准扫描工具应该仍然工作
    result = await agent_no_enhanced.scan_arbitrage_opportunities_tool.coroutine(agent_no_enhanced, "all")
    assert result is not None, "标准扫描在无增强版引擎时失败"
    print("   OK: 向后兼容性验证通过")

    print("\nV4.2 Integration tests passed!")


if __name__ == "__main__":
    asyncio.run(test_enhanced_engine_initialization())
