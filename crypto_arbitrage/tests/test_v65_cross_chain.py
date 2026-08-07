"""V65.0 集成测试

测试跨链交易执行器和桥接集成功能

创建时间：2026-05-08
"""

import pytest
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.cross_chain_execution import (
    BridgeProtocol,
    CrossChainOrderStatus,
    CrossChainOrder,
    BridgeQuote,
    BridgeIntegration,
    CrossChainTransactionBuilder,
    ChainWalletManager,
    ChainConfig,
    get_bridge_integration,
    initialize_bridge_integration,
    get_transaction_builder,
    initialize_transaction_builder,
    get_wallet_manager,
    initialize_wallet_manager,
)


class TestBridgeIntegration:
    """桥接集成测试"""

    @pytest.mark.asyncio
    async def test_bridge_integration_init(self):
        """测试桥接集成器初始化"""
        bridge = initialize_bridge_integration()
        assert bridge is not None
        assert bridge.total_quotes == 0
        print("BridgeIntegration: OK")

    @pytest.mark.asyncio
    async def test_get_quote(self):
        """测试获取报价"""
        bridge = initialize_bridge_integration()

        quote = await bridge.get_quote(
            from_chain="ethereum",
            to_chain="avalanche",
            from_token="USDC",
            to_token="USDC",
            from_amount=1000.0,
            preferred_protocol=BridgeProtocol.LAYERZERO
        )

        assert quote is not None
        assert quote.from_amount == 1000.0
        assert quote.to_amount < quote.from_amount
        assert quote.bridge_fee > 0
        print(f"Quote: {quote.to_dict()}")

    @pytest.mark.asyncio
    async def test_compare_quotes(self):
        """测试比较报价"""
        bridge = initialize_bridge_integration()

        quotes = await bridge.compare_quotes(
            from_chain="ethereum",
            to_chain="avalanche",
            from_token="USDC",
            to_token="USDC",
            from_amount=5000.0
        )

        assert len(quotes) >= 2
        # 验证按净收益排序
        for i in range(len(quotes) - 1):
            assert quotes[i].net_amount() >= quotes[i + 1].net_amount()

        print(f"Compared {len(quotes)} quotes")

    def test_calculate_fee(self):
        """测试费用计算"""
        bridge = BridgeIntegration()

        fees = bridge.calculate_fee(
            protocol=BridgeProtocol.LAYERZERO,
            from_amount=1000.0,
            from_chain="ethereum",
            to_chain="avalanche"
        )

        assert "total_fee" in fees
        assert "net_amount" in fees
        assert fees["net_amount"] < 1000.0
        print(f"Fees: {fees}")

    def test_supported_routes(self):
        """测试支持的路由"""
        bridge = BridgeIntegration()

        routes = bridge.get_supported_routes("ethereum", "avalanche")
        assert len(routes) > 0
        print(f"Routes: {routes}")


class TestCrossChainTransactionBuilder:
    """跨链交易构建器测试"""

    @pytest.mark.asyncio
    async def test_transaction_builder_init(self):
        """测试交易构建器初始化"""
        builder = initialize_transaction_builder()
        assert builder is not None
        print("CrossChainTransactionBuilder: OK")

    @pytest.mark.asyncio
    async def test_build_order(self):
        """测试构建订单"""
        builder = initialize_transaction_builder()

        order = await builder.build_order(
            from_chain="ethereum",
            to_chain="avalanche",
            from_token="USDC",
            to_token="USDC",
            from_amount=1000.0
        )

        assert order is not None
        assert order.status == CrossChainOrderStatus.PENDING
        assert order.from_amount == 1000.0
        print(f"Order created: {order.order_id}")

    @pytest.mark.asyncio
    async def test_full_order_flow(self):
        """测试完整订单流程"""
        # 初始化
        bridge = initialize_bridge_integration()
        builder = initialize_transaction_builder()

        # 1. 获取报价
        quote = await bridge.get_quote(
            from_chain="polygon",
            to_chain="arbitrum",
            from_token="USDT",
            to_token="USDT",
            from_amount=5000.0,
            preferred_protocol=BridgeProtocol.STGATE
        )

        # 2. 构建订单
        order = await builder.build_order(
            from_chain="polygon",
            to_chain="arbitrum",
            from_token="USDT",
            to_token="USDT",
            from_amount=5000.0,
            quote=quote
        )

        # 3. 请求报价
        order = await builder.request_quote(order, bridge)

        # 4. 签名提交
        order = await builder.sign_and_submit(order)

        # 5. 确认交易
        order = await builder.confirm_transaction(order)

        assert order.status == CrossChainOrderStatus.COMPLETED
        assert order.tx_hash != ""
        print(f"Order completed: {order.to_dict()}")


class TestChainWalletManager:
    """链钱包管理器测试"""

    @pytest.mark.asyncio
    async def test_wallet_manager_init(self):
        """测试钱包管理器初始化"""
        manager = initialize_wallet_manager()
        assert manager is not None
        print("ChainWalletManager: OK")

    @pytest.mark.asyncio
    async def test_add_wallet(self):
        """测试添加钱包"""
        manager = initialize_wallet_manager()

        wallet_id = manager.add_wallet(
            blockchain="ethereum",
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f2bD3A"
        )

        assert wallet_id == "ethereum_0x742d35Cc"
        print(f"Wallet added: {wallet_id}")

    @pytest.mark.asyncio
    async def test_balance_operations(self):
        """测试余额操作"""
        manager = initialize_wallet_manager()

        # 添加钱包
        wallet_id = manager.add_wallet(
            blockchain="avalanche",
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f2bD3A"
        )

        # 更新余额
        await manager.update_balance(wallet_id, "USDC", 10000.0)
        await manager.update_balance(wallet_id, "native", 1.5)

        # 查询余额
        usdc_balance = await manager.get_balance(wallet_id, "USDC")
        native_balance = await manager.get_balance(wallet_id, "native")

        assert usdc_balance == 10000.0
        assert native_balance == 1.5
        print(f"Balances: USDC={usdc_balance}, AVAX={native_balance}")


class TestV65Integration:
    """V65.0 集成测试"""

    @pytest.mark.asyncio
    async def test_v65_full_integration(self):
        """测试完整V65.0集成"""
        # 1. 初始化所有组件
        bridge = initialize_bridge_integration()
        builder = initialize_transaction_builder()
        wallet_manager = initialize_wallet_manager()

        # 2. 注册链配置
        chain_config = ChainConfig(
            blockchain="ethereum",
            chain_id=1,
            rpc_url="https://eth-mainnet.g.alchemy.com/v2/xxx",
            explorer_url="https://etherscan.io",
            gas_token="ETH",
            default_gas_limit=21000,
            avg_gas_price=30.0
        )
        bridge.register_chain(chain_config)

        # 3. 添加钱包
        wallet_id = wallet_manager.add_wallet(
            blockchain="ethereum",
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f2bD3A"
        )
        await wallet_manager.update_balance(wallet_id, "USDC", 50000.0)

        # 4. 获取报价并比较
        quotes = await bridge.compare_quotes(
            from_chain="ethereum",
            to_chain="avalanche",
            from_token="USDC",
            to_token="USDC",
            from_amount=10000.0
        )

        # 5. 构建订单
        order = await builder.build_order(
            from_chain="ethereum",
            to_chain="avalanche",
            from_token="USDC",
            to_token="USDC",
            from_amount=10000.0,
            quote=quotes[0]
        )

        # 6. 请求报价
        order = await builder.request_quote(order, bridge)

        # 7. 签名提交
        order = await builder.sign_and_submit(order)

        # 8. 确认
        order = await builder.confirm_transaction(order)

        # 验证
        assert order.status == CrossChainOrderStatus.COMPLETED

        # 统计数据
        stats = {
            "bridge": bridge.get_statistics(),
            "builder": builder.get_statistics(),
            "wallet": wallet_manager.get_statistics()
        }

        print(f"\n=== V65.0 Integration Test ===")
        print(f"Bridge: {stats['bridge']}")
        print(f"Builder: {stats['builder']}")
        print(f"Wallet: {stats['wallet']}")
        print(f"Order: {order.order_id}")
        print(f"Status: {order.status.value}")
        print("=== All Tests Passed ===")


if __name__ == "__main__":
    print("Running V65.0 Integration Tests...")
    pytest.main([__file__, "-v", "-s"])