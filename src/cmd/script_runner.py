"""
脚本入口点管理

提供统一的方式运行独立脚本，不需要启动 Web 服务。

用法：
    python -m src.cmd.script_runner scripts.example
    python -m src.cmd.script_runner scripts.init_db
"""
import sys
import asyncio
from pathlib import Path
from importlib import import_module

from loguru import logger

# 确保项目根目录在 sys.path 中
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core import lifespan as lifespan_module
from src.db.session import init_db

ScriptResources = lifespan_module.ScriptResources
script_lifespan = lifespan_module.script_lifespan
script_runtime = lifespan_module.script_runtime
get_db_session = lifespan_module.db_session

__all__ = [
    "ScriptResources",
    "script_lifespan",
    "script_context",
    "script_runtime",
    "get_db_session",
    "init_db_if_needed",
    "run_script",
    "main",
]


# ========== 脚本可用的工具函数 ==========

# 兼容旧脚本导入：from src.cmd.script_runner import script_context
script_context = script_lifespan


async def init_db_if_needed():
    """初始化数据库表"""
    logger.info("初始化数据库...")
    await init_db()
    logger.info("数据库初始化完成")


# ========== 脚本运行核心逻辑 ==========

async def run_script(module_path: str):
    """运行指定模块的脚本"""
    try:
        module = import_module(module_path)

        if hasattr(module, 'do'):
            # 新风格：async do() 函数
            if asyncio.iscoroutinefunction(module.do):
                await module.do()
            else:
                module.do()
        elif hasattr(module, 'main'):
            # 兼容旧风格：main() 函数
            logger.warning("建议使用 async do() 函数代替 main()")
            if hasattr(module.main, '__code__') and 'async' in str(module.main.__code__):
                await module.main()
            else:
                module.main()
        else:
            print(f"错误: 模块 {module_path} 没有 do() 函数")
            sys.exit(1)

    except ImportError as e:
        logger.error(f"无法导入模块 {module_path}: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"脚本执行失败: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("用法: python -m src.cmd.script_runner <模块路径>")
        print("示例: python -m src.cmd.script_runner scripts.example")
        sys.exit(1)

    module_path = sys.argv[1]
    asyncio.run(run_script(module_path))


if __name__ == "__main__":
    main()
