"""
数据库会话管理
数据库资源由 api_lifespan 统一创建与销毁。
"""
from typing import AsyncGenerator

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base

from src.core.config import settings

# 声明基类（全局唯一，所有 Model 继承它）
Base = declarative_base()


def create_db_engine() -> AsyncEngine:
    """创建异步引擎（由调用方管理生命周期）。"""
    return create_async_engine(
        settings.database.url,
        echo=settings.app.debug,
        future=True,
        pool_pre_ping=True,
    )


def create_db_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """基于给定引擎创建 Session 工厂。"""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


def _get_app_resources(request: Request):
    """从 app.state 读取统一资源容器。"""
    resources = getattr(request.app.state, "resources", None)
    if resources is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="应用资源未初始化，请检查 api_lifespan 配置",
        )
    return resources


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（FastAPI 依赖注入）

    用法：
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    session_factory = _get_app_resources(request).db_session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db(engine: AsyncEngine | None = None):
    """初始化数据库，创建所有未存在的表"""
    managed_engine = engine or create_db_engine()
    try:
        async with managed_engine.connect() as conn:
            async with conn.begin():
                await conn.run_sync(Base.metadata.create_all)
    finally:
        if engine is None:
            await managed_engine.dispose()
