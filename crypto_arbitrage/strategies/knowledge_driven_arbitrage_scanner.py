"""知识驱动套利扫描器 V16.2

桥接数据采集、Memo0知识库和低风险套利引擎，实现完整的知识驱动套利决策链。

核心能力:
1. 跨交易所价差扫描 — 检测Binance/Okex/Bybit等交易所间的实时价差
2. 三角套利机会发现 — 同一交易所内交易对间的价格不一致
3. 知识验证 — 用历史知识验证机会可靠性，过滤假信号
4. 费用模型 — 精确计算交易手续费、滑点、提币费用后的真实利润
5. 执行反馈 — 每次扫描结果自动存入知识库，持续学习

架构位置:
    RealTimeCollector → KnowledgeDrivenArbitrageScanner → LowRiskArbitrageEngine
                              ↕
                         Memo0 Knowledge Base

创建时间：2026-05-05
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ArbitrageType(Enum):
    """套利类型"""
    CROSS_EXCHANGE = "cross_exchange"      # 跨交易所套利
    TRIANGULAR = "triangular"              # 三角套利
    FUNDING_RATE = "funding_rate"          # 资金费率套利
    STATISTICAL = "statistical"            # 统计套利（均值回归）


class OpportunityStatus(Enum):
    """机会状态"""
    DETECTED = "detected"                  # 检测到
    VALIDATED = "validated"                # 已验证
    KNOWLEDGE_CONFIRMED = "knowledge_confirmed"  # 知识确认
    REJECTED = "rejected"                  # 已拒绝
    EXPIRED = "expired"                    # 已过期


@dataclass
class ArbitrageOpportunity:
    """套利机会"""
    opportunity_id: str
    arbitrage_type: ArbitrageType
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread_pct: float                          # 原始价差百分比
    net_profit_pct: float                      # 扣除费用后的净利润百分比
    volume_available: float                    # 可用交易量
    confidence_score: float                    # 置信度 (0-1)
    status: OpportunityStatus = OpportunityStatus.DETECTED
    knowledge_factors: List[str] = field(default_factory=list)
    fee_breakdown: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    detected_at: float = 0.0
    expires_at: float = 0.0

    def is_profitable(self, min_profit_pct: float = 0.05) -> bool:
        """是否盈利（扣除所有费用后）"""
        return self.net_profit_pct >= min_profit_pct


@dataclass
class FeeModel:
    """费用模型"""
    # 交易所手续费率
    maker_fee: float = 0.001          # Maker手续费 0.1%
    taker_fee: float = 0.001          # Taker手续费 0.1%
    # 提币费用
    withdrawal_fee_pct: float = 0.0005  # 提币费率 0.05%
    withdrawal_fee_fixed: float = 0.0    # 固定提币费
    # 滑点估算
    slippage_pct: float = 0.0002      # 滑点 0.02%
    # 资金费率（仅资金费率套利）
    funding_rate: float = 0.0

    def calculate_net_spread(self, gross_spread_pct: float) -> Tuple[float, Dict[str, float]]:
        """计算扣除所有费用后的净利润

        Args:
            gross_spread_pct: 原始价差百分比

        Returns:
            (净利润百分比, 费用明细)
        """
        fees = {
            "buy_taker_fee": self.taker_fee * 100,
            "sell_taker_fee": self.taker_fee * 100,
            "slippage_total": self.slippage_pct * 2 * 100,
            "withdrawal_fee": self.withdrawal_fee_pct * 100,
        }

        total_fee_pct = (
            self.taker_fee           # 买入手续费
            + self.taker_fee         # 卖出手续费
            + self.slippage_pct * 2  # 买卖滑点
            + self.withdrawal_fee_pct  # 提币费用
        )

        net_profit = gross_spread_pct - total_fee_pct * 100

        return net_profit, fees


@dataclass
class ScanResult:
    """扫描结果"""
    scan_id: str
    timestamp: float
    opportunities_found: int
    profitable_opportunities: int
    best_opportunity: Optional[ArbitrageOpportunity]
    all_opportunities: List[ArbitrageOpportunity]
    knowledge_queries: int
    scan_duration_ms: float
    market_snapshot: Dict[str, Any] = field(default_factory=dict)


class KnowledgeDrivenArbitrageScanner:
    """知识驱动套利扫描器 V16.2

    将数据采集、知识库查询和套利引擎桥接起来，
    实现从数据到决策的完整自动化链路。
    """

    # 支持的交易对
    DEFAULT_SYMBOLS = [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT",
        "XRP/USDT", "ADA/USDT", "DOGE/USDT", "AVAX/USDT"
    ]

    # 支持的交易所
    DEFAULT_EXCHANGES = ["binance", "okex", "bybit", "huobi", "coinbase"]

    # 三角套利路径
    TRIANGULAR_PATHS = [
        ("BTC/USDT", "ETH/BTC", "ETH/USDT"),
        ("BTC/USDT", "SOL/BTC", "SOL/USDT"),
        ("ETH/USDT", "SOL/ETH", "SOL/USDT"),
        ("BNB/USDT", "ETH/BNB", "ETH/USDT"),
        ("BNB/USDT", "BTC/BNB", "BTC/USDT"),
    ]

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        fee_model: Optional[FeeModel] = None,
        knowledge_storage=None
    ):
        """初始化知识驱动套利扫描器

        Args:
            config: 配置字典
            fee_model: 费用模型
            knowledge_storage: 知识存储实例（Memo0或Mock）
        """
        self.config = config or {}
        self.fee_model = fee_model or FeeModel()
        self._knowledge = knowledge_storage

        # 配置参数
        self.min_profit_pct = self.config.get("min_profit_pct", 0.05)
        self.min_confidence = self.config.get("min_confidence", 0.6)
        self.max_opportunities = self.config.get("max_opportunities", 50)
        self.opportunity_ttl_sec = self.config.get("opportunity_ttl_sec", 30.0)

        # 扫描统计
        self.total_scans = 0
        self.total_opportunities_found = 0
        self.total_profitable_found = 0
        self.knowledge_hits = 0

        # 模拟市场价格数据（用于演示和测试）
        self._simulated_prices: Dict[str, Dict[str, float]] = {}
        self._init_simulated_prices()

        logger.info("知识驱动套利扫描器 V16.2 初始化完成")

    def _init_simulated_prices(self) -> None:
        """初始化模拟价格数据

        在没有实时数据源时使用模拟数据。
        生产环境应替换为真实交易所API数据。
        """
        import random

        base_prices = {
            "BTC/USDT": 94500.0,
            "ETH/USDT": 3780.0,
            "SOL/USDT": 175.0,
            "BNB/USDT": 625.0,
            "XRP/USDT": 2.42,
            "ADA/USDT": 0.75,
            "DOGE/USDT": 0.185,
            "AVAX/USDT": 38.5,
        }

        for symbol, base_price in base_prices.items():
            self._simulated_prices[symbol] = {}
            for exchange in self.DEFAULT_EXCHANGES:
                # 每个交易所有轻微价格差异 (0-0.3%)
                variation = random.uniform(-0.003, 0.003)
                self._simulated_prices[symbol][exchange] = base_price * (1 + variation)

        # 计算交叉汇率
        for path in self.TRIANGULAR_PATHS:
            sym_a, sym_b, sym_c = path
            for exchange in self.DEFAULT_EXCHANGES:
                if sym_a in self._simulated_prices and sym_c in self._simulated_prices:
                    price_a = self._simulated_prices[sym_a].get(exchange, 0)
                    price_c = self._simulated_prices[sym_c].get(exchange, 0)
                    if price_a > 0 and price_c > 0:
                        # 交叉汇率: sym_b = price_c / price_a
                        self._simulated_prices.setdefault(sym_b, {})[exchange] = price_c / price_a

    def _get_knowledge_storage(self):
        """获取知识存储实例"""
        if self._knowledge is not None:
            return self._knowledge

        # 延迟初始化
        try:
            from storage.mem0_storage import get_mem0_storage
            self._knowledge = get_mem0_storage()
        except Exception:
            pass

        return self._knowledge

    def scan_cross_exchange(
        self,
        symbols: Optional[List[str]] = None,
        exchanges: Optional[List[str]] = None
    ) -> List[ArbitrageOpportunity]:
        """扫描跨交易所套利机会

        检测不同交易所之间的价格差异。

        Args:
            symbols: 交易对列表
            exchanges: 交易所列表

        Returns:
            套利机会列表
        """
        symbols = symbols or self.DEFAULT_SYMBOLS
        exchanges = exchanges or self.DEFAULT_EXCHANGES
        opportunities = []

        for symbol in symbols:
            prices = self._simulated_prices.get(symbol, {})
            if len(prices) < 2:
                continue

            exchange_prices = [(ex, prices.get(ex, 0)) for ex in exchanges if ex in prices]
            exchange_prices = [(ex, p) for ex, p in exchange_prices if p > 0]

            if len(exchange_prices) < 2:
                continue

            # 找到最低价和最高价
            exchange_prices.sort(key=lambda x: x[1])
            cheapest_exchange, lowest_price = exchange_prices[0]
            expensive_exchange, highest_price = exchange_prices[-1]

            # 计算价差
            spread_pct = (highest_price - lowest_price) / lowest_price * 100

            # 计算净利润
            net_profit, fee_breakdown = self.fee_model.calculate_net_spread(spread_pct)

            if net_profit > 0:
                opportunity = ArbitrageOpportunity(
                    opportunity_id=f"ce_{symbol.replace('/', '')}_{int(time.time() * 1000)}",
                    arbitrage_type=ArbitrageType.CROSS_EXCHANGE,
                    symbol=symbol,
                    buy_exchange=cheapest_exchange,
                    sell_exchange=expensive_exchange,
                    buy_price=lowest_price,
                    sell_price=highest_price,
                    spread_pct=spread_pct,
                    net_profit_pct=net_profit,
                    volume_available=1000.0,  # 模拟值
                    confidence_score=0.7,
                    fee_breakdown=fee_breakdown,
                    detected_at=time.time(),
                    expires_at=time.time() + self.opportunity_ttl_sec
                )
                opportunities.append(opportunity)

        return opportunities

    def scan_triangular(
        self,
        exchange: str = "binance"
    ) -> List[ArbitrageOpportunity]:
        """扫描三角套利机会

        检测同一交易所内交易对间的价格不一致。

        Args:
            exchange: 交易所名称

        Returns:
            套利机会列表
        """
        opportunities = []

        for path in self.TRIANGULAR_PATHS:
            sym_a, sym_b, sym_c = path

            prices = self._simulated_prices
            price_a = prices.get(sym_a, {}).get(exchange, 0)
            price_b = prices.get(sym_b, {}).get(exchange, 0)
            price_c = prices.get(sym_c, {}).get(exchange, 0)

            if price_a <= 0 or price_b <= 0 or price_c <= 0:
                continue

            # 正向路径: USDT -> A -> B -> USDT
            # 1 USDT -> 1/price_a A -> (1/price_a)/price_b B -> ((1/price_a)/price_b)*price_c USDT
            # forward_result = price_c / (price_a * price_b)
            forward_result = price_c / (price_a * price_b)

            # 反向路径: USDT -> B -> A -> USDT
            # 1 USDT -> 1/price_c B -> (1/price_c)*price_b A -> ((1/price_c)*price_b)*price_a USDT
            # reverse_result = (price_b * price_a) / price_c
            reverse_result = (price_b * price_a) / price_c

            # 取最优路径
            best_result = max(forward_result, reverse_result)
            if best_result <= 1.0:
                continue

            spread_pct = (best_result - 1.0) * 100

            # 三角套利需要3笔交易
            net_profit, fee_breakdown = self.fee_model.calculate_net_spread(spread_pct)
            # 额外扣除一笔交易费用
            extra_fee = self.fee_model.taker_fee * 100
            net_profit -= extra_fee
            fee_breakdown["extra_leg_fee"] = extra_fee

            if net_profit > 0:
                direction = "forward" if forward_result > reverse_result else "reverse"
                opportunity = ArbitrageOpportunity(
                    opportunity_id=f"tri_{sym_a.replace('/', '')}_{int(time.time() * 1000)}",
                    arbitrage_type=ArbitrageType.TRIANGULAR,
                    symbol=f"{sym_a}-{sym_b}-{sym_c}",
                    buy_exchange=exchange,
                    sell_exchange=exchange,
                    buy_price=price_a,
                    sell_price=price_c,
                    spread_pct=spread_pct,
                    net_profit_pct=net_profit,
                    volume_available=500.0,
                    confidence_score=0.6,
                    fee_breakdown=fee_breakdown,
                    metadata={"path": path, "direction": direction},
                    detected_at=time.time(),
                    expires_at=time.time() + self.opportunity_ttl_sec
                )
                opportunities.append(opportunity)

        return opportunities

    def validate_with_knowledge(
        self,
        opportunity: ArbitrageOpportunity
    ) -> ArbitrageOpportunity:
        """用知识库验证套利机会

        使用多维度查询策略搜索历史知识，评估机会可靠性。

        Args:
            opportunity: 套利机会

        Returns:
            更新后的套利机会
        """
        knowledge = self._get_knowledge_storage()
        if not knowledge:
            opportunity.status = OpportunityStatus.VALIDATED
            opportunity.knowledge_factors.append("no_knowledge_storage")
            return opportunity

        # 多维度查询策略（V16.3改进：提升知识命中率）
        queries = self._build_knowledge_queries(opportunity)
        all_results = []
        seen_ids = set()

        for query in queries:
            try:
                results = knowledge.search_memories(query, top_k=5)
                for r in results:
                    rid = r.get("id", id(r))
                    if rid not in seen_ids:
                        seen_ids.add(rid)
                        all_results.append(r)
            except Exception as e:
                logger.warning(f"知识查询失败: {e}")

        # 也尝试带分类的搜索
        try:
            cat_results = knowledge.search_knowledge(
                query=opportunity.symbol.replace("/", ""),
                category="execution_result",
                top_k=5
            )
            for r in cat_results:
                rid = r.get("content", "")[:50]
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    all_results.append({
                        "memory": r.get("content", ""),
                        "score": r.get("score", 0.3)
                    })
        except (AttributeError, Exception):
            pass  # search_knowledge 可能不可用

        self.knowledge_hits += len(all_results)

        # 分析历史知识
        positive_count = 0
        negative_count = 0
        for result in all_results:
            memory = result.get("memory", "").lower()
            score = result.get("score", 0)

            # 正面因素
            if any(kw in memory for kw in ["profitable", "successful", "success", "profit", "expected"]):
                positive_count += 1
                opportunity.knowledge_factors.append(f"history_profitable (score={score:.2f})")

            # 负面因素
            if any(kw in memory for kw in ["loss", "failed", "risky", "avoid", "rejected"]):
                negative_count += 1
                opportunity.knowledge_factors.append(f"history_risky (score={score:.2f})")

        # 更新置信度
        if all_results:
            knowledge_boost = (positive_count - negative_count * 2) / max(len(all_results), 1)
            opportunity.confidence_score = min(1.0, max(0.0,
                opportunity.confidence_score + knowledge_boost * 0.3))

        # 更新状态
        if opportunity.confidence_score >= self.min_confidence and opportunity.is_profitable(self.min_profit_pct):
            opportunity.status = OpportunityStatus.KNOWLEDGE_CONFIRMED
        elif opportunity.is_profitable(self.min_profit_pct):
            opportunity.status = OpportunityStatus.VALIDATED
        else:
            opportunity.status = OpportunityStatus.REJECTED

        return opportunity

    def _build_knowledge_queries(self, opportunity: ArbitrageOpportunity) -> List[str]:
        """构建多维度知识查询（V16.3改进）

        生成多个查询以最大化知识命中率。

        Args:
            opportunity: 套利机会

        Returns:
            查询字符串列表
        """
        queries = []

        # 查询1: 精确类型+币种
        queries.append(f"{opportunity.arbitrage_type.value} {opportunity.symbol}")

        # 查询2: 仅币种（匹配更多历史）
        queries.append(opportunity.symbol)

        # 查询3: 交易所对
        if opportunity.buy_exchange and opportunity.sell_exchange:
            queries.append(f"{opportunity.buy_exchange} {opportunity.sell_exchange}")

        # 查询4: 执行结果关键词
        queries.append("arbitrage_execution")

        # 查询5: 扫描结果关键词
        queries.append("arbitrage_scan")

        return queries

    def record_to_knowledge(
        self,
        opportunity: ArbitrageOpportunity,
        action_taken: str = "scanned"
    ) -> bool:
        """记录套利机会到知识库

        Args:
            opportunity: 套利机会
            action_taken: 执行动作

        Returns:
            是否成功
        """
        knowledge = self._get_knowledge_storage()
        if not knowledge:
            return False

        content = (
            f"[arbitrage_scan] {opportunity.arbitrage_type.value} | "
            f"{opportunity.symbol} | "
            f"buy={opportunity.buy_exchange}@{opportunity.buy_price:.6f} | "
            f"sell={opportunity.sell_exchange}@{opportunity.sell_price:.6f} | "
            f"spread={opportunity.spread_pct:.4f}% | "
            f"net={opportunity.net_profit_pct:.4f}% | "
            f"confidence={opportunity.confidence_score:.2f} | "
            f"status={opportunity.status.value} | "
            f"action={action_taken}"
        )

        try:
            knowledge.add_memory(content)
            return True
        except Exception as e:
            logger.warning(f"记录知识失败: {e}")
            return False

    def full_scan(self) -> ScanResult:
        """执行完整扫描

        包含跨交易所扫描 + 三角套利扫描 + 知识验证。

        Returns:
            扫描结果
        """
        start_time = time.time()
        scan_id = f"scan_{int(start_time * 1000)}"

        logger.info(f"开始知识驱动套利扫描: {scan_id}")

        # 1. 跨交易所扫描
        cross_exchange_opps = self.scan_cross_exchange()

        # 2. 三角套利扫描
        triangular_opps = self.scan_triangular()

        # 3. 合并所有机会
        all_opportunities = cross_exchange_opps + triangular_opps

        # 4. 知识验证
        validated_opportunities = []
        for opp in all_opportunities:
            validated = self.validate_with_knowledge(opp)
            if validated.status in [OpportunityStatus.VALIDATED, OpportunityStatus.KNOWLEDGE_CONFIRMED]:
                validated_opportunities.append(validated)

            # 记录到知识库
            self.record_to_knowledge(validated)

        # 5. 按净利润排序
        validated_opportunities.sort(key=lambda x: x.net_profit_pct, reverse=True)

        # 6. 取前N个
        top_opportunities = validated_opportunities[:self.max_opportunities]

        # 7. 统计
        scan_duration_ms = (time.time() - start_time) * 1000
        profitable_count = len([o for o in top_opportunities if o.is_profitable(self.min_profit_pct)])

        self.total_scans += 1
        self.total_opportunities_found += len(all_opportunities)
        self.total_profitable_found += profitable_count

        result = ScanResult(
            scan_id=scan_id,
            timestamp=start_time,
            opportunities_found=len(all_opportunities),
            profitable_opportunities=profitable_count,
            best_opportunity=top_opportunities[0] if top_opportunities else None,
            all_opportunities=top_opportunities,
            knowledge_queries=self.knowledge_hits,
            scan_duration_ms=scan_duration_ms,
            market_snapshot={"exchanges": len(self.DEFAULT_EXCHANGES), "symbols": len(self.DEFAULT_SYMBOLS)}
        )

        logger.info(
            f"扫描完成: {scan_id}, "
            f"发现{len(all_opportunities)}个机会, "
            f"{profitable_count}个盈利, "
            f"耗时{scan_duration_ms:.1f}ms"
        )

        return result

    def get_scan_statistics(self) -> Dict[str, Any]:
        """获取扫描统计

        Returns:
            统计数据字典
        """
        return {
            "total_scans": self.total_scans,
            "total_opportunities_found": self.total_opportunities_found,
            "total_profitable_found": self.total_profitable_found,
            "knowledge_hits": self.knowledge_hits,
            "avg_opportunities_per_scan": (
                self.total_opportunities_found / self.total_scans
                if self.total_scans > 0 else 0
            ),
            "min_profit_threshold": self.min_profit_pct,
            "fee_model": {
                "maker_fee": self.fee_model.maker_fee,
                "taker_fee": self.fee_model.taker_fee,
                "slippage_pct": self.fee_model.slippage_pct,
            }
        }


# 全局实例
_scanner: Optional[KnowledgeDrivenArbitrageScanner] = None


def get_arbitrage_scanner(
    config: Optional[Dict[str, Any]] = None
) -> KnowledgeDrivenArbitrageScanner:
    """获取全局套利扫描器实例

    Args:
        config: 配置字典

    Returns:
        套利扫描器实例
    """
    global _scanner
    if _scanner is None:
        _scanner = KnowledgeDrivenArbitrageScanner(config)
    return _scanner
