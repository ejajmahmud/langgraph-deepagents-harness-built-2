"""市场数据管理器 - Phase 13核心模块

管理市场数据的获取、清洗、存储和质量监控。

核心功能：
1. 实时数据获取 - 从多个交易所获取实时市场数据
2. 数据清洗和标准化 - 清洗和标准化市场数据
3. 数据缓存管理 - 缓存市场数据，减少API调用
4. 数据质量监控 - 监控数据质量和可用性
5. 数据存储 - 持久化市场数据到Memo0

创建时间：2026-04-19 23:07:00
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class DataQuality(Enum):
    """数据质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"


class MarketDataManager:
    """市场数据管理器

    管理市场数据的获取、清洗和存储。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化市场数据管理器

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 数据源
        self.data_sources: Dict[str, Dict] = {}
        self.active_data_source: Optional[str] = None

        # 数据缓存
        self.price_cache: Dict[str, Dict] = defaultdict(dict)
        self.order_book_cache: Dict[str, Dict] = defaultdict(dict)
        self.trade_history_cache: Dict[str, List[Dict]] = defaultdict(list)

        # 缓存配置
        self.price_cache_ttl = self.config.get('price_cache_ttl', 5)  # 秒
        self.order_book_cache_ttl = self.config.get('order_book_cache_ttl', 2)  # 秒
        self.trade_history_cache_size = self.config.get('trade_history_cache_size', 1000)
        self.enable_cache = self.config.get('enable_cache', True)

        # 数据质量监控
        self.data_quality_stats: Dict[str, Dict] = defaultdict(dict)
        self.quality_thresholds = {
            'max_price_change_percent': 20.0,  # 最大价格变化百分比
            'min_order_book_depth': 10,          # 最小订单簿深度
            'max_data_delay_ms': 1000,          # 最大数据延迟（毫秒）
        }

        # 数据收集任务
        self._data_collection_task: Optional[asyncio.Task] = None
        self._data_collection_interval = self.config.get('data_collection_interval', 1)  # 秒

        # 实时WebSocket支持 (V16.7新增)
        self.enable_realtime = self.config.get('enable_realtime', False)
        self._ws_connections: Dict[str, Any] = {}  # exchange -> websocket connection
        self._ws_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # exchange -> symbol set
        self._realtime_price_callbacks: List[Callable] = []  # 实时价格回调

        # 统计信息
        self.stats = {
            'total_data_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'data_errors': 0,
            'data_source_switches': 0,
        }

        # 存储引用
        self.storage: Optional[Any] = None

        logger.info("✅ 市场数据管理器初始化完成")

    async def initialize(self) -> bool:
        """初始化数据源

        Returns:
            是否成功
        """
        logger.info("🚀 初始化市场数据管理器...")

        try:
            # 注册默认数据源
            await self._register_default_data_sources()

            # 选择活动数据源
            if self.data_sources:
                self.active_data_source = next(iter(self.data_sources.keys()))
                logger.info(f"✅ 活动数据源: {self.active_data_source}")
            else:
                logger.warning("⚠️ 未注册数据源，使用模拟数据")
                self.active_data_source = 'simulation'

            # 启动数据收集任务
            self._data_collection_task = asyncio.create_task(
                self._data_collection_loop()
            )

            logger.info("✅ 市场数据管理器初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 市场数据管理器初始化失败: {e}")
            return False

    async def start(self) -> bool:
        """启动数据收集

        Returns:
            是否成功
        """
        logger.info("🚀 启动数据收集...")
        logger.info("✅ 数据收集已启动")
        return True

    async def stop(self) -> bool:
        """停止数据收集

        Returns:
            是否成功
        """
        logger.info("🛑 停止数据收集...")

        try:
            # 停止数据收集任务
            if self._data_collection_task:
                self._data_collection_task.cancel()
                try:
                    await self._data_collection_task
                except asyncio.CancelledError:
                    pass

            logger.info("✅ 数据收集已停止")
            return True

        except Exception as e:
            logger.error(f"❌ 停止数据收集失败: {e}")
            return False

    async def get_market_data(
        self,
        symbols: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """获取市场数据

        Args:
            symbols: 交易对列表

        Returns:
            市场数据字典
        """
        self.stats['total_data_requests'] += 1

        try:
            # 使用默认交易对
            if symbols is None:
                symbols = self.config.get('default_symbols', ['BTCUSDT', 'ETHUSDT'])

            # 收集所有市场数据
            market_data = {
                'timestamp': datetime.now().isoformat(),
                'symbols': {},
            }

            # 获取价格数据
            price_data = await self.get_price_ticker(symbols)
            if price_data:
                market_data['prices'] = price_data
                for symbol, data in price_data.items():
                    market_data['symbols'][symbol] = {
                        **market_data['symbols'].get(symbol, {}),
                        'price': data,
                    }

            # 获取订单簿
            order_book_data = await self.get_order_book(symbols[:3])  # 限制数量
            if order_book_data:
                market_data['order_books'] = order_book_data
                for symbol, data in order_book_data.items():
                    market_data['symbols'][symbol] = {
                        **market_data['symbols'].get(symbol, {}),
                        'order_book': data,
                    }

            # 获取交易历史
            trade_data = await self.get_trade_history(symbols[0])  # 只获取一个
            if trade_data:
                market_data['trade_history'] = trade_data

            # 评估数据质量
            data_quality = self.assess_data_quality(market_data)
            market_data['data_quality'] = data_quality

            # 持久化数据
            await self.persist_market_data(market_data)

            return market_data

        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            self.stats['data_errors'] += 1
            return None

    async def get_price_ticker(
        self,
        symbols: List[str]
    ) -> Optional[Dict[str, Dict]]:
        """获取价格行情

        Args:
            symbols: 交易对列表

        Returns:
            价格字典
        """
        try:
            price_data = {}

            for symbol in symbols:
                # 检查缓存
                if self.enable_cache:
                    cached_data = self._get_from_price_cache(symbol)
                    if cached_data:
                        self.stats['cache_hits'] += 1
                        price_data[symbol] = cached_data
                        continue

                    self.stats['cache_misses'] += 1

                # 从数据源获取
                data = await self._fetch_price_from_source(symbol)
                if data:
                    # 验证数据质量
                    quality = self._validate_price_data(data)
                    if quality != DataQuality.INVALID:
                        # 添加到缓存
                        if self.enable_cache:
                            self._add_to_price_cache(symbol, data)

                        price_data[symbol] = data
                        self._update_data_quality_stats(symbol, 'price', quality)

            return price_data if price_data else None

        except Exception as e:
            logger.error(f"获取价格行情失败: {e}")
            return None

    async def get_order_book(
        self,
        symbols: List[str],
        limit: int = 20
    ) -> Optional[Dict[str, Dict]]:
        """获取订单簿

        Args:
            symbols: 交易对列表
            limit: 深度限制

        Returns:
            订单簿字典
        """
        try:
            order_book_data = {}

            for symbol in symbols:
                # 检查缓存
                if self.enable_cache:
                    cached_data = self._get_from_order_book_cache(symbol)
                    if cached_data:
                        self.stats['cache_hits'] += 1
                        order_book_data[symbol] = cached_data
                        continue

                    self.stats['cache_misses'] += 1

                # 从数据源获取
                data = await self._fetch_order_book_from_source(symbol, limit)
                if data:
                    # 验证数据质量
                    quality = self._validate_order_book_data(data)
                    if quality != DataQuality.INVALID:
                        # 添加到缓存
                        if self.enable_cache:
                            self._add_to_order_book_cache(symbol, data)

                        order_book_data[symbol] = data
                        self._update_data_quality_stats(symbol, 'order_book', quality)

            return order_book_data if order_book_data else None

        except Exception as e:
            logger.error(f"获取订单簿失败: {e}")
            return None

    async def get_trade_history(
        self,
        symbol: str,
        limit: int = 100
    ) -> Optional[List[Dict]]:
        """获取交易历史

        Args:
            symbol: 交易对
            limit: 数量限制

        Returns:
            交易历史列表
        """
        try:
            # 从缓存获取
            if self.enable_cache:
                cached_data = self.trade_history_cache.get(symbol, [])
                if cached_data:
                    return cached_data[:limit]

            # 从数据源获取
            data = await self._fetch_trade_history_from_source(symbol, limit)
            if data:
                # 添加到缓存
                if self.enable_cache:
                    self.trade_history_cache[symbol] = data

            return data

        except Exception as e:
            logger.error(f"获取交易历史失败: {e}")
            return None

    def register_data_source(
        self,
        name: str,
        source_config: Dict[str, Any]
    ) -> None:
        """注册数据源

        Args:
            name: 数据源名称
            source_config: 数据源配置
        """
        self.data_sources[name] = source_config
        logger.info(f"注册数据源: {name}")

    def remove_data_source(self, name: str) -> None:
        """移除数据源

        Args:
            name: 数据源名称
        """
        if name in self.data_sources:
            del self.data_sources[name]
            logger.info(f"移除数据源: {name}")

    async def switch_data_source(self, name: str) -> bool:
        """切换数据源

        Args:
            name: 数据源名称

        Returns:
            是否成功
        """
        if name not in self.data_sources:
            logger.error(f"数据源不存在: {name}")
            return False

        old_source = self.active_data_source
        self.active_data_source = name
        self.stats['data_source_switches'] += 1

        logger.info(f"切换数据源: {old_source} -> {name}")
        return True

    def check_data_source_health(self, name: str) -> Dict[str, Any]:
        """检查数据源健康状态

        Args:
            name: 数据源名称

        Returns:
            健康状态字典
        """
        if name not in self.data_sources:
            return {
                'healthy': False,
                'reason': 'Data source not found',
            }

        # 检查数据质量统计
        quality_stats = self.data_quality_stats.get(name, {})

        # 计算健康评分
        if not quality_stats:
            return {
                'healthy': True,
                'score': 100,
                'reason': 'No data yet',
            }

        # 简单的健康评分逻辑
        invalid_count = sum(
            1 for stats in quality_stats.values()
            if stats.get('invalid', 0) > 0
        )

        total_requests = sum(
            stats.get('total', 0)
            for stats in quality_stats.values()
        )

        if total_requests == 0:
            return {
                'healthy': True,
                'score': 100,
                'reason': 'No data yet',
            }

        health_score = max(0, 100 - (invalid_count / total_requests * 100))

        return {
            'healthy': health_score > 70,
            'score': health_score,
            'invalid_count': invalid_count,
            'total_requests': total_requests,
        }

    def assess_data_quality(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估数据质量

        Args:
            market_data: 市场数据字典

        Returns:
            数据质量字典
        """
        quality = {
            'overall': DataQuality.GOOD.value,
            'details': {},
        }

        # 评估价格数据
        if 'prices' in market_data:
            price_quality = self._assess_price_quality(market_data['prices'])
            quality['details']['price'] = price_quality

        # 评估订单簿数据
        if 'order_books' in market_data:
            order_book_quality = self._assess_order_book_quality(
                market_data['order_books']
            )
            quality['details']['order_book'] = order_book_quality

        # 计算整体质量
        details = quality['details']
        if details:
            qualities = [
                detail.get('quality', DataQuality.FAIR.value)
                for detail in details.values()
            ]

            # 优先级排序
            quality_order = [
                DataQuality.EXCELLENT.value,
                DataQuality.GOOD.value,
                DataQuality.FAIR.value,
                DataQuality.POOR.value,
                DataQuality.INVALID.value,
            ]

            min_quality_index = min(
                quality_order.index(q) if q in quality_order else len(quality_order)
                for q in qualities
            )

            quality['overall'] = quality_order[min_quality_index]

        return quality

    async def persist_market_data(self, market_data: Dict[str, Any]) -> None:
        """持久化市场数据

        Args:
            market_data: 市场数据字典
        """
        try:
            if self.storage:
                await self.storage.add_knowledge(
                    content=f"Market data: {market_data.get('timestamp')}",
                    metadata={
                        'type': 'market_data',
                        'timestamp': market_data.get('timestamp'),
                        'symbols': list(market_data.get('symbols', {}).keys()),
                        'data_quality': market_data.get('data_quality', {}).get('overall'),
                    }
                )
        except Exception as e:
            logger.error(f"持久化市场数据失败: {e}")

    async def query_historical_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[List[Dict]]:
        """查询历史数据

        Args:
            symbol: 交易对
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            历史数据列表
        """
        try:
            if self.storage:
                results = await self.storage.search_knowledge(
                    query=f"symbol:{symbol} type:market_data",
                    top_k=1000,
                )

                # 过滤时间范围
                filtered_results = []
                for result in results:
                    metadata = result.get('metadata', {})
                    timestamp_str = metadata.get('timestamp', '')
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                            if start_time <= timestamp <= end_time:
                                filtered_results.append(result)
                        except ValueError:
                            continue

                return filtered_results

        except Exception as e:
            logger.error(f"查询历史数据失败: {e}")
            return None

    def export_data(
        self,
        data: Dict[str, Any],
        format: str = 'json'
    ) -> str:
        """导出数据

        Args:
            data: 数据字典
            format: 导出格式（json/csv）

        Returns:
            导出的数据字符串
        """
        try:
            if format == 'json':
                import json
                return json.dumps(data, indent=2, default=str)
            elif format == 'csv':
                import csv
                import io

                output = io.StringIO()
                writer = csv.writer(output)

                # 扁平化数据
                flattened = self._flatten_dict(data)
                writer.writerow(flattened.keys())
                writer.writerow(flattened.values())

                return output.getvalue()
            else:
                raise ValueError(f"不支持的格式: {format}")

        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            return ""

    # ========== 私有方法 ==========

    async def _register_default_data_sources(self) -> None:
        """注册默认数据源"""
        # 注册模拟数据源
        self.register_data_source('simulation', {
            'type': 'simulation',
            'enabled': True,
        })

    async def _data_collection_loop(self) -> None:
        """数据收集循环"""
        while True:
            try:
                # 定期更新缓存数据
                await self._update_caches()

                # 等待下一个周期
                await asyncio.sleep(self._data_collection_interval)

            except asyncio.CancelledError:
                logger.info("数据收集任务已取消")
                break
            except Exception as e:
                logger.error(f"数据收集失败: {e}")
                await asyncio.sleep(10)  # 错误后等待10秒

    async def _update_caches(self) -> None:
        """更新缓存"""
        try:
            # 这里可以添加主动更新缓存的逻辑
            # 例如定期获取最新价格
            pass
        except Exception as e:
            logger.error(f"更新缓存失败: {e}")

    async def _fetch_price_from_source(self, symbol: str) -> Optional[Dict]:
        """从数据源获取价格

        Args:
            symbol: 交易对

        Returns:
            价格数据字典
        """
        try:
            # 根据活动数据源获取数据
            if self.active_data_source == 'simulation':
                return await self._generate_simulation_price(symbol)
            else:
                # 其他数据源的实现
                logger.warning(f"未实现数据源: {self.active_data_source}")
                return None

        except Exception as e:
            logger.error(f"获取价格失败: {e}")
            return None

    async def _generate_simulation_price(self, symbol: str) -> Dict:
        """生成模拟价格数据

        Args:
            symbol: 交易对

        Returns:
            价格数据字典
        """
        import random

        # 基于交易对生成基础价格
        base_prices = {
            'BTCUSDT': 65000.0,
            'ETHUSDT': 3500.0,
            'BNBUSDT': 550.0,
        }

        base_price = base_prices.get(symbol, 100.0)

        # 添加随机波动
        change_percent = random.uniform(-0.01, 0.01)  # ±1%
        price = base_price * (1 + change_percent)

        return {
            'symbol': symbol,
            'price': round(price, 2),
            'bid': round(price * 0.9995, 2),  # -0.05%
            'ask': round(price * 1.0005, 2),   # +0.05%
            'change_24h': round(change_percent * 100, 2),
            'volume_24h': round(random.uniform(1000, 10000), 2),
            'timestamp': datetime.now().isoformat(),
            'source': 'simulation',
        }

    async def _fetch_order_book_from_source(
        self,
        symbol: str,
        limit: int
    ) -> Optional[Dict]:
        """从数据源获取订单簿

        Args:
            symbol: 交易对
            limit: 深度限制

        Returns:
            订单簿字典
        """
        try:
            if self.active_data_source == 'simulation':
                return await self._generate_simulation_order_book(symbol, limit)
            else:
                logger.warning(f"未实现数据源: {self.active_data_source}")
                return None

        except Exception as e:
            logger.error(f"获取订单簿失败: {e}")
            return None

    async def _generate_simulation_order_book(
        self,
        symbol: str,
        limit: int
    ) -> Dict:
        """生成模拟订单簿

        Args:
            symbol: 交易对
            limit: 深度限制

        Returns:
            订单簿字典
        """
        import random

        # 获取当前价格
        price_data = await self._generate_simulation_price(symbol)
        current_price = price_data['price']

        # 生成买单
        bids = []
        for i in range(limit):
            price = current_price * (1 - 0.0001 * (i + 1))
            quantity = random.uniform(0.1, 10.0)
            bids.append({
                'price': round(price, 2),
                'quantity': round(quantity, 4),
                'total': round(price * quantity, 2),
            })

        # 生成卖单
        asks = []
        for i in range(limit):
            price = current_price * (1 + 0.0001 * (i + 1))
            quantity = random.uniform(0.1, 10.0)
            asks.append({
                'price': round(price, 2),
                'quantity': round(quantity, 4),
                'total': round(price * quantity, 2),
            })

        return {
            'symbol': symbol,
            'bids': bids,
            'asks': asks,
            'timestamp': datetime.now().isoformat(),
            'source': 'simulation',
        }

    async def _fetch_trade_history_from_source(
        self,
        symbol: str,
        limit: int
    ) -> Optional[List[Dict]]:
        """从数据源获取交易历史

        Args:
            symbol: 交易对
            limit: 数量限制

        Returns:
            交易历史列表
        """
        try:
            if self.active_data_source == 'simulation':
                return await self._generate_simulation_trades(symbol, limit)
            else:
                logger.warning(f"未实现数据源: {self.active_data_source}")
                return None

        except Exception as e:
            logger.error(f"获取交易历史失败: {e}")
            return None

    async def _generate_simulation_trades(
        self,
        symbol: str,
        limit: int
    ) -> List[Dict]:
        """生成模拟交易历史

        Args:
            symbol: 交易对
            limit: 数量限制

        Returns:
            交易历史列表
        """
        import random

        # 获取当前价格
        price_data = await self._generate_simulation_price(symbol)
        current_price = price_data['price']

        trades = []
        for i in range(limit):
            # 生成随机时间戳（倒序）
            trade_time = datetime.now() - timedelta(seconds=i * random.uniform(1, 10))

            # 随机买卖方向
            side = random.choice(['buy', 'sell'])

            # 生成价格和数量
            price = current_price * random.uniform(0.999, 1.001)
            quantity = random.uniform(0.01, 5.0)

            trades.append({
                'id': f"TRADE_{i}",
                'price': round(price, 2),
                'quantity': round(quantity, 4),
                'total': round(price * quantity, 2),
                'side': side,
                'timestamp': trade_time.isoformat(),
                'source': 'simulation',
            })

        return trades

    def _validate_price_data(self, data: Dict) -> DataQuality:
        """验证价格数据

        Args:
            data: 价格数据

        Returns:
            数据质量
        """
        try:
            # 检查必要字段
            required_fields = ['symbol', 'price', 'bid', 'ask']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"价格数据缺少字段: {field}")
                    return DataQuality.INVALID

            price = data.get('price', 0)
            bid = data.get('bid', 0)
            ask = data.get('ask', 0)

            # 检查价格合理性
            if price <= 0 or bid <= 0 or ask <= 0:
                logger.warning(f"价格数据不合理: price={price}, bid={bid}, ask={ask}")
                return DataQuality.INVALID

            # 检查bid-ask关系
            if bid >= ask:
                logger.warning(f"bid >= ask: bid={bid}, ask={ask}")
                return DataQuality.POOR

            # 计算spread
            spread_percent = ((ask - bid) / bid) * 100
            if spread_percent > 1.0:  # spread > 1%
                return DataQuality.POOR
            elif spread_percent > 0.5:  # spread > 0.5%
                return DataQuality.FAIR
            else:
                return DataQuality.GOOD

        except Exception as e:
            logger.error(f"验证价格数据失败: {e}")
            return DataQuality.INVALID

    def _validate_order_book_data(self, data: Dict) -> DataQuality:
        """验证订单簿数据

        Args:
            data: 订单簿数据

        Returns:
            数据质量
        """
        try:
            # 检查必要字段
            required_fields = ['symbol', 'bids', 'asks']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"订单簿数据缺少字段: {field}")
                    return DataQuality.INVALID

            bids = data.get('bids', [])
            asks = data.get('asks', [])

            # 检查深度
            min_depth = self.quality_thresholds.get('min_order_book_depth', 10)
            if len(bids) < min_depth or len(asks) < min_depth:
                logger.warning(f"订单簿深度不足: bids={len(bids)}, asks={len(asks)}")
                return DataQuality.POOR

            # 检查价格排序
            # bids应该是降序（价格从高到低）
            for i in range(len(bids) - 1):
                if bids[i]['price'] < bids[i + 1]['price']:
                    logger.warning("bids价格排序错误")
                    return DataQuality.FAIR

            # asks应该是升序（价格从低到高）
            for i in range(len(asks) - 1):
                if asks[i]['price'] > asks[i + 1]['price']:
                    logger.warning("asks价格排序错误")
                    return DataQuality.FAIR

            return DataQuality.GOOD

        except Exception as e:
            logger.error(f"验证订单簿数据失败: {e}")
            return DataQuality.INVALID

    def _assess_price_quality(self, price_data: Dict) -> Dict[str, Any]:
        """评估价格质量

        Args:
            price_data: 价格数据字典

        Returns:
            质量评估字典
        """
        if not price_data:
            return {
                'quality': DataQuality.INVALID.value,
                'reason': 'No price data',
            }

        # 计算质量指标
        qualities = []
        for symbol, data in price_data.items():
            quality = self._validate_price_data(data)
            qualities.append(quality)

        # 统计质量分布
        quality_counts = {}
        for quality in qualities:
            quality_name = quality.value
            quality_counts[quality_name] = quality_counts.get(quality_name, 0) + 1

        # 确定整体质量
        if DataQuality.INVALID in qualities:
            overall_quality = DataQuality.INVALID.value
        elif DataQuality.POOR in qualities:
            overall_quality = DataQuality.POOR.value
        elif DataQuality.FAIR in qualities:
            overall_quality = DataQuality.FAIR.value
        elif DataQuality.GOOD in qualities:
            overall_quality = DataQuality.GOOD.value
        else:
            overall_quality = DataQuality.EXCELLENT.value

        return {
            'quality': overall_quality,
            'distribution': quality_counts,
            'total_symbols': len(qualities),
        }

    def _assess_order_book_quality(self, order_book_data: Dict) -> Dict[str, Any]:
        """评估订单簿质量

        Args:
            order_book_data: 订单簿数据字典

        Returns:
            质量评估字典
        """
        if not order_book_data:
            return {
                'quality': DataQuality.INVALID.value,
                'reason': 'No order book data',
            }

        # 计算质量指标
        qualities = []
        for symbol, data in order_book_data.items():
            quality = self._validate_order_book_data(data)
            qualities.append(quality)

        # 统计质量分布
        quality_counts = {}
        for quality in qualities:
            quality_name = quality.value
            quality_counts[quality_name] = quality_counts.get(quality_name, 0) + 1

        # 确定整体质量
        if DataQuality.INVALID in qualities:
            overall_quality = DataQuality.INVALID.value
        elif DataQuality.POOR in qualities:
            overall_quality = DataQuality.POOR.value
        elif DataQuality.FAIR in qualities:
            overall_quality = DataQuality.FAIR.value
        elif DataQuality.GOOD in qualities:
            overall_quality = DataQuality.GOOD.value
        else:
            overall_quality = DataQuality.EXCELLENT.value

        return {
            'quality': overall_quality,
            'distribution': quality_counts,
            'total_symbols': len(qualities),
        }

    def _update_data_quality_stats(
        self,
        symbol: str,
        data_type: str,
        quality: DataQuality
    ) -> None:
        """更新数据质量统计

        Args:
            symbol: 交易对
            data_type: 数据类型
            quality: 数据质量
        """
        key = f"{symbol}_{data_type}"
        if key not in self.data_quality_stats:
            self.data_quality_stats[key] = {
                'total': 0,
                'excellent': 0,
                'good': 0,
                'fair': 0,
                'poor': 0,
                'invalid': 0,
            }

        stats = self.data_quality_stats[key]
        stats['total'] += 1
        stats[quality.value] += 1

    def _get_from_price_cache(self, symbol: str) -> Optional[Dict]:
        """从价格缓存获取

        Args:
            symbol: 交易对

        Returns:
            缓存的数据，不存在返回None
        """
        cached_data = self.price_cache.get(symbol)
        if not cached_data:
            return None

        # 检查是否过期
        try:
            timestamp_str = cached_data.get('timestamp', '')
            if not timestamp_str:
                # 无时间戳，视为过期
                del self.price_cache[symbol]
                return None

            cached_time = datetime.fromisoformat(timestamp_str)
            if datetime.now() - cached_time > timedelta(seconds=self.price_cache_ttl):
                # 缓存过期
                del self.price_cache[symbol]
                return None

        except (ValueError, TypeError, OSError) as e:
            # 时间戳解析失败，视为过期
            logger.warning(f"缓存时间戳解析失败: {symbol}, {e}")
            del self.price_cache[symbol]
            return None

        return cached_data

    def _add_to_price_cache(self, symbol: str, data: Dict) -> None:
        """添加到价格缓存

        Args:
            symbol: 交易对
            data: 价格数据
        """
        self.price_cache[symbol] = data

    def _get_from_order_book_cache(self, symbol: str) -> Optional[Dict]:
        """从订单簿缓存获取

        Args:
            symbol: 交易对

        Returns:
            缓存的数据，不存在返回None
        """
        cached_data = self.order_book_cache.get(symbol)
        if not cached_data:
            return None

        # 检查是否过期
        try:
            timestamp_str = cached_data.get('timestamp', '')
            if not timestamp_str:
                del self.order_book_cache[symbol]
                return None

            cached_time = datetime.fromisoformat(timestamp_str)
            if datetime.now() - cached_time > timedelta(seconds=self.order_book_cache_ttl):
                del self.order_book_cache[symbol]
                return None

        except (ValueError, TypeError, OSError) as e:
            logger.warning(f"订单簿缓存时间戳解析失败: {symbol}, {e}")
            del self.order_book_cache[symbol]
            return None

        return cached_data

    def _add_to_order_book_cache(self, symbol: str, data: Dict) -> None:
        """添加到订单簿缓存

        Args:
            symbol: 交易对
            data: 订单簿数据
        """
        self.order_book_cache[symbol] = data

    def _flatten_dict(self, d: Dict, parent_key: str = '') -> Dict:
        """扁平化字典

        Args:
            d: 字典
            parent_key: 父键

        Returns:
            扁平化字典
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}_{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

    # ========== 实时WebSocket支持 (V16.7新增) ==========

    def register_realtime_callback(self, callback: Callable[[str, Dict], None]) -> None:
        """注册实时价格回调

        Args:
            callback: (symbol, price_data) -> None 回调函数
        """
        self._realtime_price_callbacks.append(callback)
        logger.info(f"注册实时价格回调: {callback.__name__}")

    async def subscribe_realtime_prices(
        self, exchange: str, symbols: List[str]
    ) -> bool:
        """订阅实时价格

        Args:
            exchange: 交易所名称 (如 'binance', 'okx')
            symbols: 交易对列表

        Returns:
            是否成功
        """
        if not self.enable_realtime:
            logger.warning("实时模式未启用，请在配置中设置 enable_realtime: true")
            return False

        # 记录订阅
        self._ws_subscriptions[exchange].update(symbols)
        logger.info(f"订阅实时价格: {exchange} -> {symbols}")

        # TODO: 实现真实的WebSocket连接
        # 示例: 使用ccxt.pro或原生WebSocket连接交易所
        # if exchange == 'binance':
        #     await self._connect_binance_ws(symbols)
        # elif exchange == 'okx':
        #     await self._connect_okx_ws(symbols)

        logger.info(f"实时价格订阅已记录 (模拟模式): {exchange}")
        return True

    async def unsubscribe_realtime_prices(
        self, exchange: str, symbols: List[str]
    ) -> bool:
        """取消订阅实时价格

        Args:
            exchange: 交易所名称
            symbols: 交易对列表

        Returns:
            是否成功
        """
        if exchange in self._ws_subscriptions:
            self._ws_subscriptions[exchange] -= set(symbols)
            if not self._ws_subscriptions[exchange]:
                del self._ws_subscriptions[exchange]
                # TODO: 关闭WebSocket连接

        logger.info(f"取消订阅实时价格: {exchange} -> {symbols}")
        return True

    def _handle_realtime_price_update(self, symbol: str, price_data: Dict) -> None:
        """处理实时价格更新

        Args:
            symbol: 交易对
            price_data: 价格数据
        """
        # 更新缓存
        self._add_to_price_cache(symbol, price_data)

        # 触发回调
        for callback in self._realtime_price_callbacks:
            try:
                callback(symbol, price_data)
            except Exception as e:
                logger.error(f"实时价格回调执行失败: {e}")

    async def connect_realtime_ws(self, exchange: str) -> bool:
        """连接实时WebSocket

        Args:
            exchange: 交易所名称

        Returns:
            是否成功
        """
        if not self.enable_realtime:
            logger.warning("实时模式未启用")
            return False

        # TODO: 实现真实的WebSocket连接
        # 目前返回成功但使用模拟数据
        logger.info(f"实时WebSocket连接已建立 (模拟): {exchange}")
        return True

    async def disconnect_realtime_ws(self, exchange: str) -> bool:
        """断开实时WebSocket

        Args:
            exchange: 交易所名称

        Returns:
            是否成功
        """
        if exchange in self._ws_connections:
            # TODO: 关闭WebSocket连接
            del self._ws_connections[exchange]

        logger.info(f"实时WebSocket已断开: {exchange}")
        return True

    def is_realtime_connected(self, exchange: str) -> bool:
        """检查是否已连接实时WebSocket

        Args:
            exchange: 交易所名称

        Returns:
            是否已连接
        """
        return exchange in self._ws_connections

    # ========== 统计信息 ==========

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return {
            **self.stats,
            'cache_size': {
                'price': len(self.price_cache),
                'order_book': len(self.order_book_cache),
                'trade_history': sum(
                    len(trades) for trades in self.trade_history_cache.values()
                ),
            },
            'data_sources': list(self.data_sources.keys()),
            'active_data_source': self.active_data_source,
        }


# ========== 全局市场数据管理器实例 ==========

_market_data_manager_instance: Optional[MarketDataManager] = None


def get_market_data_manager() -> MarketDataManager:
    """获取市场数据管理器单例

    Returns:
        市场数据管理器实例
    """
    global _market_data_manager_instance
    if _market_data_manager_instance is None:
        _market_data_manager_instance = MarketDataManager()
    return _market_data_manager_instance
