"""应用资源容器定义。"""
from dataclasses import dataclass
from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


@dataclass
class AppResources:
    """统一资源容器：所有跨请求复用资源在这里收口。"""

    http_client: AsyncClient
    db_engine: AsyncEngine
    db_session_factory: async_sessionmaker[AsyncSession]
    redis_client: Any | None = None


@dataclass
class ScriptResources:
    """脚本运行时的按需资源容器。"""

    db: AsyncSession | None = None
    http_client: AsyncClient | None = None
    redis_client: Any | None = None

