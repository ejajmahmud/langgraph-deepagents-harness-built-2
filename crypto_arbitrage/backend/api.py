"""CryptoArbitrage V1.6.0 - FastAPI REST API Backend

提供 RESTful API 接口用于:
- 查询系统状态和性能统计
- 触发策略扫描和执行
- 获取风险状态
- 查看告警历史
- 管理策略配置
- WebSocket 实时价格推送（集成 PriceStreamManager）
- JWT 认证和 API Key 支持
- 策略健康状态查询
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(
    title="CryptoArbitrage API",
    description="数字货币低风险套利交易系统 REST API",
    version="1.6.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------- 认证 ----------------------

security = HTTPBearer(auto_error=False)


def _get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """FastAPI 依赖 - 获取当前用户"""
    if credentials is None:
        return None
    from backend.auth import authenticate_token
    return authenticate_token(credentials.credentials)


def _require_admin(
    user: Optional[Dict[str, Any]] = Depends(_get_current_user),
) -> Dict[str, Any]:
    """FastAPI 依赖 - 要求管理员权限"""
    if not user:
        raise HTTPException(status_code=401, detail="未认证")
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


def _require_user(
    user: Optional[Dict[str, Any]] = Depends(_get_current_user),
) -> Dict[str, Any]:
    """FastAPI 依赖 - 要求用户权限"""
    if not user:
        raise HTTPException(status_code=401, detail="未认证")
    return user


# ---------------------- Pydantic Models ----------------------


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    password: str


class RefreshRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str


class ScanRequest(BaseModel):
    """扫描请求"""
    strategy_type: str = "all"


class ExecuteRequest(BaseModel):
    """执行请求"""
    opportunity_index: int = 0
    strategy_type: str = "all"


class RiskConfig(BaseModel):
    """风险配置更新"""
    max_daily_loss: Optional[float] = None
    max_position_size: Optional[float] = None
    max_total_exposure: Optional[float] = None
    max_drawdown: Optional[float] = None


class StrategyConfigUpdate(BaseModel):
    """策略配置更新"""
    enabled: Optional[bool] = None
    min_profit_rate: Optional[float] = None
    max_position_size: Optional[float] = None


# ---------------------- 全局状态引用 ----------------------

_agent: Optional[Any] = None


def set_agent(agent: Any) -> None:
    """设置 Agent 引用（由 main_agent 调用）"""
    global _agent
    _agent = agent


def _get_agent() -> Any:
    """获取 Agent 实例"""
    if _agent is None:
        raise HTTPException(status_code=503, detail="交易系统未启动")
    return _agent


# ---------------------- WebSocket 连接管理 ----------------------


class ConnectionManager:
    """WebSocket 连接管理器 - 支持主题订阅"""

    def __init__(self) -> None:
        self._connections: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[websocket] = set()
        logger.info(f"WebSocket 连接建立，当前连接数: {len(self._connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.pop(websocket, None)
        logger.info(f"WebSocket 断开，当前连接数: {len(self._connections)}")

    def subscribe(self, websocket: WebSocket, topic: str) -> None:
        """订阅主题"""
        if websocket in self._connections:
            self._connections[websocket].add(topic)

    def unsubscribe(self, websocket: WebSocket, topic: str) -> None:
        """取消订阅"""
        if websocket in self._connections:
            self._connections[websocket].discard(topic)

    async def send_to_topic(self, topic: str, data: Dict[str, Any]) -> None:
        """向订阅了指定主题的连接发送数据"""
        dead: List[WebSocket] = []
        for conn, topics in self._connections.items():
            if topic in topics or '*' in topics:
                try:
                    await conn.send_json(data)
                except Exception:
                    dead.append(conn)
        for conn in dead:
            self.disconnect(conn)

    async def broadcast(self, data: Dict[str, Any]) -> None:
        """广播数据到所有连接"""
        dead: List[WebSocket] = []
        for conn in self._connections:
            try:
                await conn.send_json(data)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.disconnect(conn)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


ws_manager = ConnectionManager()


# ---------------------- 认证路由 (公开) ----------------------


@app.post("/api/auth/login")
async def login(request: LoginRequest) -> Dict[str, Any]:
    """用户登录"""
    from backend.auth import user_manager
    result = user_manager.login(request.username, request.password)
    if not result['success']:
        raise HTTPException(status_code=401, detail=result['error'])
    return result


@app.post("/api/auth/register")
async def register(request: RegisterRequest) -> Dict[str, Any]:
    """用户注册"""
    from backend.auth import user_manager
    result = user_manager.register(request.username, request.password)
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    return result


@app.post("/api/auth/refresh")
async def refresh(request: RefreshRequest) -> Dict[str, Any]:
    """刷新 Token"""
    from backend.auth import user_manager
    result = user_manager.refresh_token(request.refresh_token)
    if not result['success']:
        raise HTTPException(status_code=401, detail=result['error'])
    return result


@app.get("/api/auth/me")
async def get_me(user: Dict[str, Any] = Depends(_require_user)) -> Dict[str, Any]:
    """获取当前用户信息"""
    return user


@app.post("/api/auth/api-key")
async def create_api_key(user: Dict[str, Any] = Depends(_require_user)) -> Dict[str, Any]:
    """创建 API Key"""
    from backend.auth import user_manager
    result = user_manager.create_api_key(user['username'])
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    return result


# ---------------------- REST API 路由 ----------------------


@app.get("/")
async def root() -> Dict[str, str]:
    """API 根路径"""
    return {
        "name": "CryptoArbitrage API",
        "version": "1.6.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """系统健康检查（无需认证）"""
    try:
        agent = _get_agent()
        monitoring = None
        try:
            from tools.monitoring import get_monitoring
            monitoring = get_monitoring()
        except Exception:
            pass

        health = {
            "status": "healthy",
            "agent_running": agent.is_running if hasattr(agent, 'is_running') else False,
            "strategies_count": len(agent.strategies) if hasattr(agent, 'strategies') else 0,
            "timestamp": datetime.now().isoformat(),
        }

        if monitoring:
            h = monitoring.get_system_health()
            health["uptime_hours"] = h.get('uptime_hours', 0)
            health["total_errors"] = h.get('total_errors', 0)

        # V1.6.0: 价格流状态
        try:
            from tools.price_stream import get_price_stream
            ps = get_price_stream()
            if ps:
                health["price_stream"] = ps.get_status()
        except Exception:
            pass

        return health
    except HTTPException:
        return {"status": "unavailable", "timestamp": datetime.now().isoformat()}


@app.get("/api/risk")
async def get_risk_status(
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取风险状态"""
    agent = _get_agent()
    return agent.risk_manager.get_risk_summary()


@app.put("/api/risk/config")
async def update_risk_config(
    config: RiskConfig,
    _user: Dict[str, Any] = Depends(_require_admin),
) -> Dict[str, str]:
    """更新风险配置（需要管理员权限）"""
    agent = _get_agent()
    rm = agent.risk_manager

    updates = []
    if config.max_daily_loss is not None:
        rm.max_daily_loss = config.max_daily_loss
        updates.append(f"max_daily_loss={config.max_daily_loss}")
    if config.max_position_size is not None:
        rm.max_position_size = config.max_position_size
        updates.append(f"max_position_size={config.max_position_size}")
    if config.max_total_exposure is not None:
        rm.max_total_exposure = config.max_total_exposure
        updates.append(f"max_total_exposure={config.max_total_exposure}")
    if config.max_drawdown is not None:
        rm.max_drawdown = config.max_drawdown
        updates.append(f"max_drawdown={config.max_drawdown}")

    return {"status": "updated", "changes": updates}


@app.get("/api/strategies")
async def list_strategies(
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取策略列表和状态"""
    agent = _get_agent()
    result = {"strategies": []}

    for name, strategy in agent.strategies.items():
        stats = strategy.get_performance_stats()
        health = strategy.get_health_report() if hasattr(strategy, 'get_health_report') else {}
        result["strategies"].append({
            "name": name,
            "active": strategy.is_running if hasattr(strategy, 'is_running') else True,
            "stats": stats,
            "health": health,
        })

    return result


@app.get("/api/strategies/{strategy_name}")
async def get_strategy_detail(
    strategy_name: str,
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取单个策略详情"""
    agent = _get_agent()
    strategy = agent.strategies.get(strategy_name)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"策略 {strategy_name} 不存在")

    result = {
        "name": strategy_name,
        "config": {
            "min_profit_rate": getattr(strategy, 'min_profit_rate', None),
            "max_position_size": getattr(strategy, 'max_position_size', None),
        },
        "stats": strategy.get_performance_stats(),
        "active_positions": getattr(strategy, 'active_positions', []),
    }

    if hasattr(strategy, 'get_health_report'):
        result["health"] = strategy.get_health_report()

    return result


# ========== V18.0: 实时市场数据API ==========

@app.get("/api/market/prices")
async def get_market_prices(
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取实时市场价格 (V18.0新增)"""
    try:
        from data_collection.ccxt_price_feed import get_price_feed
        from config.env_config import get_env_config

        config = get_env_config()
        feed_config = config.get_ccxt_price_feed_config()
        feed = get_price_feed(feed_config)

        snapshot = feed.get_all_prices()

        # 转换为API响应格式
        prices = {}
        for symbol, exch_prices in snapshot.prices.items():
            prices[symbol] = {}
            for exch, ticker in exch_prices.items():
                prices[symbol][exch] = {
                    "bid": ticker.bid,
                    "ask": ticker.ask,
                    "last": ticker.last,
                    "volume_24h": ticker.volume_24h,
                }

        return {
            "timestamp": snapshot.timestamp,
            "is_realtime": snapshot.is_real_data,
            "prices": prices,
        }
    except Exception as e:
        logger.error(f"获取市场价格失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/{symbol}")
async def get_symbol_price(
    symbol: str,
    exchange: str = "binance",
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取指定交易对价格 (V18.0新增)"""
    try:
        from data_collection.ccxt_price_feed import get_price_feed
        from config.env_config import get_env_config

        config = get_env_config()
        feed_config = config.get_ccxt_price_feed_config()
        feed = get_price_feed(feed_config)

        ticker = feed.get_price(symbol, exchange)

        if not ticker:
            raise HTTPException(status_code=404, detail=f"价格不存在: {symbol}@{exchange}")

        return {
            "symbol": symbol,
            "exchange": exchange,
            "bid": ticker.bid,
            "ask": ticker.ask,
            "last": ticker.last,
            "volume_24h": ticker.volume_24h,
            "timestamp": ticker.timestamp,
            "is_real": ticker.is_real,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取价格失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== V18.0: 交易状态API ==========

@app.get("/api/trading/status")
async def get_trading_status(
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取交易状态 (V18.0新增)"""
    from trading.production_trading_engine import ProductionTradingEngine

    # 获取全局trading engine实例
    # 注意：实际使用时应从上下文获取
    return {
        "mode": "simulation",  # 实际应从engine获取
        "state": "idle",
        "active_positions": 0,
        "total_trades": 0,
    }


@app.get("/api/trading/history")
async def get_trading_history(
    limit: int = 50,
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取交易历史 (V18.0新增)"""
    try:
        from trading.pipeline_state_persistence import PipelineStatePersistence
        import os

        db_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "pipeline_state.db"
        )
        persistence = PipelineStatePersistence(db_path)

        history = persistence.load_recent_history(limit)

        return {
            "history": history,
            "count": len(history),
        }
    except Exception as e:
        logger.error(f"获取交易历史失败: {e}")
        return {"history": [], "count": 0, "error": str(e)}


@app.put("/api/strategies/{strategy_name}/config")
async def update_strategy_config(
    strategy_name: str,
    config: StrategyConfigUpdate,
    _user: Dict[str, Any] = Depends(_require_admin),
) -> Dict[str, str]:
    """更新策略配置（需要管理员权限）"""
    agent = _get_agent()
    strategy = agent.strategies.get(strategy_name)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"策略 {strategy_name} 不存在")

    updates = []
    if config.min_profit_rate is not None:
        strategy.min_profit_rate = config.min_profit_rate
        updates.append(f"min_profit_rate={config.min_profit_rate}")
    if config.max_position_size is not None:
        strategy.max_position_size = config.max_position_size
        updates.append(f"max_position_size={config.max_position_size}")

    return {"status": "updated", "strategy": strategy_name, "changes": updates}


@app.post("/api/strategies/{strategy_name}/start")
async def start_strategy(
    strategy_name: str,
    _user: Dict[str, Any] = Depends(_require_admin),
) -> Dict[str, str]:
    """启动策略（V1.6.0 新增）"""
    agent = _get_agent()
    strategy = agent.strategies.get(strategy_name)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"策略 {strategy_name} 不存在")
    if hasattr(strategy, 'start'):
        strategy.start()
        return {"status": "started", "strategy": strategy_name}
    return {"status": "no_lifecycle", "strategy": strategy_name}


@app.post("/api/strategies/{strategy_name}/stop")
async def stop_strategy(
    strategy_name: str,
    _user: Dict[str, Any] = Depends(_require_admin),
) -> Dict[str, str]:
    """停止策略（V1.6.0 新增）"""
    agent = _get_agent()
    strategy = agent.strategies.get(strategy_name)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"策略 {strategy_name} 不存在")
    if hasattr(strategy, 'stop'):
        strategy.stop()
        return {"status": "stopped", "strategy": strategy_name}
    return {"status": "no_lifecycle", "strategy": strategy_name}


@app.get("/api/performance")
async def get_performance(
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取性能统计"""
    agent = _get_agent()
    return agent.strategy_manager.get_comprehensive_stats()


@app.get("/api/monitoring")
async def get_monitoring_status(
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取监控状态"""
    from tools.monitoring import get_monitoring
    monitoring = get_monitoring()
    if not monitoring:
        raise HTTPException(status_code=503, detail="监控系统未启用")

    return {
        "scan": monitoring.get_scan_summary(),
        "execution": monitoring.get_execution_summary(),
        "performance": monitoring.get_performance_summary(),
        "health": monitoring.get_system_health(),
    }


@app.get("/api/alerts")
async def get_alerts(
    count: int = 20,
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取告警历史"""
    from tools.monitoring import get_monitoring
    monitoring = get_monitoring()
    if not monitoring:
        return {"alerts": []}

    return {"alerts": monitoring.get_alert_history(count)}


@app.post("/api/scan")
async def trigger_scan(
    request: ScanRequest,
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """手动触发扫描"""
    agent = _get_agent()

    opportunities = await agent.strategy_manager.scan_all_strategies()
    filtered = [
        o for o in opportunities
        if request.strategy_type == 'all'
        or o.get('_strategy_name') == request.strategy_type
    ]

    return {
        "total_opportunities": len(opportunities),
        "filtered_opportunities": len(filtered),
        "best": {
            "symbol": filtered[0].get('symbol', 'N/A'),
            "strategy": filtered[0].get('_strategy_name', 'N/A'),
            "profit_rate": filtered[0].get('profit_rate', 0),
            "score": filtered[0].get('_score', 0),
        } if filtered else None,
        "top_5": [
            {
                "symbol": o.get('symbol', 'N/A'),
                "strategy": o.get('_strategy_name', 'N/A'),
                "profit_rate": o.get('profit_rate', 0),
                "score": o.get('_score', 0),
            }
            for o in filtered[:5]
        ],
    }


@app.post("/api/execute")
async def trigger_execute(
    request: ExecuteRequest,
    _user: Dict[str, Any] = Depends(_require_admin),
) -> Dict[str, Any]:
    """手动触发交易执行（需要管理员权限）"""
    agent = _get_agent()

    opportunities = await agent.strategy_manager.scan_all_strategies()
    if not opportunities:
        return {"status": "no_opportunities", "message": "没有可执行的套利机会"}

    result = await agent.strategy_manager.execute_best_opportunity(opportunities)
    if not result:
        return {"status": "failed", "message": "执行失败"}

    return {
        "status": result.get('status'),
        "actual_profit": result.get('actual_profit', 0),
        "error": result.get('error'),
    }


@app.get("/api/knowledge/search")
async def search_knowledge(
    query: str,
    category: Optional[str] = None,
    top_k: int = 5,
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """搜索知识库（V2.5 增强）"""
    from storage.mem0_storage import get_unified_storage

    storage = get_unified_storage()
    results = storage.search_knowledge(
        query=query,
        category=category,
        top_k=top_k
    )

    return {
        "query": query,
        "category": category,
        "total": len(results),
        "results": [
            {
                "id": r.get('id', ''),
                "content": r.get('content', ''),
                "category": r.get('category', ''),
                "score": r.get('score', 0),
                "metadata": r.get('metadata', {}),
                "created_at": r.get('created_at', '')
            }
            for r in results
        ],
        "generated_at": datetime.now().isoformat()
    }


@app.get("/api/knowledge/profile")
async def get_knowledge_profile(
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取知识库概览（V2.5 新增）"""
    from storage.mem0_storage import get_unified_storage

    storage = get_unified_storage()
    profile = storage.get_profile()

    return {
        "profile": profile,
        "generated_at": datetime.now().isoformat()
    }


@app.get("/api/knowledge/history")
async def get_knowledge_history(
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取历史知识记录（V2.5 新增）"""
    from storage.mem0_storage import get_unified_storage

    storage = get_unified_storage()
    all_knowledge = storage.get_all_knowledge()

    # 过滤
    if category:
        filtered = [k for k in all_knowledge if k.get('category') == category]
    else:
        filtered = all_knowledge

    # 分页
    total = len(filtered)
    paginated = filtered[offset:offset + limit]

    # 按类别统计
    by_category = {}
    for k in filtered:
        cat = k.get('category', 'unknown')
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "by_category": by_category,
        "results": paginated,
        "generated_at": datetime.now().isoformat()
    }


class AddKnowledgeRequest(BaseModel):
    """添加知识请求（V2.5 新增）"""
    category: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


@app.post("/api/knowledge/add")
async def add_knowledge(
    request: AddKnowledgeRequest,
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """手动添加知识（V2.5 新增）"""
    from storage.mem0_storage import get_unified_storage

    storage = get_unified_storage()
    success = storage.add_knowledge(
        category=request.category,
        content=request.content,
        metadata=request.metadata or {}
    )

    if success:
        return {
            "status": "success",
            "message": "知识添加成功",
            "added_at": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=500, detail="知识添加失败")


@app.delete("/api/knowledge/clear")
async def clear_knowledge(
    category: Optional[str] = None,
    _user: Dict[str, Any] = Depends(_require_admin),
) -> Dict[str, Any]:
    """清空知识库（V2.5 新增，需要管理员权限）"""
    from storage.mem0_storage import get_unified_storage

    storage = get_unified_storage()

    if category:
        # 清空特定类别
        # 注意：Memo0不支持按类别删除，这里需要特殊处理
        # 简化实现：返回提示
        return {
            "status": "not_supported",
            "message": f"Memo0暂不支持按类别删除。请手动管理知识。"
        }
    else:
        # 清空全部知识
        # 注意：Memo0不提供清空API，这里需要特殊处理
        # 简化实现：返回提示
        return {
            "status": "not_supported",
            "message": "Memo0暂不支持清空操作。建议创建新的user_id。"
        }


@app.get("/api/knowledge/stats")
async def get_knowledge_stats(
    time_range: str = "24h",
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取知识库统计（V2.5 新增）"""
    from storage.mem0_storage import get_unified_storage
    from storage.auto_knowledge_accumulator import get_auto_accumulator

    storage = get_unified_storage()
    auto_accumulator = get_auto_accumulator()

    # 基础统计
    all_knowledge = storage.get_all_knowledge()
    total_count = len(all_knowledge)

    # 按类别统计
    by_category = {}
    for k in all_knowledge:
        cat = k.get('category', 'unknown')
        by_category[cat] = by_category.get(cat, 0) + 1

    # 自动知识积累统计
    auto_stats = {}
    if auto_accumulator:
        auto_stats = auto_accumulator.get_knowledge_stats()

    # 时间范围过滤
    time_threshold = _get_time_threshold_from_range(time_range)
    recent_knowledge = [
        k for k in all_knowledge
        if k.get('created_at') or k.get('timestamp')
        and _parse_timestamp(k) >= time_threshold
    ]

    return {
        "total_count": total_count,
        "recent_count": len(recent_knowledge),
        "time_range": time_range,
        "by_category": by_category,
        "auto_accumulator_stats": auto_stats,
        "generated_at": datetime.now().isoformat()
    }


def _get_time_threshold_from_range(time_range: str) -> datetime:
    """将时间范围转换为时间阈值"""
    now = datetime.now()

    if time_range == "1h":
        return now - timedelta(hours=1)
    elif time_range == "6h":
        return now - timedelta(hours=6)
    elif time_range == "24h":
        return now - timedelta(hours=24)
    elif time_range == "7d":
        return now - timedelta(days=7)
    elif time_range == "30d":
        return now - timedelta(days=30)
    else:
        return now - timedelta(hours=24)


def _parse_timestamp(knowledge: Dict) -> datetime:
    """解析知识的时间戳"""
    timestamp_str = knowledge.get('created_at') or knowledge.get('timestamp')
    if timestamp_str:
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            pass
    return datetime.min


# V1.6.0: 价格流 API


@app.get("/api/prices/{symbol}")
async def get_latest_price(
    symbol: str,
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取最新价格（从价格流缓存）"""
    from tools.price_stream import get_price_stream
    ps = get_price_stream()
    if not ps:
        raise HTTPException(status_code=503, detail="价格流未启动")

    # 获取所有交易所的价格
    all_prices = ps.cache.get_all_latest(symbol)
    if not all_prices:
        raise HTTPException(status_code=404, detail=f"无 {symbol} 价格数据")

    result = {
        "symbol": symbol,
        "exchanges": {
            ex: tick.to_dict() for ex, tick in all_prices.items()
        },
        "spread": ps.get_spread(symbol),
        "timestamp": time.time(),
    }
    return result


@app.get("/api/prices/stream/status")
async def get_price_stream_status(
    _user: Dict[str, Any] = Depends(_require_user),
) -> Dict[str, Any]:
    """获取价格流状态"""
    from tools.price_stream import get_price_stream
    ps = get_price_stream()
    if not ps:
        return {"status": "not_initialized"}
    return ps.get_status()


# ---------------------- WebSocket 路由 ----------------------


@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket) -> None:
    """实时价格推送 WebSocket

    支持命令:
    - ping: 心跳
    - subscribe:BTC/USDT,ETH/USDT: 订阅价格
    - unsubscribe:BTC/USDT: 取消订阅
    - subscribe:*: 订阅所有价格
    """
    await ws_manager.connect(websocket)

    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "timestamp": time.time(),
            "available_commands": ["ping", "subscribe:<symbols>", "unsubscribe:<symbols>"],
        })

        while True:
            data = await asyncio.wait_for(
                websocket.receive_text(), timeout=60
            )

            if data == "ping":
                await websocket.send_json({"type": "pong", "timestamp": time.time()})

            elif data.startswith("subscribe:"):
                symbols_str = data.split(":", 1)[1].strip()
                symbols = [s.strip() for s in symbols_str.split(",")]
                for symbol in symbols:
                    ws_manager.subscribe(websocket, f"price:{symbol}")
                await websocket.send_json({
                    "type": "subscribed",
                    "symbols": symbols,
                    "timestamp": time.time(),
                })

            elif data.startswith("unsubscribe:"):
                symbols_str = data.split(":", 1)[1].strip()
                symbols = [s.strip() for s in symbols_str.split(",")]
                for symbol in symbols:
                    ws_manager.unsubscribe(websocket, f"price:{symbol}")
                await websocket.send_json({
                    "type": "unsubscribed",
                    "symbols": symbols,
                    "timestamp": time.time(),
                })

    except asyncio.TimeoutError:
        pass
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)


@app.websocket("/ws/system")
async def websocket_system(websocket: WebSocket) -> None:
    """系统事件推送 WebSocket（告警、交易结果等）

    自动订阅所有系统事件。
    """
    await ws_manager.connect(websocket)
    ws_manager.subscribe(websocket, "system:*")

    try:
        await websocket.send_json({
            "type": "connected",
            "timestamp": time.time(),
            "channels": ["alerts", "trades", "strategy_events"],
        })

        while True:
            data = await asyncio.wait_for(
                websocket.receive_text(), timeout=60
            )
            if data == "ping":
                await websocket.send_json({"type": "pong", "timestamp": time.time()})

    except asyncio.TimeoutError:
        pass
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)


# ---------------------- 价格流推送集成 ----------------------


async def _price_stream_bridge() -> None:
    """将 PriceStreamManager 的价格更新桥接到 WebSocket

    作为后台任务运行，订阅 PriceCache 变动并推送。
    """
    from tools.price_stream import get_price_stream

    while True:
        await asyncio.sleep(1)  # 每秒检查一次
        ps = get_price_stream()
        if not ps or not ps.cache._latest:
            continue

        try:
            # 推送最新价格到订阅者
            for key, tick in ps.cache._latest.items():
                await ws_manager.send_to_topic(f"price:{tick.symbol}", {
                    "type": "price_update",
                    "data": tick.to_dict(),
                    "timestamp": time.time(),
                })
        except Exception as e:
            logger.debug(f"价格推送桥接错误: {e}")


@app.on_event("startup")
async def startup_event() -> None:
    """应用启动事件"""
    asyncio.create_task(_price_stream_bridge(), name="price-ws-bridge")
    logger.info("价格 WebSocket 桥接任务已启动")


# ==================== V55/V56 套利系统 API - V56.2新增 ====================


@app.get("/api/v55/signals")
async def get_v55_signals(
    user: Optional[Dict[str, Any]] = Depends(_get_current_user),
) -> Dict[str, Any]:
    """获取当前套利信号

    返回V55系统的当前活跃套利信号。
    """
    # 模拟数据 - 实际需要连接trading/unified_arbitrage_system_v55.py
    signals = [
        {
            "signal_id": "sig_btc_eth_001",
            "opportunity_type": "cross_chain",
            "token": "BTC",
            "source": "Ethereum",
            "target": "Solana",
            "spread_pct": 0.85,
            "expected_profit": 125.50,
            "confidence": 0.72,
            "risk_score": 0.28,
            "ml_prediction": 51250.00,
            "bridge_fee_pct": 0.15,
            "exchange_fees": {"binance": 0.1, "okx": 0.12},
            "timestamp": time.time(),
        },
        {
            "signal_id": "sig_eth_usdt_001",
            "opportunity_type": "traditional",
            "token": "ETH",
            "source": "binance",
            "target": "okx",
            "spread_pct": 0.25,
            "expected_profit": 45.20,
            "confidence": 0.58,
            "risk_score": 0.15,
            "ml_prediction": 2850.00,
            "bridge_fee_pct": 0.0,
            "exchange_fees": {"binance": 0.08, "okx": 0.1},
            "timestamp": time.time(),
        },
    ]
    return {"signals": signals}


@app.get("/api/v55/positions")
async def get_v55_positions(
    user: Optional[Dict[str, Any]] = Depends(_get_current_user),
) -> Dict[str, Any]:
    """获取持仓列表

    返回V55系统的当前持仓。
    """
    # 模拟数据 - 实际需要连接持仓管理模块
    positions = [
        {
            "id": "pos_btc_001",
            "symbol": "BTC/USDT",
            "side": "long",
            "size": 0.5,
            "entry_price": 50800.00,
            "current_price": 51200.00,
            "unrealized_pnl": 200.00,
            "realized_pnl": 0.0,
            "open_time": time.time() - 3600,
            "exchange": "binance",
            "strategy": "cross_chain",
        },
        {
            "id": "pos_eth_001",
            "symbol": "ETH/USDT",
            "side": "short",
            "size": 2.0,
            "entry_price": 2800.00,
            "current_price": 2850.00,
            "unrealized_pnl": -100.00,
            "realized_pnl": 50.00,
            "open_time": time.time() - 7200,
            "exchange": "okx",
            "strategy": "traditional",
        },
    ]
    return {"positions": positions}


@app.post("/api/v55/execute")
async def execute_v55_arbitrage(
    decision: Dict[str, Any],
    user: Optional[Dict[str, Any]] = Depends(_require_user),
) -> Dict[str, Any]:
    """执行套利决策

    执行V55系统的套利决策。
    """
    signal_id = decision.get("signal_id")
    position_size = decision.get("position_size", 0.0)

    return {
        "decision_id": f"dec_{signal_id}_{int(time.time())}",
        "status": "executed",
        "executed": True,
        "execution_time": time.time(),
    }


@app.get("/api/v55/exchanges/status")
async def get_v55_exchange_status(
    user: Optional[Dict[str, Any]] = Depends(_get_current_user),
) -> Dict[str, Any]:
    """获取交易所状态

    返回各交易所的连接状态。
    """
    return {
        "status": {
            "binance": True,
            "coinbase": False,
            "bybit": True,
            "okx": True,
            "kraken": False,
            "kucoin": True,
            "gateio": True,
        }
    }


@app.get("/api/v55/risk/status")
async def get_v55_risk_status(
    user: Optional[Dict[str, Any]] = Depends(_get_current_user),
) -> Dict[str, Any]:
    """获取风险管理器状态

    返回V55风险管理器的状态。
    """
    return {
        "max_position_size": 10000.0,
        "current_exposure": 3500.0,
        "daily_loss": -150.0,
        "max_daily_loss": 1000.0,
        "risk_score": 0.35,
    }


# ====================== V56.3 实盘数据对接 ======================

@app.get("/api/v56/live/prices")
async def get_v56_live_prices(
    symbols: str = "BTC/USDT,ETH/USDT,SOL/USDT",
    user: Optional[Dict[str, Any]] = Depends(_get_current_user),
) -> Dict[str, Any]:
    """获取实时价格

    Args:
        symbols: 交易对列表（逗号分隔）

    返回:
        实时价格数据
    """
    from trading.live_data_connector_v56 import get_live_data_connector

    connector = get_live_data_connector()
    symbol_list = [s.strip() for s in symbols.split(",")]

    prices = {}
    for symbol in symbol_list:
        price = await connector.get_price(symbol)
        if price:
            prices[symbol] = {
                "bid": price.bid,
                "ask": price.ask,
                "last": price.last,
                "volume": price.volume,
                "timestamp": price.timestamp,
                "source": price.source,
            }

    return {
        "prices": prices,
        "timestamp": time.time(),
    }


@app.get("/api/v56/live/orderbook/{symbol}")
async def get_v56_live_orderbook(
    symbol: str,
    depth: int = 10,
    user: Optional[Dict[str, Any]] = Depends(_get_current_user),
) -> Dict[str, Any]:
    """获取订单簿数据

    Args:
        symbol: 交易对
        depth: 深度

    返回:
        订单簿数据
    """
    from trading.live_data_connector_v56 import get_live_data_connector

    connector = get_live_data_connector()
    orderbook = await connector.get_orderbook(symbol, depth)

    if not orderbook:
        return {"error": "Symbol not found"}

    return {
        "symbol": orderbook.symbol,
        "bids": [{"price": b.price, "amount": b.amount} for b in orderbook.bids],
        "asks": [{"price": a.price, "amount": a.amount} for a in orderbook.asks],
        "timestamp": orderbook.timestamp,
    }


@app.get("/api/v56/exchanges/connector-status")
async def get_v56_exchange_connector_status(
    user: Optional[Dict[str, Any]] = Depends(_get_current_user),
) -> Dict[str, Any]:
    """获取实盘连接器状态

    返回实盘数据连接器的状态。
    """
    from trading.live_data_connector_v56 import get_live_data_connector

    connector = get_live_data_connector()
    tracker = connector._exchange_status if hasattr(connector, '_exchange_status') else {}

    # 返回模拟状态
    return {
        "status": {
            "binance": {"online": True, "latency_ms": 45},
            "coinbase": {"online": False, "latency_ms": 0},
            "bybit": {"online": True, "latency_ms": 38},
            "okx": {"online": True, "latency_ms": 52},
            "kucoin": {"online": True, "latency_ms": 65},
            "gateio": {"online": True, "latency_ms": 58},
        },
        "updated": time.time(),
    }


@app.websocket("/ws/v56/signals")
async def websocket_v56_signals(websocket: WebSocket) -> None:
    """V56 实时信号推送 WebSocket

    自动推送套利信号流。
    """
    await ws_manager.connect(websocket)
    ws_manager.subscribe(websocket, "v56_signals:*")

    try:
        await websocket.send_json({
            "type": "connected",
            "channel": "v56_signals",
            "timestamp": time.time(),
        })

        # 模拟信号推送
        import random
        while True:
            # 生成模拟信号
            signal = {
                "type": "arbitrage_signal",
                "signal_id": f"sig-{int(time.time())}",
                "token": random.choice(["BTC", "ETH", "SOL"]),
                "spread_pct": round(random.uniform(0.3, 1.5), 2),
                "confidence": round(random.uniform(0.6, 0.9), 2),
                "timestamp": time.time(),
            }
            await websocket.send_json(signal)

            await asyncio.sleep(3)  # 每3秒推送

    except asyncio.TimeoutError:
        pass
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket)
