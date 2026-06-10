"""健康检查端点"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.core.dependencies import get_http_client
from src.db.session import get_db

router = APIRouter()


@router.get("/")
async def health_check(client=Depends(get_http_client)):
    """
    基础健康检查
    演示：从 lifespan 管理的共享资源获取客户端
    """
    return {
        "status": "ok",
        "message": "Service is running",
        "http_client_type": type(client).__name__,
    }


@router.get("/db")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    """数据库健康检查"""
    try:
        result = await db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "connected",
            "result": result.scalar(),
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e),
        }


@router.get("/http-test")
async def http_client_test(
    client=Depends(get_http_client),
    url: str = "https://httpbin.org/status/200",
):
    """
    演示 HTTP 客户端共享资源的使用

    用法：GET /api/v1/health/http-test?url=https://example.com
    """
    resp = await client.get(url, timeout=5.0)
    return {
        "status": "ok",
        "test_url": url,
        "response_status": resp.status_code,
        "http_client_id": id(client),  # 同一个对象 → 资源复用生效
    }


@router.get("/http-test-di")
async def http_client_test_di(
    client=Depends(get_http_client),
):
    """
    演示用依赖注入方式获取共享资源
    """
    resp = await client.get("https://httpbin.org/status/200", timeout=5.0)
    return {
        "dependency_injection": True,
        "response_status": resp.status_code,
        "client_id": id(client),
    }
