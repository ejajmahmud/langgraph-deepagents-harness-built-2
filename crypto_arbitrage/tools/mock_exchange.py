"""模拟交易所 - V3.0

提供完整的模拟交易所功能，用于安全测试套利策略：
- 模拟价格数据生成（支持不同市场条件）
- 模拟订单簿
- 模拟交易执行
- 模拟账户管理
- 模拟手续费
- 模拟网络延迟
- 模拟滑点
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal

logger = logging.getLogger(__name__)


class MockOrder:
    """模拟订单"""

    def __init__(
        self,
        order_id: str,
        symbol: str,
        side: str,
        order_type: str,
        amount: float,
        price: Optional[float] = None,
        timestamp: Optional[float] = None
    ):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side  # 'buy' or 'sell'
        self.order_type = order_type  # 'market' or 'limit'
        self.amount = amount
        self.price = price
        self.timestamp = timestamp or time.time()
        self.filled_amount = 0.0
        self.status = 'open'
        self.fills: List[Dict] = []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'type': self.order_type,
            'amount': self.amount,
            'price': self.price,
            'filled': self.filled_amount,
            'remaining': self.amount - self.filled_amount,
            'status': self.status,
            'timestamp': self.timestamp,
            'fills': self.fills
        }


class MockAccount:
    """模拟账户"""

    def __init__(self, initial_balance: Dict[str, float]):
        """初始化模拟账户

        Args:
            initial_balance: 初始余额，如 {'USDT': 10000, 'BTC': 0.1}
        """
        self.balances = initial_balance.copy()
        self.orders: List[MockOrder] = []
        self.trades: List[Dict] = []
        self.order_id_counter = 0

    def get_balance(self, currency: str) -> float:
        """获取余额"""
        return self.balances.get(currency, 0.0)

    def get_all_balances(self) -> Dict[str, float]:
        """获取所有余额"""
        return self.balances.copy()

    def create_order_id(self) -> str:
        """生成订单ID"""
        self.order_id_counter += 1
        return f"MOCK-{int(time.time())}-{self.order_id_counter:06d}"

    def add_order(self, order: MockOrder) -> None:
        """添加订单"""
        self.orders.append(order)

    def get_order(self, order_id: str) -> Optional[MockOrder]:
        """获取订单"""
        for order in self.orders:
            if order.order_id == order_id:
                return order
        return None

    def update_balance(self, currency: str, amount: float) -> None:
        """更新余额"""
        self.balances[currency] = self.balances.get(currency, 0.0) + amount

    def add_trade(self, trade: Dict[str, Any]) -> None:
        """添加交易记录"""
        self.trades.append(trade)


class MockExchange:
    """模拟交易所

    提供完整的交易所功能模拟，用于测试套利策略。
    """

    def __init__(
        self,
        name: str,
        initial_prices: Dict[str, float],
        fee_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        latency_ms: int = 100,
        volatility: float = 0.001,
        trend: float = 0.0
    ):
        """初始化模拟交易所

        Args:
            name: 交易所名称
            initial_prices: 初始价格，如 {'BTC/USDT': 50000, 'ETH/USDT': 3000}
            fee_rate: 手续费率（默认0.1%）
            slippage_rate: 滑点率（默认0.05%）
            latency_ms: 网络延迟（毫秒）
            volatility: 价格波动率（默认0.1%）
            trend: 价格趋势（正数上涨，负数下跌，0震荡）
        """
        self.name = name
        self.prices = initial_prices.copy()
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self.latency_ms = latency_ms
        self.volatility = volatility
        self.trend = trend

        # 订单簿深度
        self.order_book_depth = 10
        self.order_books: Dict[str, Dict] = {}

        # 账户
        self.account = MockAccount({
            'USDT': 100000.0,
            'BTC': 1.0,
            'ETH': 10.0,
            'BNB': 50.0,
            'SOL': 100.0
        })

        # 交易历史
        self.trade_history: List[Dict] = []

        # 初始化订单簿
        self._initialize_order_books()

        logger.info(
            f"模拟交易所 {name} 初始化完成: "
            f"{len(initial_prices)} 个交易对, "
            f"手续费 {fee_rate*100:.2f}%, "
            f"滑点 {slippage_rate*100:.2f}%"
        )

    def _initialize_order_books(self) -> None:
        """初始化所有交易对的订单簿"""
        for symbol, price in self.prices.items():
            self.order_books[symbol] = self._generate_order_book(symbol, price)

    def _generate_order_book(
        self,
        symbol: str,
        base_price: float
    ) -> Dict[str, Any]:
        """生成订单簿

        Args:
            symbol: 交易对
            base_price: 基准价格

        Returns:
            订单簿字典
        """
        # 分解交易对
        base, quote = symbol.split('/')

        bids = []
        asks = []

        # 生成买单（低于基准价）
        for i in range(self.order_book_depth):
            price = base_price * (1.0 - (i + 1) * 0.0005)
            amount = random.uniform(0.1, 5.0)
            bids.append([price, amount])

        # 生成卖单（高于基准价）
        for i in range(self.order_book_depth):
            price = base_price * (1.0 + (i + 1) * 0.0005)
            amount = random.uniform(0.1, 5.0)
            asks.append([price, amount])

        # 排序
        bids.sort(key=lambda x: x[0], reverse=True)  # 买单从高到低
        asks.sort(key=lambda x: x[0])  # 卖单从低到高

        return {
            'bids': bids,
            'asks': asks,
            'timestamp': int(time.time() * 1000),
            'datetime': datetime.now().isoformat()
        }

    async def simulate_latency(self) -> None:
        """模拟网络延迟"""
        if self.latency_ms > 0:
            delay = random.gauss(self.latency_ms, self.latency_ms * 0.2)
            delay = max(0, delay / 1000.0)  # 转换为秒
            await asyncio.sleep(delay)

    def update_prices(self) -> None:
        """更新价格（模拟市场波动）"""
        for symbol in self.prices:
            # 随机游走 + 趋势
            change = random.gauss(0, self.volatility) + self.trend
            new_price = self.prices[symbol] * (1.0 + change)
            self.prices[symbol] = max(0.0001, new_price)

            # 更新订单簿
            self.order_books[symbol] = self._generate_order_book(
                symbol, self.prices[symbol]
            )

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取交易对行情

        Args:
            symbol: 交易对

        Returns:
            行情数据
        """
        await self.simulate_latency()

        if symbol not in self.prices:
            raise ValueError(f"交易对 {symbol} 不存在")

        base_price = self.prices[symbol]
        order_book = self.order_books[symbol]

        bid = order_book['bids'][0][0] if order_book['bids'] else base_price
        ask = order_book['asks'][0][0] if order_book['asks'] else base_price

        return {
            'symbol': symbol,
            'timestamp': int(time.time() * 1000),
            'datetime': datetime.now().isoformat(),
            'high': base_price * 1.02,
            'low': base_price * 0.98,
            'bid': bid,
            'bidVolume': order_book['bids'][0][1] if order_book['bids'] else 0,
            'ask': ask,
            'askVolume': order_book['asks'][0][1] if order_book['asks'] else 0,
            'vwap': base_price,
            'open': base_price * 0.99,
            'close': base_price,
            'last': base_price,
            'previousClose': base_price * 0.99,
            'change': base_price * 0.01,
            'percentage': 1.0,
            'average': base_price,
            'baseVolume': random.uniform(100, 1000),
            'quoteVolume': random.uniform(100000, 1000000),
            'info': {}
        }

    async def fetch_order_book(
        self,
        symbol: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取订单簿

        Args:
            symbol: 交易对
            limit: 深度限制

        Returns:
            订单簿数据
        """
        await self.simulate_latency()

        if symbol not in self.order_books:
            raise ValueError(f"交易对 {symbol} 不存在")

        order_book = self.order_books[symbol].copy()

        if limit:
            order_book['bids'] = order_book['bids'][:limit]
            order_book['asks'] = order_book['asks'][:limit]

        return order_book

    async def fetch_balance(self) -> Dict[str, Any]:
        """获取账户余额

        Returns:
            余额数据
        """
        await self.simulate_latency()

        balances = {}
        for currency, amount in self.account.get_all_balances().items():
            if amount > 0:
                balances[currency] = {
                    'free': amount,
                    'used': 0.0,
                    'total': amount
                }

        return {
            'timestamp': int(time.time() * 1000),
            'datetime': datetime.now().isoformat(),
            'info': {},
            'balances': balances
        }

    async def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float
    ) -> Dict[str, Any]:
        """创建市价单

        Args:
            symbol: 交易对
            side: 买卖方向 ('buy' or 'sell')
            amount: 数量

        Returns:
            订单信息
        """
        await self.simulate_latency()

        if symbol not in self.prices:
            raise ValueError(f"交易对 {symbol} 不存在")

        # 解析交易对
        base, quote = symbol.split('/')

        # 创建订单
        order_id = self.account.create_order_id()
        order = MockOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type='market',
            amount=amount
        )

        # 计算执行价格（带滑点）
        order_book = self.order_books[symbol]
        if side == 'buy':
            # 买入：使用卖一价 + 滑点
            if order_book['asks']:
                execution_price = order_book['asks'][0][0] * (1.0 + self.slippage_rate)
            else:
                execution_price = self.prices[symbol] * (1.0 + self.slippage_rate)
        else:
            # 卖出：使用买一价 - 滑点
            if order_book['bids']:
                execution_price = order_book['bids'][0][0] * (1.0 - self.slippage_rate)
            else:
                execution_price = self.prices[symbol] * (1.0 - self.slippage_rate)

        # 计算手续费
        fee = amount * execution_price * self.fee_rate

        # 执行交易
        if side == 'buy':
            # 买入：扣除quote，获得base
            cost = amount * execution_price + fee
            if self.account.get_balance(quote) < cost:
                raise ValueError(f"{quote} 余额不足")

            self.account.update_balance(quote, -cost)
            self.account.update_balance(base, amount)
        else:
            # 卖出：扣除base，获得quote
            if self.account.get_balance(base) < amount:
                raise ValueError(f"{base} 余额不足")

            proceeds = amount * execution_price - fee
            self.account.update_balance(base, -amount)
            self.account.update_balance(quote, proceeds)

        # 更新订单状态
        order.filled_amount = amount
        order.status = 'closed'
        order.fills.append({
            'price': execution_price,
            'amount': amount,
            'cost': amount * execution_price,
            'fee': fee,
            'timestamp': time.time()
        })

        # 记录交易
        trade = {
            'id': f"TRADE-{order_id}",
            'order': order_id,
            'symbol': symbol,
            'side': side,
            'price': execution_price,
            'amount': amount,
            'cost': amount * execution_price,
            'fee': fee,
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'takerOrMaker': 'taker'
        }

        self.account.add_trade(trade)
        self.trade_history.append(trade)
        self.account.add_order(order)

        logger.info(
            f"[{self.name}] 市价单执行: {side} {amount} {base} @ {execution_price:.2f} {quote}, "
            f"手续费 {fee:.4f} {quote}"
        )

        return order.to_dict()

    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float
    ) -> Dict[str, Any]:
        """创建限价单

        Args:
            symbol: 交易对
            side: 买卖方向
            amount: 数量
            price: 价格

        Returns:
            订单信息
        """
        await self.simulate_latency()

        if symbol not in self.prices:
            raise ValueError(f"交易对 {symbol} 不存在")

        # 创建订单
        order_id = self.account.create_order_id()
        order = MockOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type='limit',
            amount=amount,
            price=price
        )

        self.account.add_order(order)

        logger.info(
            f"[{self.name}] 限价单创建: {side} {amount} @ {price} "
            f"(订单ID: {order_id})"
        )

        return order.to_dict()

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """取消订单

        Args:
            order_id: 订单ID

        Returns:
            取消结果
        """
        await self.simulate_latency()

        order = self.account.get_order(order_id)
        if not order:
            raise ValueError(f"订单 {order_id} 不存在")

        if order.status != 'open':
            raise ValueError(f"订单 {order_id} 状态为 {order.status}，无法取消")

        order.status = 'canceled'

        logger.info(f"[{self.name}] 订单取消: {order_id}")

        return order.to_dict()

    async def fetch_order(self, order_id: str) -> Dict[str, Any]:
        """获取订单信息

        Args:
            order_id: 订单ID

        Returns:
            订单信息
        """
        await self.simulate_latency()

        order = self.account.get_order(order_id)
        if not order:
            raise ValueError(f"订单 {order_id} 不存在")

        return order.to_dict()

    async def fetch_my_trades(
        self,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """获取交易历史

        Args:
            symbol: 交易对过滤
            since: 时间戳过滤
            limit: 数量限制

        Returns:
            交易列表
        """
        await self.simulate_latency()

        trades = self.account.trades.copy()

        # 过滤
        if symbol:
            trades = [t for t in trades if t['symbol'] == symbol]

        if since:
            trades = [t for t in trades if t['timestamp'] >= since]

        # 排序（最新的在前）
        trades.sort(key=lambda x: x['timestamp'], reverse=True)

        # 限制数量
        if limit:
            trades = trades[:limit]

        return trades

    def get_trading_fees(self, symbol: str) -> Dict[str, float]:
        """获取交易手续费

        Args:
            symbol: 交易对

        Returns:
            手续费信息
        """
        return {
            'trading': {
                'maker': self.fee_rate,
                'taker': self.fee_rate
            }
        }

    def set_market_condition(
        self,
        volatility: Optional[float] = None,
        trend: Optional[float] = None,
        slippage: Optional[float] = None
    ) -> None:
        """设置市场条件

        Args:
            volatility: 波动率
            trend: 趋势
            slippage: 滑点
        """
        if volatility is not None:
            self.volatility = volatility
        if trend is not None:
            self.trend = trend
        if slippage is not None:
            self.slippage_rate = slippage

        logger.info(
            f"[{self.name}] 市场条件更新: "
            f"波动率={self.volatility:.3f}, "
            f"趋势={self.trend:.3f}, "
            f"滑点={self.slippage_rate:.3f}"
        )

    def get_account_summary(self) -> Dict[str, Any]:
        """获取账户摘要"""
        balances = self.account.get_all_balances()

        # 计算总资产价值（按USDT计价）
        total_usdt = balances.get('USDT', 0.0)
        for symbol, price in self.prices.items():
            base = symbol.split('/')[0]
            if base in balances and base != 'USDT':
                total_usdt += balances[base] * price

        return {
            'exchange': self.name,
            'total_usdt': total_usdt,
            'balances': balances,
            'total_orders': len(self.account.orders),
            'total_trades': len(self.account.trades),
            'open_orders': sum(1 for o in self.account.orders if o.status == 'open')
        }


def create_mock_exchange(
    name: str,
    initial_prices: Optional[Dict[str, float]] = None,
    fee_rate: float = 0.001,
    slippage_rate: float = 0.0005,
    latency_ms: int = 100,
    volatility: float = 0.001,
    trend: float = 0.0
) -> MockExchange:
    """工厂函数：创建模拟交易所

    Args:
        name: 交易所名称
        initial_prices: 初始价格
        fee_rate: 手续费率
        slippage_rate: 滑点率
        latency_ms: 延迟
        volatility: 波动率
        trend: 趋势

    Returns:
        MockExchange实例
    """
    if initial_prices is None:
        # 默认价格
        initial_prices = {
            'BTC/USDT': 50000.0,
            'ETH/USDT': 3000.0,
            'BNB/USDT': 400.0,
            'SOL/USDT': 150.0,
            'DOGE/USDT': 0.15,
            'ETH/BTC': 0.06,
            'BNB/BTC': 0.008,
            'SOL/BTC': 0.003
        }

    return MockExchange(
        name=name,
        initial_prices=initial_prices,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        latency_ms=latency_ms,
        volatility=volatility,
        trend=trend
    )
