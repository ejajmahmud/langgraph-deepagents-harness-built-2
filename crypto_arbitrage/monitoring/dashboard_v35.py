"""
V35.0 Dashboard 增强 - 实时监控仪表板

功能：
1. 实时数据面板 - 实时价格/持仓/订单
2. 性能指标卡 - PnL/胜率/最大回撤
3. 机会监控 - 套利机会流
4. 风险警报 - 风险事件通知
5. 可视化图表 - 性能图表

创建时间：2026-05-07 21:25
"""

import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


class DashboardMetrics:
    """仪表板指标"""

    def __init__(self, max_history: int = 1000):
        """初始化仪表板指标

        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history

        # 价格历史
        self.price_history: Dict[str, deque] = {}

        # PnL历史
        self.pnl_history: deque = deque(maxlen=max_history)

        # 持仓历史
        self.position_history: deque = deque(maxlen=max_history)

        # 订单历史
        self.order_history: deque = deque(maxlen=max_history)

        # 机会历史
        self.opportunity_history: deque = deque(maxlen=max_history)

    def add_price(self, symbol: str, price: float) -> None:
        """添加价格数据

        Args:
            symbol: 交易品种
            price: 价格
        """
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.max_history)

        self.price_history[symbol].append({
            "symbol": symbol,
            "price": price,
            "timestamp": time.time()
        })

    def add_pnl(self, pnl: float) -> None:
        """添加PnL数据

        Args:
            pnl: 盈亏
        """
        self.pnl_history.append({
            "pnl": pnl,
            "timestamp": time.time()
        })

    def add_position(self, position: Dict) -> None:
        """添加持仓数据

        Args:
            position: 持仓字典
        """
        self.position_history.append({
            **position,
            "timestamp": time.time()
        })

    def add_opportunity(self, opportunity: Dict) -> None:
        """添加机会数据

        Args:
            opportunity: 机会字典
        """
        self.opportunity_history.append({
            **opportunity,
            "timestamp": time.time()
        })

    def get_price_range(
        self,
        symbol: str,
        minutes: int = 60
    ) -> List[Dict]:
        """获取价格时间范围

        Args:
            symbol: 交易品种
            minutes: 分钟数

        Returns:
            价格历史列表
        """
        if symbol not in self.price_history:
            return []

        cutoff_time = time.time() - minutes * 60
        return [
            p for p in self.price_history[symbol]
            if p["timestamp"] >= cutoff_time
        ]


class DashboardDataProvider:
    """仪表板数据提供者

    为仪表板提供数据。
    """

    def __init__(self):
        """初始化数据提供者"""
        self.metrics = DashboardMetrics()
        self.alerts: List[Dict] = []
        self.alert_threshold = {
            "max_drawdown": 0.1,      # 10% 最大回撤
            "min_balance": 1000.0,     # 1000 最小余额
            "max_position_size": 0.5,  # 50% 最大持仓比例
            "max_slippage": 0.005,     # 0.5% 最大滑点
        }

    def add_ticker(self, symbol: str, price: float) -> None:
        """添加交易对价格

        Args:
            symbol: 交易对
            price: 价格
        """
        self.metrics.add_price(symbol, price)

    def add_order(self, order: Dict) -> None:
        """添加订单

        Args:
            order: 订单字典
        """
        self.metrics.order_history.append(order)
        self._check_order_alerts(order)

    def add_position(self, position: Dict) -> None:
        """添加持仓

        Args:
            position: 持仓字典
        """
        self.metrics.add_position(position)
        self._check_position_alerts(position)

    def _check_order_alerts(self, order: Dict) -> None:
        """检查订单警报

        Args:
            order: 订单字典
        """
        # 检查滑点
        slippage = order.get("slippage_bps", 0)
        if slippage > self.alert_threshold["max_slippage"] * 10000:
            self.alerts.append({
                "type": "high_slippage",
                "severity": "warning",
                "message": f"高滑点: {slippage/10000*100:.2f}%",
                "order": order,
                "timestamp": time.time()
            })

    def _check_position_alerts(self, position: Dict) -> None:
        """检查持仓警报

        Args:
            position: 持仓字典
        """
        # 检查持仓比例
        total_value = position.get("total_value", 0)
        if total_value > self.alert_threshold["max_position_size"]:
            self.alerts.append({
                "type": "position_size",
                "severity": "warning",
                "message": f"持仓过大: {total_value*100:.1f}%",
                "position": position,
                "timestamp": time.time()
            })

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据

        Returns:
            仪表板数据字典
        """
        # 计算统计
        total_pnl = sum(p["pnl"] for p in self.metrics.pnl_history)
        win_count = sum(1 for p in self.metrics.pnl_history if p["pnl"] > 0)
        total_trades = len(self.metrics.pnl_history)
        win_rate = win_count / total_trades if total_trades > 0 else 0

        # 获取最新价格
        latest_prices = {}
        for symbol, history in self.metrics.price_history.items():
            if history:
                latest_prices[symbol] = history[-1]["price"]

        # 获取最新持仓
        latest_position = None
        if self.metrics.position_history:
            latest_position = self.metrics.position_history[-1]

        return {
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "total_pnl": total_pnl,
                "total_trades": total_trades,
                "win_rate": win_rate,
                "open_positions": len(self.metrics.position_history),
            },
            "prices": latest_prices,
            "latest_position": latest_position,
            "recent_orders": list(self.metrics.order_history)[-10:],
            "recent_opportunities": list(self.metrics.opportunity_history)[-10:],
            "alerts": self.alerts[-10:],
        }

    def get_performance_chart(self, hours: int = 24) -> List[Dict]:
        """获取性能图表数据

        Args:
            hours: 小时数

        Returns:
            图表数据列表
        """
        cutoff_time = time.time() - hours * 3600

        return [
            p for p in self.metrics.pnl_history
            if p["timestamp"] >= cutoff_time
        ]

    def get_opportunity_feed(self, minutes: int = 60) -> List[Dict]:
        """获取机会流

        Args:
            minutes: 分钟数

        Returns:
            机会列表
        """
        return self.metrics.get_price_range("OPPORTUNITY", minutes)


class RealtimeDashboard:
    """实时仪表板

    提供实时监控仪表板功能。
    """

    def __init__(self):
        """初始化实时仪表板"""
        self.provider = DashboardDataProvider()
        self.is_running = False
        self.update_interval = 1.0  # 秒

    def start(self) -> None:
        """启动仪表板"""
        self.is_running = True
        logger.info("实时仪表板已启动")

    def stop(self) -> None:
        """停止仪表板"""
        self.is_running = False
        logger.info("实时仪表板已停止")

    def get_data(self) -> Dict[str, Any]:
        """获取仪表板数据

        Returns:
            仪表板数据字典
        """
        return self.provider.get_dashboard_data()

    def export_json(self) -> str:
        """导出JSON格式

        Returns:
            JSON字符串
        """
        import json
        return json.dumps(
            self.get_data(),
            indent=2,
            default=str
        )

    def export_html(self) -> str:
        """导出HTML格式

        Returns:
            HTML字符串
        """
        data = self.get_data()

        stats = data["statistics"]
        prices = data.get("prices", {})

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Crypto Arbitrage Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }}
        .card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 16px;
        }}
        .card-title {{
            font-size: 12px;
            color: #8b949e;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        .card-value {{
            font-size: 28px;
            font-weight: bold;
        }}
        .positive {{ color: #3fb950; }}
        .negative {{ color: #f85149; }}
        .alert {{
            background: #f8514910;
            border-color: #f85149;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <div class="header">Crypto Arbitrage Dashboard</div>

    <div class="grid">
        <div class="card">
            <div class="card-title">Total PnL</div>
            <div class="card-value {{
                'positive' if stats['total_pnl'] >= 0 else 'negative'
            }}">${stats['total_pnl']:,.2f}</div>
        </div>
        <div class="card">
            <div class="card-title">Total Trades</div>
            <div class="card-value">{stats['total_trades']}</div>
        </div>
        <div class="card">
            <div class="card-title">Win Rate</div>
            <div class="card-value">{stats['win_rate']*100:.1f}%</div>
        </div>
        <div class="card">
            <div class="card-title">Open Positions</div>
            <div class="card-value">{stats['open_positions']}</div>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <div class="card-title">Prices</div>
            {''.join(f'<div>{k}: ${v:,.2f}</div>' for k, v in prices.items())}
        </div>
    </div>

    {''.join(f'<div class="alert">{a["message"]}</div>' for a in data['alerts'][:5])}

    <div class="card">
        <div class="card-title">Last Updated</div>
        <div>{data['timestamp']}</div>
    </div>
</body>
</html>
"""
        return html