"""API v1 路由聚合"""
from fastapi import APIRouter

from src.api.v1.endpoints import health, users

# prefix 在 main.py 中注入 /api/v1，这里不重复加
api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["健康检查"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
