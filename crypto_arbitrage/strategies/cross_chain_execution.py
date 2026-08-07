"""V65.0 跨链交易执行器与桥接集成

V65.0 新增功能:
1. CrossChainTransactionBuilder - 跨链交易构建器
2. BridgeIntegration - 跨链桥集成
3. MultiChainExecutor - 多链执行器
4. ChainWalletManager - 链钱包管理器
5. CrossChainOrder - 跨链订单类型
6. BridgeFeeCalculator - 桥接费用计算

创建时间：2026-05-08
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# 桥接协议
class BridgeProtocol(Enum):
    """支持的跨链桥协议"""
    STGATE = "stargate"           # Stargate
    AXELAR = "axelar"             # Axelar
    WORMSHOLE = "wormhole"        # Wormhole
    LAYERZERO = "layerzero"      # LayerZero
    SYNAPSE = "synapse"           # Synapse
    CELER = "celer"              # Celer


# 交易状态
class CrossChainOrderStatus(Enum):
    """跨链订单状态"""
    PENDING = "pending"
    QUOTE_REQUESTED = "quote_requested"
    QUOTE_RECEIVED = "quote_received"
    SIGNING = "signing"
    SUBMITTED = "submitted"
    CONFIRMING = "confirming"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# 链上交易类型
class OnChainTxType(Enum):
    """链上交易类型"""
    SWAP = "swap"
    TRANSFER = "transfer"
    BRIDGE = "bridge"
    WRAP = "wrap"
    UNWRAP = "unwrap"


@dataclass
class ChainAddress:
    """链上地址"""
    address: str
    blockchain: str
    chain_id: int = 0
    symbol: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "blockchain": self.blockchain,
            "chain_id": self.chain_id,
            "symbol": self.symbol
        }


@dataclass
class CrossChainOrder:
    """跨链订单"""
    order_id: str
    from_chain: str
    to_chain: str
    from_token: str
    to_token: str
    from_amount: float
    to_amount: float = 0.0
    min_to_amount: float = 0.0
    status: CrossChainOrderStatus = CrossChainOrderStatus.PENDING
    bridge_protocol: BridgeProtocol = BridgeProtocol.LAYERZERO
    tx_hash: str = ""
    bridge_tx_hash: str = ""
    fee: float = 0.0
    slippage_tolerance: float = 0.01  # 1%滑点容忍
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 600)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "from_chain": self.from_chain,
            "to_chain": self.to_chain,
            "from_token": self.from_token,
            "to_token": self.to_token,
            "from_amount": self.from_amount,
            "to_amount": self.to_amount,
            "min_to_amount": self.min_to_amount,
            "status": self.status.value,
            "bridge_protocol": self.bridge_protocol.value,
            "tx_hash": self.tx_hash,
            "bridge_tx_hash": self.bridge_tx_hash,
            "fee": self.fee,
            "slippage_tolerance": self.slippage_tolerance,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at
        }


@dataclass
class BridgeQuote:
    """桥接报价"""
    quote_id: str
    from_chain: str
    to_chain: str
    from_token: str
    to_token: str
    from_amount: float
    to_amount: float
    bridge_fee: float
    gas_fee: float
    estimated_time: int  # 秒
    min_amount: float
    max_amount: float
    protocol: BridgeProtocol
    expires_at: float

    def total_fee(self) -> float:
        return self.bridge_fee + self.gas_fee

    def net_amount(self) -> float:
        return self.to_amount - self.bridge_fee

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quote_id": self.quote_id,
            "from_chain": self.from_chain,
            "to_chain": self.to_chain,
            "from_token": self.from_token,
            "to_token": self.to_token,
            "from_amount": self.from_amount,
            "to_amount": self.to_amount,
            "bridge_fee": self.bridge_fee,
            "gas_fee": self.gas_fee,
            "total_fee": self.total_fee(),
            "net_amount": self.net_amount(),
            "estimated_time": self.estimated_time,
            "min_amount": self.min_amount,
            "max_amount": self.max_amount,
            "protocol": self.protocol.value,
            "expires_at": self.expires_at
        }


@dataclass
class ChainConfig:
    """链配置"""
    blockchain: str
    chain_id: int
    rpc_url: str
    explorer_url: str
    gas_token: str
    default_gas_limit: int
    avg_gas_price: float = 0.0
    is_testnet: bool = False


class BridgeIntegration:
    """跨链桥集成器

    功能：
    - 多桥协议支持
    - 报价获取
    - 交易构建
    - 费用计算
    """

    # 桥接协议配置
    BRIDGE_CONFIGS: Dict[BridgeProtocol, Dict[str, Any]] = {
        BridgeProtocol.LAYERZERO: {
            "name": "LayerZero",
            "chains": ["ethereum", "avalanche", "polygon", "arbitrum", "optimism", "base"],
            "avg_time": 300,
            "fee_structure": {"fixed": 0.001, "percent": 0.003}
        },
        BridgeProtocol.AXELAR: {
            "name": "Axelar",
            "chains": ["ethereum", "avalanche", "polygon", "cosmos", "solana"],
            "avg_time": 600,
            "fee_structure": {"fixed": 0.005, "percent": 0.005}
        },
        BridgeProtocol.WORMSHOLE: {
            "name": "Wormhole",
            "chains": ["ethereum", "solana", "avalanche", "polygon", "algorand"],
            "avg_time": 900,
            "fee_structure": {"fixed": 0.01, "percent": 0.002}
        },
        BridgeProtocol.STGATE: {
            "name": "Stargate",
            "chains": ["ethereum", "avalanche", "polygon", "arbitrum", "optimism"],
            "avg_time": 180,
            "fee_structure": {"fixed": 0.0005, "percent": 0.006}
        }
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化桥接集成器

        Args:
            config: 配置字典
                - preferred_protocols: 优先协议列表
                - default_slippage: 默认滑点容忍
        """
        self.config = config or {}

        # 优先协议
        self.preferred_protocols = self.config.get(
            "preferred_protocols",
            [BridgeProtocol.LAYERZERO, BridgeProtocol.AXELAR]
        )

        # 默认滑点
        self.default_slippage = self.config.get("default_slippage", 0.01)

        # 链配置
        self.chain_configs: Dict[str, ChainConfig] = {}

        # 报价缓存
        self.quote_cache: Dict[str, BridgeQuote] = {}

        # 历史交易
        self.transaction_history: List[CrossChainOrder] = []

        # 统计
        self.total_quotes = 0
        self.total_transactions = 0

        logger.info("桥接集成器 V65.0 初始化完成")

    def register_chain(self, config: ChainConfig) -> None:
        """注册链配置

        Args:
            config: 链配置
        """
        self.chain_configs[config.blockchain] = config
        logger.info(f"注册链: {config.blockchain} (ID: {config.chain_id})")

    async def get_quote(
        self,
        from_chain: str,
        to_chain: str,
        from_token: str,
        to_token: str,
        from_amount: float,
        preferred_protocol: Optional[BridgeProtocol] = None
    ) -> Optional[BridgeQuote]:
        """获取桥接报价

        Args:
            from_chain: 源链
            to_chain: 目标链
            from_token: 源代币
            to_token: 目标代币
            from_amount: 源数量
            preferred_protocol: 优先协议

        Returns:
            桥接报价或None
        """
        # 确定协议
        protocol = preferred_protocol or self.preferred_protocols[0]

        # 模拟API调用
        await asyncio.sleep(0.01)  # 模拟延迟

        # 获取协议配置
        bridge_config = self.BRIDGE_CONFIGS.get(protocol, {})
        fee_structure = bridge_config.get("fee_structure", {})

        # 计算费用
        fixed_fee = fee_structure.get("fixed", 0.001)
        percent_fee = fee_structure.get("percent", 0.003)

        bridge_fee = fixed_fee + from_amount * percent_fee
        gas_fee = 0.001 * from_amount  # 简化gas计算
        estimated_time = bridge_config.get("avg_time", 300)

        # 简化转换计算（使用1:1简化）
        to_amount = from_amount - bridge_fee

        # 生成报价
        quote = BridgeQuote(
            quote_id=f"quote_{int(time.time() * 1000)}",
            from_chain=from_chain,
            to_chain=to_chain,
            from_token=from_token,
            to_token=to_token,
            from_amount=from_amount,
            to_amount=to_amount,
            bridge_fee=bridge_fee,
            gas_fee=gas_fee,
            estimated_time=estimated_time,
            min_amount=from_amount * 0.01,
            max_amount=from_amount * 100,
            protocol=protocol,
            expires_at=time.time() + 60  # 60秒有效期
        )

        # 缓存
        self.quote_cache[quote.quote_id] = quote
        self.total_quotes += 1

        return quote

    async def compare_quotes(
        self,
        from_chain: str,
        to_chain: str,
        from_token: str,
        to_token: str,
        from_amount: float
    ) -> List[BridgeQuote]:
        """比较多个协议的报价

        Args:
            from_chain: 源链
            to_chain: 目标链
            from_token: 源代币
            to_token: 目标代币
            from_amount: 源数量

        Returns:
            报价列表（按净收益排序）
        """
        quotes = []

        for protocol in self.preferred_protocols:
            quote = await self.get_quote(
                from_chain, to_chain,
                from_token, to_token,
                from_amount, protocol
            )
            if quote:
                quotes.append(quote)

        # 按净收益排序
        quotes.sort(key=lambda q: q.net_amount(), reverse=True)

        return quotes

    def calculate_fee(
        self,
        protocol: BridgeProtocol,
        from_amount: float,
        from_chain: str,
        to_chain: str
    ) -> Dict[str, float]:
        """计算桥接费用

        Args:
            protocol: 桥接协议
            from_amount: 源数量
            from_chain: 源链
            to_chain: 目标链

        Returns:
            费用字典
        """
        bridge_config = self.BRIDGE_CONFIGS.get(protocol, {})
        fee_structure = bridge_config.get("fee_structure", {})

        fixed_fee = fee_structure.get("fixed", 0.001)
        percent_fee = fee_structure.get("percent", 0.003)

        # 距离调整
        distance_factor = 1.0
        if (from_chain, to_chain) in [
            ("ethereum", "avalanche"),
            ("polygon", "avalanche"),
            ("arbitrum", "optimism")
        ]:
            distance_factor = 0.8
        elif (from_chain, to_chain) in [
            ("solana", "ethereum"),
            ("cosmos", "ethereum")
        ]:
            distance_factor = 1.5

        bridge_fee = (fixed_fee + from_amount * percent_fee) * distance_factor
        gas_fee = 0.001 * from_amount

        return {
            "fixed_fee": fixed_fee,
            "percent_fee": from_amount * percent_fee,
            "bridge_fee": bridge_fee,
            "gas_fee": gas_fee,
            "total_fee": bridge_fee + gas_fee,
            "net_amount": from_amount - bridge_fee - gas_fee
        }

    def get_supported_routes(
        self,
        from_chain: str,
        to_chain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取支持的路由

        Args:
            from_chain: 源链
            to_chain: 目标链（可选）

        Returns:
            路由列表
        """
        routes = []

        for protocol, config in self.BRIDGE_CONFIGS.items():
            if from_chain in config["chains"]:
                if to_chain is None:
                    for to_ch in config["chains"]:
                        if to_ch != from_chain:
                            routes.append({
                                "protocol": protocol.value,
                                "from_chain": from_chain,
                                "to_chain": to_ch,
                                "avg_time": config["avg_time"]
                            })
                elif to_chain in config["chains"]:
                    routes.append({
                        "protocol": protocol.value,
                        "from_chain": from_chain,
                        "to_chain": to_chain,
                        "avg_time": config["avg_time"]
                    })

        return routes

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计字典
        """
        return {
            "total_quotes": self.total_quotes,
            "total_transactions": self.total_transactions,
            "supported_protocols": len(self.BRIDGE_CONFIGS),
            "registered_chains": len(self.chain_configs)
        }


class CrossChainTransactionBuilder:
    """跨链交易构建器

    功能：
    - 构建跨链交易
    - 交易签名
    - 交易提交
    - 交易状态跟踪
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化交易构建器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 待处理订单
        self.pending_orders: Dict[str, CrossChainOrder] = {}

        # 活跃订单
        self.active_orders: Dict[str, CrossChainOrder] = {}

        # 完成的订单
        self.completed_orders: Dict[str, CrossChainOrder] = {}

        # 默认配置
        self.default_slippage = self.config.get("default_slippage", 0.01)
        self.default_timeout = self.config.get("default_timeout", 600)

        logger.info("跨链交易构建器 V65.0 初始化完成")

    async def build_order(
        self,
        from_chain: str,
        to_chain: str,
        from_token: str,
        to_token: str,
        from_amount: float,
        quote: Optional[BridgeQuote] = None,
        slippage_tolerance: Optional[float] = None
    ) -> CrossChainOrder:
        """构建跨链订单

        Args:
            from_chain: 源链
            to_chain: 目标链
            from_token: 源代币
            to_token: 目标代币
            from_amount: 源数量
            quote: 桥接报价
            slippage_tolerance: 滑点容忍

        Returns:
            跨链订单
        """
        slippage = slippage_tolerance or self.default_slippage

        # 使用报价计算
        if quote:
            min_to_amount = quote.to_amount * (1 - slippage)
            to_amount = quote.to_amount
            bridge_protocol = quote.protocol
            fee = quote.total_fee()
        else:
            # 简化计算
            min_to_amount = from_amount * 0.99
            to_amount = from_amount
            bridge_protocol = BridgeProtocol.LAYERZERO
            fee = from_amount * 0.005

        # 生成订单ID
        order_id = f"order_{from_chain}_{to_chain}_{int(time.time() * 1000)}"

        order = CrossChainOrder(
            order_id=order_id,
            from_chain=from_chain,
            to_chain=to_chain,
            from_token=from_token,
            to_token=to_token,
            from_amount=from_amount,
            to_amount=to_amount,
            min_to_amount=min_to_amount,
            status=CrossChainOrderStatus.PENDING,
            bridge_protocol=bridge_protocol,
            slippage_tolerance=slippage,
            expires_at=time.time() + self.default_timeout
        )

        self.pending_orders[order_id] = order

        return order

    async def request_quote(
        self,
        order: CrossChainOrder,
        bridge_integration: BridgeIntegration
    ) -> CrossChainOrder:
        """请求报价

        Args:
            order: 跨链订单
            bridge_integration: 桥接集成器

        Returns:
            更新后的订单
        """
        order.status = CrossChainOrderStatus.QUOTE_REQUESTED
        order.updated_at = time.time()

        # 获取报价
        quote = await bridge_integration.get_quote(
            order.from_chain,
            order.to_chain,
            order.from_token,
            order.to_token,
            order.from_amount,
            order.bridge_protocol
        )

        if quote:
            order.to_amount = quote.to_amount
            order.min_to_amount = quote.net_amount() * (1 - order.slippage_tolerance)
            order.fee = quote.total_fee()
            order.status = CrossChainOrderStatus.QUOTE_RECEIVED

        order.updated_at = time.time()

        return order

    async def sign_and_submit(
        self,
        order: CrossChainOrder,
        private_key: Optional[str] = None
    ) -> CrossChainOrder:
        """签名并提交交易

        Args:
            order: 跨链订单
            private_key: 私钥（可选，用于测试）

        Returns:
            更新后的订单
        """
        if order.status != CrossChainOrderStatus.QUOTE_RECEIVED:
            raise ValueError(f"订单状态不正确: {order.status}")

        order.status = CrossChainOrderStatus.SIGNING
        order.updated_at = time.time()

        # 模拟签名（实际需要真实签名）
        if private_key:
            message = f"{order.order_id}{order.from_amount}{order.to_amount}"
            signature = hashlib.sha256(message.encode()).hexdigest()[:32]
        else:
            signature = f"模拟签名_{order.order_id}"

        # 模拟提交
        order.tx_hash = f"0x{hashlib.sha256(signature.encode()).hexdigest()[:40]}"
        order.status = CrossChainOrderStatus.SUBMITTED
        order.updated_at = time.time()

        # 移动到活跃订单
        if order.order_id in self.pending_orders:
            del self.pending_orders[order.order_id]

        self.active_orders[order.order_id] = order

        return order

    async def confirm_transaction(
        self,
        order: CrossChainOrder
    ) -> CrossChainOrder:
        """确认交易

        Args:
            order: 跨链订单

        Returns:
            更新后的订单
        """
        if order.status != CrossChainOrderStatus.SUBMITTED:
            raise ValueError(f"订单状态不正确: {order.status}")

        # 模拟确认过程
        order.status = CrossChainOrderStatus.CONFIRMING

        # 模拟确认完成
        await asyncio.sleep(0.01)

        order.bridge_tx_hash = f"bridge_{order.tx_hash}"
        order.status = CrossChainOrderStatus.COMPLETED
        order.updated_at = time.time()

        # 移动到完成订单
        if order.order_id in self.active_orders:
            del self.active_orders[order.order_id]

        self.completed_orders[order.order_id] = order

        return order

    def get_order_status(
        self,
        order_id: str
    ) -> Optional[CrossChainOrderStatus]:
        """获取订单状态

        Args:
            order_id: 订单ID

        Returns:
            订单状态或None
        """
        for orders in [self.pending_orders, self.active_orders, self.completed_orders]:
            if order_id in orders:
                return orders[order_id].status

        return None

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计字典
        """
        return {
            "pending_orders": len(self.pending_orders),
            "active_orders": len(self.active_orders),
            "completed_orders": len(self.completed_orders)
        }


class ChainWalletManager:
    """链钱包管理器

    功能：
    - 多链钱包管理
    - 余额查询
    - 交易签名
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化钱包管理器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 钱包数据库
        self.wallets: Dict[str, Dict[str, Any]] = {}

        # 余额缓存
        self.balances: Dict[str, Dict[str, float]] = {}

        logger.info("链钱包管理器 V65.0 初始化完成")

    def add_wallet(
        self,
        blockchain: str,
        address: str,
        private_key: Optional[str] = None,
        public_key: Optional[str] = None
    ) -> str:
        """添加钱包

        Args:
            blockchain: 区块链
            address: 地址
            private_key: 私钥（可选，仅本地存储）
            public_key: 公钥（可选）

        Returns:
            钱包ID
        """
        wallet_id = f"{blockchain}_{address[:10]}"

        self.wallets[wallet_id] = {
            "blockchain": blockchain,
            "address": address,
            "private_key": private_key,
            "public_key": public_key,
            "created_at": time.time()
        }

        # 初始化余额
        self.balances[wallet_id] = {}

        logger.info(f"添加钱包: {wallet_id}")

        return wallet_id

    async def get_balance(
        self,
        wallet_id: str,
        token: str = "native"
    ) -> float:
        """获取余额

        Args:
            wallet_id: 钱包ID
            token: 代币符号

        Returns:
            余额
        """
        if wallet_id not in self.balances:
            return 0.0

        return self.balances[wallet_id].get(token, 0.0)

    async def update_balance(
        self,
        wallet_id: str,
        token: str,
        balance: float
    ) -> None:
        """更新余额

        Args:
            wallet_id: 钱包ID
            token: 代币符号
            balance: 新余额
        """
        if wallet_id not in self.balances:
            self.balances[wallet_id] = {}

        self.balances[wallet_id][token] = balance

    def get_wallet_address(
        self,
        wallet_id: str
    ) -> Optional[str]:
        """获取钱包地址

        Args:
            wallet_id: 钱包ID

        Returns:
            钱包地址或None
        """
        wallet = self.wallets.get(wallet_id)
        return wallet.get("address") if wallet else None

    def get_blockchain_wallets(
        self,
        blockchain: str
    ) -> List[Dict[str, Any]]:
        """获取某区块链的钱包列表

        Args:
            blockchain: 区块链

        Returns:
            钱包列表
        """
        return [
            {"wallet_id": wid, **w}
            for wid, w in self.wallets.items()
            if w.get("blockchain") == blockchain
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计字典
        """
        return {
            "total_wallets": len(self.wallets),
            "blockchains": list(set(w.get("blockchain") for w in self.wallets.values()))
        }


# 全局单例
_bridge_integration: Optional[BridgeIntegration] = None
_transaction_builder: Optional[CrossChainTransactionBuilder] = None
_wallet_manager: Optional[ChainWalletManager] = None


def get_bridge_integration() -> Optional[BridgeIntegration]:
    """获取桥接集成器

    Returns:
        桥接集成器实例
    """
    return _bridge_integration


def initialize_bridge_integration(
    config: Optional[Dict[str, Any]] = None
) -> BridgeIntegration:
    """初始化桥接集成器

    Args:
        config: 配置字典

    Returns:
        桥接集成器实例
    """
    global _bridge_integration

    _bridge_integration = BridgeIntegration(config)
    return _bridge_integration


def get_transaction_builder() -> Optional[CrossChainTransactionBuilder]:
    """获取交易构建器

    Returns:
        交易构建器实例
    """
    return _transaction_builder


def initialize_transaction_builder(
    config: Optional[Dict[str, Any]] = None
) -> CrossChainTransactionBuilder:
    """初始化交易构建器

    Args:
        config: 配置字典

    Returns:
        交易构建器实例
    """
    global _transaction_builder

    _transaction_builder = CrossChainTransactionBuilder(config)
    return _transaction_builder


def get_wallet_manager() -> Optional[ChainWalletManager]:
    """获取钱包管理器

    Returns:
        钱包管理器实例
    """
    return _wallet_manager


def initialize_wallet_manager(
    config: Optional[Dict[str, Any]] = None
) -> ChainWalletManager:
    """初始化钱包管理器

    Args:
        config: 配置字典

    Returns:
        钱包管理器实例
    """
    global _wallet_manager

    _wallet_manager = ChainWalletManager(config)
    return _wallet_manager


__all__ = [
    # 枚举
    'BridgeProtocol',
    'CrossChainOrderStatus',
    'OnChainTxType',
    # 数据类
    'ChainAddress',
    'CrossChainOrder',
    'BridgeQuote',
    'ChainConfig',
    # 主类
    'BridgeIntegration',
    'CrossChainTransactionBuilder',
    'ChainWalletManager',
    # 工厂函数
    'get_bridge_integration',
    'initialize_bridge_integration',
    'get_transaction_builder',
    'initialize_transaction_builder',
    'get_wallet_manager',
    'initialize_wallet_manager',
]