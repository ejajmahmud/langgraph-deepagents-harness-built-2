"""JWT 认证模块 V1.6.0

为 FastAPI 后端提供 JWT Token 认证，保护敏感 API 端点。

功能:
- 用户注册和登录
- JWT Token 签发和验证
- Token 自动刷新
- API Key 支持（用于程序化访问）
- 速率限制
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# JWT 配置
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24
JWT_REFRESH_HOURS = 72

# 简易 JWT 实现（避免引入 PyJWT 依赖）
# 生产环境建议使用 PyJWT 库


def _base64url_encode(data: bytes) -> str:
    """Base64URL 编码（无填充）"""
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _base64url_decode(s: str) -> bytes:
    """Base64URL 解码"""
    import base64
    padding = 4 - len(s) % 4
    if padding != 4:
        s += '=' * padding
    return base64.urlsafe_b64decode(s)


def _ensure_secret() -> str:
    """确保 JWT 密钥存在"""
    global JWT_SECRET_KEY
    if not JWT_SECRET_KEY:
        JWT_SECRET_KEY = secrets.token_hex(32)
        logger.warning("JWT_SECRET_KEY 未设置，已生成临时密钥（重启后失效）")
    return JWT_SECRET_KEY


def _sign_jwt(header_b64: str, payload_b64: str) -> str:
    """签名 JWT"""
    secret = _ensure_secret()
    message = f"{header_b64}.{payload_b64}".encode('ascii')
    signature = hmac.new(secret.encode('ascii'), message, hashlib.sha256).digest()
    return _base64url_encode(signature)


def create_jwt(
    payload: Dict[str, Any],
    expire_hours: float = JWT_EXPIRE_HOURS,
) -> str:
    """创建 JWT Token

    Args:
        payload: 载荷数据
        expire_hours: 过期时间（小时）

    Returns:
        JWT Token 字符串
    """
    header = {"alg": "HS256", "typ": "JWT"}
    now = time.time()

    payload_data = {
        **payload,
        'iat': int(now),
        'exp': int(now + expire_hours * 3600),
        'nbf': int(now),
    }

    header_b64 = _base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = _base64url_encode(json.dumps(payload_data).encode('utf-8'))
    signature = _sign_jwt(header_b64, payload_b64)

    return f"{header_b64}.{payload_b64}.{signature}"


def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    """验证 JWT Token

    Args:
        token: JWT Token 字符串

    Returns:
        载荷数据，验证失败返回 None
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts

        # 验证签名
        expected_signature = _sign_jwt(header_b64, payload_b64)
        if not hmac.compare_digest(signature_b64, expected_signature):
            return None

        # 解析载荷
        payload = json.loads(_base64url_decode(payload_b64))

        # 检查过期
        if payload.get('exp', 0) < time.time():
            return None

        # 检查生效时间
        if payload.get('nbf', 0) > time.time():
            return None

        return payload

    except Exception as e:
        logger.debug(f"JWT 验证失败: {e}")
        return None


def _hash_password(password: str, salt: Optional[str] = None) -> tuple:
    """哈希密码

    Args:
        password: 明文密码
        salt: 盐值（可选）

    Returns:
        (哈希值, 盐值) 元组
    """
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000,
    ).hex()
    return hashed, salt


def _verify_password(password: str, hashed: str, salt: str) -> bool:
    """验证密码

    Args:
        password: 明文密码
        hashed: 存储的哈希值
        salt: 盐值

    Returns:
        是否匹配
    """
    new_hash, _ = _hash_password(password, salt)
    return hmac.compare_digest(new_hash, hashed)


class UserManager:
    """用户管理器 - 管理用户账户和认证

    使用简单的内存存储。生产环境应使用数据库。
    """

    def __init__(self) -> None:
        self._users: Dict[str, Dict[str, Any]] = {}
        self._api_keys: Dict[str, str] = {}  # api_key -> username
        self._rate_limits: Dict[str, List[float]] = {}  # username -> request timestamps
        self._max_requests_per_minute = 60

        # 创建默认管理员账户
        self._create_default_admin()

    def _create_default_admin(self) -> None:
        """创建默认管理员账户"""
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        hashed, salt = _hash_password(admin_password)
        self._users['admin'] = {
            'username': 'admin',
            'password_hash': hashed,
            'password_salt': salt,
            'role': 'admin',
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        logger.info("默认管理员账户已创建 (用户名: admin)")

    def register(
        self,
        username: str,
        password: str,
        role: str = 'user',
    ) -> Dict[str, Any]:
        """注册新用户

        Args:
            username: 用户名
            password: 密码
            role: 角色 ('admin', 'user', 'readonly')

        Returns:
            注册结果字典
        """
        if not username or len(username) < 3:
            return {'success': False, 'error': '用户名至少3个字符'}
        if not password or len(password) < 6:
            return {'success': False, 'error': '密码至少6个字符'}
        if username in self._users:
            return {'success': False, 'error': '用户已存在'}

        hashed, salt = _hash_password(password)
        self._users[username] = {
            'username': username,
            'password_hash': hashed,
            'password_salt': salt,
            'role': role,
            'created_at': datetime.now(timezone.utc).isoformat(),
        }

        return {
            'success': True,
            'username': username,
            'role': role,
        }

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            登录结果（含 JWT Token）
        """
        user = self._users.get(username)
        if not user:
            return {'success': False, 'error': '用户不存在'}

        if not _verify_password(password, user['password_hash'], user['password_salt']):
            return {'success': False, 'error': '密码错误'}

        # 签发 Token
        access_token = create_jwt({
            'sub': username,
            'role': user['role'],
            'type': 'access',
        }, expire_hours=JWT_EXPIRE_HOURS)

        refresh_token = create_jwt({
            'sub': username,
            'role': user['role'],
            'type': 'refresh',
        }, expire_hours=JWT_REFRESH_HOURS)

        return {
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': JWT_EXPIRE_HOURS * 3600,
            'role': user['role'],
        }

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """刷新 Access Token

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的 Token 对
        """
        payload = verify_jwt(refresh_token)
        if not payload:
            return {'success': False, 'error': '无效或过期的刷新令牌'}
        if payload.get('type') != 'refresh':
            return {'success': False, 'error': '不是刷新令牌'}

        username = payload['sub']
        user = self._users.get(username)
        if not user:
            return {'success': False, 'error': '用户不存在'}

        new_access = create_jwt({
            'sub': username,
            'role': user['role'],
            'type': 'access',
        }, expire_hours=JWT_EXPIRE_HOURS)

        return {
            'success': True,
            'access_token': new_access,
            'token_type': 'Bearer',
            'expires_in': JWT_EXPIRE_HOURS * 3600,
        }

    def create_api_key(self, username: str) -> Dict[str, Any]:
        """创建 API Key（用于程序化访问）

        Args:
            username: 用户名

        Returns:
            API Key 信息
        """
        if username not in self._users:
            return {'success': False, 'error': '用户不存在'}

        api_key = f"ca_{secrets.token_hex(24)}"
        self._api_keys[api_key] = username

        logger.info(f"API Key 已创建: {username} ({api_key[:12]}...)")
        return {
            'success': True,
            'api_key': api_key,
            'username': username,
        }

    def validate_api_key(self, api_key: str) -> Optional[str]:
        """验证 API Key

        Args:
            api_key: API Key

        Returns:
            用户名或 None
        """
        return self._api_keys.get(api_key)

    def check_rate_limit(self, username: str) -> bool:
        """检查速率限制

        Args:
            username: 用户名

        Returns:
            是否允许请求
        """
        now = time.time()
        if username not in self._rate_limits:
            self._rate_limits[username] = []

        # 清理一分钟前的记录
        self._rate_limits[username] = [
            t for t in self._rate_limits[username]
            if now - t < 60
        ]

        if len(self._rate_limits[username]) >= self._max_requests_per_minute:
            return False

        self._rate_limits[username].append(now)
        return True

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """获取用户信息（不含密码）"""
        user = self._users.get(username)
        if not user:
            return None
        return {
            'username': user['username'],
            'role': user['role'],
            'created_at': user.get('created_at'),
        }


# 全局用户管理器实例
user_manager = UserManager()


# 依赖注入函数（供 FastAPI 使用）
def authenticate_token(token: str) -> Optional[Dict[str, Any]]:
    """认证 JWT Token 或 API Key

    Args:
        token: Bearer Token 或 API Key

    Returns:
        用户信息字典或 None
    """
    # 尝试 API Key 认证
    if token.startswith('ca_'):
        username = user_manager.validate_api_key(token)
        if username:
            user = user_manager.get_user_info(username)
            if user:
                return user

    # 尝试 JWT 认证
    payload = verify_jwt(token)
    if payload:
        return user_manager.get_user_info(payload['sub'])

    return None


def require_role(role: str):
    """角色检查装饰器工厂

    Args:
        role: 要求的角色

    Returns:
        检查函数
    """
    def check(user_info: Optional[Dict[str, Any]]) -> bool:
        if not user_info:
            return False
        user_role = user_info.get('role', 'user')
        role_hierarchy = {'readonly': 1, 'user': 2, 'admin': 3}
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(role, 0)

    return check
