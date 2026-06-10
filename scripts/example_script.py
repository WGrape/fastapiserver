"""
示例脚本：展示如何不启动 API 服务，直接使用项目核心功能

运行方式:
    export ENVIRONMENT=dev
    python -m src.cmd.script_runner scripts.example_script
"""
from loguru import logger

from src.cmd.script_runner import script_runtime
from src.services.user import UserService


async def do():
    """脚本入口函数"""
    async with script_runtime(with_db=True) as ctx:
        db = ctx.db
        if db is None:
            raise RuntimeError("数据库会话未初始化")

        # 示例：查询用户
        logger.info("查询用户 ID=1...")
        user = await UserService.get_by_id(db, user_id=1)
        if user:
            logger.info(f"找到用户: {user.username}")
        else:
            logger.info("用户不存在")

        # 示例：创建用户（取消注释测试）
        # logger.info("创建测试用户...")
        # new_user = await UserService.create(
        #     db,
        #     UserCreate(
        #         username="test_user",
        #         email="test@example.com",
        #         password="test123456"
        #     )
        # )
        # logger.info(f"创建用户成功: {new_user.id}")
