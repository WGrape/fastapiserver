"""可复用依赖对象提供器。"""
from fastapi.security import HTTPBearer

# 认证依赖对象集中定义，避免分散在多个模块里。
security = HTTPBearer()

