"""监控 API V3.3 - 仪表板数据接口

提供实时监控、数据查询和系统控制的 API 接口。

核心功能：
1. 实时数据查询 API
2. 历史数据查询 API
3. 系统控制 API
4. 配置管理 API
5. WebSocket 实时推送
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# 创建 API 路由
router = APIRouter(prefix="/api/v3.3/monitoring", tags=["monitoring"])

# ---------------------- Pydantic Models ----------------------


class MetricQuery(BaseModel):
    """指标查询请求"""
    metric_names: Optional[List[str]] = None
    time_range: Optional[Tuple[str, str]] = None


class ControlRequest(BaseModel):
    """控制请求"""
    action: str
    params: Optional[Dict[str, Any]] = None


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    config_section: str
    config_data: Dict[str, Any]


class ExportRequest(BaseModel):
    """导出请求"""
    data_type: str
    format: str = 'json'


# ---------------------- WebSocket 连接管理 ----------------------


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected, total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected, total: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)

        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)


# 全局连接管理器
connection_manager = ConnectionManager()


# ---------------------- 实时数据 API ----------------------


@router.get("/overview")
async def get_overview() -> Dict[str, Any]:
    """获取系统总览数据

    Returns:
        系统总览数据字典
    """
    try:
        from monitoring.dashboard import get_dashboard

        dashboard = get_dashboard()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not initialized")

        return dashboard.get_overview_data()
    except Exception as e:
        logger.error(f"Error getting overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk")
async def get_risk_data() -> Dict[str, Any]:
    """获取风险监控数据

    Returns:
        风险监控数据字典
    """
    try:
        from monitoring.dashboard import get_dashboard

        dashboard = get_dashboard()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not initialized")

        return dashboard.get_risk_data()
    except Exception as e:
        logger.error(f"Error getting risk data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trade")
async def get_trade_data() -> Dict[str, Any]:
    """获取交易数据

    Returns:
        交易数据字典
    """
    try:
        from monitoring.dashboard import get_dashboard

        dashboard = get_dashboard()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not initialized")

        return dashboard.get_trade_data()
    except Exception as e:
        logger.error(f"Error getting trade data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy")
async def get_strategy_data() -> Dict[str, Any]:
    """获取策略数据

    Returns:
        策略数据字典
    """
    try:
        from monitoring.dashboard import get_dashboard

        dashboard = get_dashboard()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not initialized")

        return dashboard.get_strategy_data()
    except Exception as e:
        logger.error(f"Error getting strategy data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_data() -> Dict[str, Any]:
    """获取性能数据

    Returns:
        性能数据字典
    """
    try:
        from monitoring.dashboard import get_dashboard

        dashboard = get_dashboard()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not initialized")

        return dashboard.get_performance_data()
    except Exception as e:
        logger.error(f"Error getting performance data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics")
async def get_metrics(query: MetricQuery) -> Dict[str, List[Dict[str, Any]]]:
    """获取指标数据

    Args:
        query: 指标查询请求

    Returns:
        指标数据字典
    """
    try:
        from monitoring.dashboard import get_dashboard

        dashboard = get_dashboard()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not initialized")

        return dashboard.get_metrics(
            metric_names=query.metric_names,
            time_range=query.time_range
        )
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------- 系统控制 API ----------------------


@router.post("/control")
async def control_system(request: ControlRequest) -> Dict[str, Any]:
    """系统控制

    Args:
        request: 控制请求

    Returns:
        操作结果
    """
    try:
        from monitoring.dashboard import get_dashboard

        dashboard = get_dashboard()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not initialized")

        action = request.action
        params = request.params or {}

        result = {'action': action, 'success': False, 'message': ''}

        if action == 'start':
            dashboard.start()
            result['success'] = True
            result['message'] = 'Dashboard started'

        elif action == 'stop':
            dashboard.stop()
            result['success'] = True
            result['message'] = 'Dashboard stopped'

        elif action == 'clear_history':
            dashboard.clear_history()
            result['success'] = True
            result['message'] = 'History cleared'

        elif action == 'update_risk':
            dashboard.update_risk_metrics(params)
            result['success'] = True
            result['message'] = 'Risk metrics updated'

        elif action == 'record_trade':
            dashboard.record_trade(params)
            result['success'] = True
            result['message'] = 'Trade recorded'

        elif action == 'add_alert':
            dashboard.add_alert(params)
            result['success'] = True
            result['message'] = 'Alert added'

        else:
            result['message'] = f'Unknown action: {action}'

        return result
    except Exception as e:
        logger.error(f"Error in system control: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """获取系统状态

    Returns:
        系统状态字典
    """
    try:
        from monitoring.dashboard import get_dashboard

        dashboard = get_dashboard()
        if not dashboard:
            return {
                'dashboard_initialized': False,
                'status': 'not_available'
            }

        return {
            'dashboard_initialized': True,
            'is_running': dashboard.is_running,
            'uptime': dashboard.uptime,
            'start_time': dashboard.start_time.isoformat() if dashboard.start_time else None,
            'last_update': dashboard.system_status.get('last_update'),
            'active_connections': len(connection_manager.active_connections)
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------- 配置管理 API ----------------------


@router.post("/config/update")
async def update_config(request: ConfigUpdateRequest) -> Dict[str, Any]:
    """更新配置

    Args:
        request: 配置更新请求

    Returns:
        更新结果
    """
    try:
        # 这里可以集成配置热更新功能
        result = {
            'section': request.config_section,
            'success': False,
            'message': 'Config hot reload not implemented yet'
        }

        # TODO: 实现配置热更新逻辑
        # from config.hot_reload import reload_config_section
        # result = reload_config_section(request.config_section, request.config_data)

        return result
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/current")
async def get_current_config() -> Dict[str, Any]:
    """获取当前配置

    Returns:
        当前配置字典
    """
    try:
        # 这里可以返回当前系统配置
        result = {
            'message': 'Current config retrieval not implemented yet',
            'config': {}
        }

        # TODO: 实现配置获取逻辑
        # from config.config_manager import get_config_manager
        # manager = get_config_manager()
        # result['config'] = manager.get_current_config()

        return result
    except Exception as e:
        logger.error(f"Error getting current config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------- 数据导出 API ----------------------


@router.post("/export")
async def export_data(request: ExportRequest) -> Dict[str, Any]:
    """导出数据

    Args:
        request: 导出请求

    Returns:
        导出结果
    """
    try:
        from monitoring.dashboard import get_dashboard

        dashboard = get_dashboard()
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not initialized")

        data = dashboard.export_data(request.data_type, request.format)

        return {
            'data_type': request.data_type,
            'format': request.format,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------- WebSocket 实时推送 ----------------------


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 实时数据推送端点"""
    await connection_manager.connect(websocket)

    try:
        # 获取仪表板实例
        from monitoring.dashboard import get_dashboard
        dashboard = get_dashboard()

        if dashboard:
            # 发送初始数据
            await websocket.send_json({
                'type': 'initial',
                'data': dashboard.get_overview_data()
            })

        # 持续推送数据
        while True:
            try:
                if dashboard:
                    # 获取最新数据
                    data = dashboard.get_overview_data()

                    # 发送更新
                    await websocket.send_json({
                        'type': 'update',
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    })

                # 等待一段时间再推送
                import asyncio
                await asyncio.sleep(2.0)

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connection_manager.disconnect(websocket)


@router.websocket("/ws/risk")
async def websocket_risk_endpoint(websocket: WebSocket):
    """WebSocket 风险数据推送端点"""
    await connection_manager.connect(websocket)

    try:
        from monitoring.dashboard import get_dashboard
        dashboard = get_dashboard()

        if dashboard:
            # 发送初始数据
            await websocket.send_json({
                'type': 'initial',
                'data': dashboard.get_risk_data()
            })

        while True:
            try:
                if dashboard:
                    data = dashboard.get_risk_data()
                    await websocket.send_json({
                        'type': 'update',
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    })

                import asyncio
                await asyncio.sleep(2.0)

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in risk WebSocket loop: {e}")
                break

    except WebSocketDisconnect:
        logger.info("Risk WebSocket disconnected")
    except Exception as e:
        logger.error(f"Risk WebSocket error: {e}")
    finally:
        connection_manager.disconnect(websocket)


@router.websocket("/ws/trade")
async def websocket_trade_endpoint(websocket: WebSocket):
    """WebSocket 交易数据推送端点"""
    await connection_manager.connect(websocket)

    try:
        from monitoring.dashboard import get_dashboard
        dashboard = get_dashboard()

        if dashboard:
            # 发送初始数据
            await websocket.send_json({
                'type': 'initial',
                'data': dashboard.get_trade_data()
            })

        while True:
            try:
                if dashboard:
                    data = dashboard.get_trade_data()
                    await websocket.send_json({
                        'type': 'update',
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    })

                import asyncio
                await asyncio.sleep(2.0)

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in trade WebSocket loop: {e}")
                break

    except WebSocketDisconnect:
        logger.info("Trade WebSocket disconnected")
    except Exception as e:
        logger.error(f"Trade WebSocket error: {e}")
    finally:
        connection_manager.disconnect(websocket)


# ---------------------- 路由集成函数 ----------------------


def setup_monitoring_routes(app):
    """设置监控路由到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """
    app.include_router(router)
    logger.info("Monitoring routes setup complete")
