"""
用户 Pydantic Schema
用于请求/响应数据的验证和序列化
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# ========== 基础 Schema ==========
class UserBase(BaseModel):
    """用户基础 Schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """用户创建请求 Schema"""
    password: str = Field(..., min_length=6, max_length=50)


class UserUpdate(BaseModel):
    """用户更新请求 Schema（所有字段可选）"""
    username: str | None = Field(None, min_length=3, max_length=50)
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=6, max_length=50)
    is_active: bool | None = None


class UserInDB(UserBase):
    """从数据库读取的用户 Schema"""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


# ========== 响应 Schema ==========
class UserResponse(UserInDB):
    """用户响应 Schema（不包含密码）"""
    pass


# ========== Token Schema ==========
class Token(BaseModel):
    """Token 响应 Schema"""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token 载荷 Schema"""
    sub: str | None = None  # 用户ID或用户名
    exp: int | None = None  # 过期时间
