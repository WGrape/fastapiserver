"""
初始化数据库脚本：创建所有数据表

运行方式:
    export ENVIRONMENT=dev
    python -m src.cmd.script_runner scripts.init_db_script
"""
from loguru import logger

from src.cmd.script_runner import script_lifespan, init_db_if_needed
from src.core.config import settings


async def do():
    """初始化数据库"""
    async with script_lifespan():
        logger.warning(f"即将在数据库: {settings.database.url} 中创建表")
        logger.warning("确认继续? (Ctrl+C 取消)")

        # 暂停一下让用户确认
        import asyncio
        await asyncio.sleep(3)

        logger.info("开始创建数据表...")
        await init_db_if_needed()
        logger.info("✅ 数据库表创建完成!")
