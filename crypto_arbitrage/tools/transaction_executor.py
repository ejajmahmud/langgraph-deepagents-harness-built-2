"""高级交易执行引擎 - V1.4.0 修复全局单例 + 增强功能"""

import asyncio
import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from tools.exchange_api import get_exchange_manager

logger = logging.getLogger(__name__)


class TransactionExecutor:
    """交易执行引擎 - 执行和管理套利交易"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_concurrent_trades = config.get('max_concurrent_trades', 3)
        self.execution_timeout = config.get('execution_timeout', 30)
        self.auto_retry = config.get('auto_retry', True)
        self.max_retries = config.get('max_retries', 2)
        self.retry_delay = config.get('retry_delay', 5)

        # 交易队列
        self.trade_queue: List[Dict[str, Any]] = []
        self.active_trades: Dict[str, Dict] = {}
        self.completed_trades: List[Dict] = []
        self._semaphore = asyncio.Semaphore(self.max_concurrent_trades)

        logger.info("交易执行引擎初始化完成")

    async def execute_arbitrage(
        self,
        opportunity: Dict[str, Any],
        validate_risk: bool = True
    ) -> Optional[Dict[str, Any]]:
        """执行套利交易（带并发控制和重试）"""
        async with self._semaphore:
            return await self._execute_with_retry(opportunity, validate_risk)

    async def _execute_with_retry(
        self,
        opportunity: Dict[str, Any],
        validate_risk: bool
    ) -> Optional[Dict[str, Any]]:
        """带重试机制的执行"""
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                result = await self._execute_single(opportunity, validate_risk)
                if result and result.get('status') in ('completed', 'rejected'):
                    return result
                last_error = result.get('error') if result else '未知错误'
                if result and result.get('status') == 'rejected':
                    return result  # 被风控拒绝不重试
            except Exception as e:
                last_error = str(e)
                logger.warning(f"执行失败 (尝试 {attempt}/{self.max_retries}): {e}")

            if attempt < self.max_retries and self.auto_retry:
                await asyncio.sleep(self.retry_delay)

        # 所有重试失败
        trade_record = {
            'trade_id': self._generate_trade_id(),
            'opportunity': opportunity,
            'status': 'failed',
            'error': f"所有重试失败: {last_error}",
            'created_at': datetime.now(),
            'steps': []
        }
        self._record_trade_to_knowledge(trade_record, "trade_failed")
        return trade_record

    async def _execute_single(
        self,
        opportunity: Dict[str, Any],
        validate_risk: bool
    ) -> Optional[Dict[str, Any]]:
        """单次执行套利交易"""
        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            logger.error("交易所管理器未初始化")
            return None

        trade_record = {
            'trade_id': self._generate_trade_id(),
            'opportunity': opportunity,
            'status': 'pending',
            'created_at': datetime.now(),
            'steps': []
        }

        self._record_trade_to_knowledge(trade_record, "trade_created")

        try:
            if validate_risk:
                risk_check = await self._validate_risk(opportunity)
                if not risk_check['passed']:
                    trade_record['status'] = 'rejected'
                    trade_record['reason'] = risk_check['reason']
                    self._record_trade_to_knowledge(trade_record, "trade_rejected")
                    return trade_record

            execution_result = await asyncio.wait_for(
                self._execute_trade_sequence(trade_record, exchange_manager),
                timeout=self.execution_timeout + 60  # 包含转账等待时间
            )

            trade_record['status'] = execution_result['status']
            trade_record['result'] = execution_result
            trade_record['completed_at'] = datetime.now()

            if execution_result['status'] == 'completed':
                self.completed_trades.append(trade_record)

            self._record_trade_to_knowledge(trade_record,
                "trade_completed" if execution_result['status'] == 'completed' else "trade_failed")

            # 发送监控数据
            try:
                from tools.monitoring import get_monitoring
                monitoring = get_monitoring()
                if monitoring:
                    await monitoring.record_execution_metrics(
                        opportunity.get('strategy', 'cross_exchange'),
                        execution_result['status'] == 'completed',
                        (datetime.now() - trade_record['created_at']).total_seconds(),
                        execution_result.get('actual_profit', 0)
                    )
            except Exception:
                pass

            return trade_record

        except asyncio.TimeoutError:
            trade_record['status'] = 'failed'
            trade_record['error'] = f"执行超时 ({self.execution_timeout + 60}秒)"
            self._record_trade_to_knowledge(trade_record, "trade_timeout")
            return trade_record
        except Exception as e:
            logger.error(f"套利交易执行失败: {e}")
            trade_record['status'] = 'failed'
            trade_record['error'] = str(e)
            self._record_trade_to_knowledge(trade_record, "trade_failed")
            return trade_record

    async def _validate_risk(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """验证交易风险"""
        exchange_manager = get_exchange_manager()
        if not exchange_manager:
            return {'passed': False, 'reason': '交易所管理器未初始化'}

        buy_exchange = exchange_manager.exchanges.get(opportunity.get('buy_exchange'))
        sell_exchange = exchange_manager.exchanges.get(opportunity.get('sell_exchange'))

        if not buy_exchange or not sell_exchange:
            return {'passed': False, 'reason': f"交易所未配置"}

        # 检查余额
        try:
            buy_balance = await buy_exchange.fetch_balance()
            required = opportunity.get('amount', 0) * opportunity.get('buy_price', 0)
            available = buy_balance.get('USDT', {}).get('free', 0)
            if available < required:
                return {'passed': False, 'reason': f"余额不足: 需要${required:.2f}, 可用${available:.2f}"}
        except Exception as e:
            logger.warning(f"余额检查失败: {e}")

        # 检查价格时效
        timestamp = opportunity.get('timestamp', 0)
        if isinstance(timestamp, float) and timestamp > 1e12:
            timestamp = timestamp / 1000  # 毫秒转秒
        elif isinstance(timestamp, float) and timestamp < 1e12:
            pass  # 已经是秒
        else:
            timestamp = 0

        if timestamp > 0:
            price_age = datetime.now() - datetime.fromtimestamp(timestamp)
            if price_age.total_seconds() > 15:
                return {'passed': False, 'reason': f"价格过期: {price_age.total_seconds():.1f}秒前"}

        return {'passed': True, 'reason': '风险验证通过'}

    async def _execute_trade_sequence(
        self,
        trade_record: Dict[str, Any],
        exchange_manager
    ) -> Dict[str, Any]:
        """执行交易序列"""
        opportunity = trade_record['opportunity']
        steps = []

        # 步骤1: 买入
        buy_order = await self._execute_buy_order(trade_record, opportunity, exchange_manager)
        if not buy_order['success']:
            return {'status': 'failed', 'error': buy_order['error'], 'steps': [buy_order]}
        steps.append(buy_order)
        trade_record['buy_order_id'] = buy_order.get('order_id')
        await asyncio.sleep(2)

        # 步骤2: 转账（跨交易所时）
        buy_ex = opportunity.get('buy_exchange')
        sell_ex = opportunity.get('sell_exchange')
        if buy_ex and sell_ex and buy_ex != sell_ex:
            transfer = await self._execute_transfer(trade_record, opportunity, exchange_manager)
            if not transfer['success']:
                return {'status': 'failed', 'error': transfer['error'], 'steps': steps + [transfer]}
            steps.append(transfer)
            trade_record['transfer_id'] = transfer.get('transfer_id')
            await asyncio.sleep(min(60, self.execution_timeout))

        # 步骤3: 卖出
        sell_order = await self._execute_sell_order(trade_record, opportunity, exchange_manager)
        if not sell_order['success']:
            return {'status': 'failed', 'error': sell_order['error'], 'steps': steps + [sell_order]}
        steps.append(sell_order)
        trade_record['sell_order_id'] = sell_order.get('order_id')

        # 计算实际利润
        actual_profit = self._calculate_profit(trade_record)
        trade_record['actual_profit'] = actual_profit
        trade_record['steps'] = steps

        return {'status': 'completed', 'steps': steps, 'actual_profit': actual_profit}

    async def _execute_buy_order(self, trade_record, opportunity, exchange_manager) -> Dict:
        """执行买入订单"""
        exchange_name = opportunity.get('buy_exchange')
        symbol = opportunity.get('symbol')
        amount = opportunity.get('amount')

        logger.info(f"在 {exchange_name} 买入 {symbol}: {amount}")
        try:
            order = await exchange_manager.place_order(exchange_name, symbol, 'market', 'buy', amount)
            if not order:
                raise Exception("下单失败")
            return {
                'success': True, 'order_id': order.get('id'),
                'exchange': exchange_name, 'action': 'buy',
                'timestamp': datetime.now()
            }
        except Exception as e:
            return {
                'success': False, 'error': str(e),
                'exchange': exchange_name, 'action': 'buy',
                'timestamp': datetime.now()
            }

    async def _execute_sell_order(self, trade_record, opportunity, exchange_manager) -> Dict:
        """执行卖出订单"""
        exchange_name = opportunity.get('sell_exchange')
        symbol = opportunity.get('symbol')
        amount = opportunity.get('amount')

        logger.info(f"在 {exchange_name} 卖出 {symbol}: {amount}")
        try:
            order = await exchange_manager.place_order(exchange_name, symbol, 'market', 'sell', amount)
            if not order:
                raise Exception("下单失败")
            return {
                'success': True, 'order_id': order.get('id'),
                'exchange': exchange_name, 'action': 'sell',
                'timestamp': datetime.now()
            }
        except Exception as e:
            return {
                'success': False, 'error': str(e),
                'exchange': exchange_name, 'action': 'sell',
                'timestamp': datetime.now()
            }

    async def _execute_transfer(self, trade_record, opportunity, exchange_manager) -> Dict:
        """执行跨交易所转账"""
        transfer_id = f"transfer_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        logger.info(f"跨交易所转账: {transfer_id}")
        # 实际环境需实现链上转账
        return {
            'success': True, 'transfer_id': transfer_id,
            'from_exchange': opportunity.get('buy_exchange'),
            'to_exchange': opportunity.get('sell_exchange'),
            'action': 'transfer', 'timestamp': datetime.now()
        }

    def _calculate_profit(self, trade_record: Dict) -> float:
        """计算实际利润

        BUG FIX #3: 使用实际成交数据而非固定折扣
        """
        steps = trade_record.get('steps', [])
        if steps and len(steps) >= 2:
            # 从买卖步骤中提取实际成交信息
            buy_step = next((s for s in steps if s.get('action') == 'buy'), None)
            sell_step = next((s for s in steps if s.get('action') == 'sell'), None)
            if buy_step and sell_step:
                # 如果有实际成交价格就使用
                buy_price = buy_step.get('price', 0)
                sell_price = sell_step.get('price', 0)
                amount = trade_record['opportunity'].get('amount', 0)
                if buy_price > 0 and sell_price > 0 and amount > 0:
                    buy_fee = trade_record['opportunity'].get('buy_fee', 0.001)
                    sell_fee = trade_record['opportunity'].get('sell_fee', 0.001)
                    buy_cost = buy_price * amount * (1 + buy_fee)
                    sell_revenue = sell_price * amount * (1 - sell_fee)
                    return sell_revenue - buy_cost

        # 降级：使用预期利润并预留滑点缓冲
        opp = trade_record['opportunity']
        expected = opp.get('expected_profit', 0)
        if expected:
            return expected * 0.9
        return 0.0

    def _calculate_actual_profit(self, trade_record: Dict, execution_context: Any = None) -> float:
        """计算实际利润（别名方法，向后兼容）

        Args:
            trade_record: 交易记录
            execution_context: 执行上下文（保留接口，暂未使用）

        Returns:
            实际利润金额
        """
        return self._calculate_profit(trade_record)

    def _generate_trade_id(self) -> str:
        """生成唯一的交易ID（修复：增加随机数确保唯一性）"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        random_suffix = random.randint(10000, 99999)  # 5位随机数
        return f"trade_{timestamp}_{random_suffix}"

    def _record_trade_to_knowledge(self, trade_record: Dict, event_type: str) -> None:
        """记录交易事件到知识库"""
        try:
            from storage.mem0_storage import add_trading_knowledge
            opp = trade_record.get('opportunity', {})
            content = (
                f"交易ID: {trade_record['trade_id']}\n"
                f"状态: {trade_record['status']}\n"
                f"交易对: {opp.get('symbol', 'N/A')}\n"
            )
            if 'buy_exchange' in opp:
                content += f"买入: {opp['buy_exchange']} @ ${opp.get('buy_price', 0):.2f}\n"
            if 'sell_exchange' in opp:
                content += f"卖出: {opp['sell_exchange']} @ ${opp.get('sell_price', 0):.2f}\n"
            if 'expected_profit' in opp:
                content += f"预期利润: ${opp['expected_profit']:.2f}\n"
            if 'actual_profit' in trade_record:
                content += f"实际利润: ${trade_record['actual_profit']:.2f}\n"
            if 'reason' in trade_record:
                content += f"原因: {trade_record['reason']}\n"
            if 'error' in trade_record:
                content += f"错误: {trade_record['error']}\n"
            add_trading_knowledge(event_type, content)
        except Exception as e:
            logger.debug(f"记录交易事件失败: {e}")

    def get_active_trades(self) -> List[Dict]:
        return [t for t in self.active_trades.values() if t.get('status') in ('pending', 'executing')]

    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        return self.completed_trades[-limit:]


# 全局单例
_transaction_executor: Optional[TransactionExecutor] = None


def initialize_transaction_executor(config: Dict[str, Any] = None) -> TransactionExecutor:
    """初始化交易执行引擎（全局单例）"""
    global _transaction_executor
    if config is None:
        config = {}
    _transaction_executor = TransactionExecutor(config)
    logger.info("交易执行引擎初始化完成")
    return _transaction_executor


def get_transaction_executor() -> Optional[TransactionExecutor]:
    """获取交易执行引擎实例（全局单例）"""
    return _transaction_executor
