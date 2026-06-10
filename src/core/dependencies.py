"""
依赖注入模块
提供通用的依赖项，如当前用户、权限检查等
"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from src.core.providers import security
from src.core.resources import AppResources
from src.core.security import decode_token



async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    获取当前登录用户（依赖注入）
    从 JWT token 中解析用户信息
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    # TODO: 根据 user_id 从数据库查询用户
    return {"user_id": user_id, "payload": payload}


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    获取当前活跃用户
    可扩展：检查用户是否被禁用
    """
    # TODO: 检查用户 is_active 状态
    return current_user


async def get_current_superuser(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    """
    获取当前超级用户（管理员权限）
    """
    # TODO: 检查用户 is_superuser 状态
    return current_user


def get_app_resources(request: Request) -> AppResources:
    """依赖注入：获取应用级统一资源容器。"""
    resources = getattr(request.app.state, "resources", None)
    if resources is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="应用资源未初始化，请检查 api_lifespan 配置",
        )
    return resources


def get_http_client(resources: AppResources = Depends(get_app_resources)):
    """依赖注入：获取 lifespan 初始化的 HTTP 客户端。"""
    return resources.http_client


def get_redis_client(resources: AppResources = Depends(get_app_resources)):
    """依赖注入：获取 lifespan 初始化的 Redis 客户端。"""
    client = resources.redis_client
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="redis_client 未初始化，请检查 api_lifespan 配置",
        )
    return client

