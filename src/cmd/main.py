"""
FastAPI 应用入口
"""
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中，支持直接运行 python src/cmd/main.py
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.lifespan import api_lifespan
from src.api.v1 import api_router


def create_application() -> FastAPI:
    """创建 FastAPI 应用实例"""
    application = FastAPI(
        title=settings.app.name,
        description="server",
        version=settings.app.version,
        lifespan=api_lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # 配置 CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.app.cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    application.include_router(api_router, prefix="/api/v1")

    return application


app = create_application()


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "server is running",
        "docs": "/api/docs",
        "version": settings.app.version,
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.cmd.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
