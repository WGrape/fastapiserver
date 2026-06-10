"""
用户服务层
处理用户相关的业务逻辑
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.user import User
from src.schemas.user import UserCreate, UserUpdate


class UserService:
    """用户服务类"""

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        """根据 ID 获取用户"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> User | None:
        """根据用户名获取用户"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        """根据邮箱获取用户"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_in: UserCreate) -> User:
        """创建用户"""
        # TODO: 实现密码哈希
        # TODO: 检查用户名/邮箱是否已存在
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password="hashed_" + user_in.password,  # 待替换为真实哈希
            is_active=True,
            is_superuser=False,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def update(
        db: AsyncSession, user_id: int, user_in: UserUpdate
    ) -> User | None:
        """更新用户信息"""
        db_user = await UserService.get_by_id(db, user_id)
        if not db_user:
            return None

        update_data = user_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "password":
                # TODO: 密码需要哈希处理
                setattr(db_user, "hashed_password", "hashed_" + value)
            else:
                setattr(db_user, field, value)

        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def delete(db: AsyncSession, user_id: int) -> bool:
        """删除用户（软删除）"""
        db_user = await UserService.get_by_id(db, user_id)
        if not db_user:
            return False

        db_user.is_active = False
        await db.commit()
        return True
