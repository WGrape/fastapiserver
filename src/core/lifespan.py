"""
应用生命周期 & 异步上下文管理器统一管理

所有 asynccontextmanager 集中在此模块，职责清晰：
  1. api_lifespan        — FastAPI 应用生命周期（资源初始化 / 销毁）
  2. script_lifespan     — 脚本运行生命周期（日志 + 异常兜底）
  3. db_session          — 便捷数据库 Session（脚本 / 测试用）
"""
from contextlib import asynccontextmanager
from contextlib import AsyncExitStack
from typing import AsyncGenerator
from typing import Any

import httpx
from fastapi import FastAPI
from httpx import AsyncClient
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.resources import AppResources, ScriptResources
from src.db.session import create_db_engine, create_db_session_factory


def _create_http_client() -> AsyncClient:
    """创建 HTTP 客户端资源（API 和脚本共用配置）。"""
    return AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
    )


# ================================================================
#  1. FastAPI 应用生命周期
# ================================================================

@asynccontextmanager
async def api_lifespan(app: FastAPI):
    """
    FastAPI lifespan — 统一管理基础资源的创建与销毁。

    在此处集中初始化，保证：
      • 有清晰的启动顺序
      • 关闭时统一清理资源
      • 所有端点都能通过 app.state 复用同一资源
    """
    # ---- 启动 ----
    logger.info("应用启动中...")

    db_engine = create_db_engine()
    resources = AppResources(
        http_client=_create_http_client(),
        db_engine=db_engine,
        db_session_factory=create_db_session_factory(db_engine),
    )
    app.state.resources = resources
    logger.info("✅ 应用资源初始化完成（http_client, db_engine, db_session_factory)")

    # Redis 客户端资源（按需启用）
    # import redis.asyncio as redis
    # app.state.redis_client = await redis.from_url(
    #     "redis://localhost:6379/0?encoding=utf-8",
    #     decode_responses=True,
    # )
    # logger.info("✅ Redis 客户端资源初始化完成")

    try:
        yield  # ---- 应用运行期间 ----
    finally:
        # ---- 关闭 ----
        logger.info("应用关闭中...")

        await app.state.resources.http_client.aclose()
        await app.state.resources.db_engine.dispose()
        logger.info("✅ 应用资源已关闭（http_client, db_engine)")

    # if hasattr(app.state, "redis_client"):
    #     await app.state.redis_client.close()
    #     logger.info("✅ Redis 客户端资源已关闭")


# ================================================================
#  2. 脚本运行上下文
# ================================================================

@asynccontextmanager
async def script_lifespan() -> AsyncGenerator[None, None]:
    """
    脚本运行上下文 — 包裹脚本主逻辑，提供日志与异常兜底。

    用法::

        async with script_lifespan():
            # 你的脚本逻辑
            ...
    """
    separator = "=" * 60
    logger.info(separator)
    logger.info(f"脚本运行: ENVIRONMENT={settings.environment}")
    logger.info(separator)

    try:
        yield
    except Exception as e:
        logger.exception(f"脚本执行失败: {e}")
        raise
    finally:
        logger.info(separator)
        logger.info("脚本结束")
        logger.info(separator)


# ================================================================
#  3. 便捷数据库 Session（脚本 / 测试场景）
# ================================================================

@asynccontextmanager
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库 Session 的便捷上下文管理器（非 FastAPI 依赖注入场景）。

    用法::

        async with db_session() as session:
            user = await UserService.get_by_id(session, 1)
    """
    engine = create_db_engine()
    session_factory = create_db_session_factory(engine)
    try:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()


@asynccontextmanager
async def _http_client_session() -> AsyncGenerator[AsyncClient, None]:
    """脚本场景下的 HTTP 客户端上下文。"""
    client = _create_http_client()
    try:
        yield client
    finally:
        await client.aclose()


def _build_redis_url() -> str:
    """按当前配置拼装 Redis URL。"""
    redis_cfg = settings.redis
    auth_part = f":{redis_cfg.password}@" if redis_cfg.password else ""
    return f"redis://{auth_part}{redis_cfg.host}:{redis_cfg.port}/{redis_cfg.db}"


@asynccontextmanager
async def _redis_session() -> AsyncGenerator[Any, None]:
    """脚本场景下的 Redis 客户端上下文（按需导入依赖）。"""
    try:
        import redis.asyncio as redis
    except ImportError as e:
        raise RuntimeError("需要安装 redis[asyncio] 才能启用 Redis 资源") from e

    client = redis.from_url(_build_redis_url(), decode_responses=True)
    try:
        yield client
    finally:
        await client.close()


@asynccontextmanager
async def script_runtime(
    *,
    with_db: bool = False,
    with_http: bool = False,
    with_redis: bool = False,
) -> AsyncGenerator[ScriptResources, None]:
    """
    单入口脚本上下文：按需申请资源，避免写 `async with a(), b(), c()`。

    用法::

        async with script_runtime(with_db=True, with_http=True) as ctx:
            user = await UserService.get_by_id(ctx.db, 1)
            resp = await ctx.http_client.get("https://example.com")
    """
    async with script_lifespan():
        async with AsyncExitStack() as stack:
            resources = ScriptResources()

            if with_db:
                resources.db = await stack.enter_async_context(db_session())
            if with_http:
                resources.http_client = await stack.enter_async_context(_http_client_session())
            if with_redis:
                resources.redis_client = await stack.enter_async_context(_redis_session())

            yield resources


