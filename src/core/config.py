"""
应用配置管理
从 YAML 配置文件加载配置，支持通过环境变量覆盖单个配置项
支持多环境配置：通过 ENVIRONMENT 变量指定加载 etc/{dev|test|prod}/config.yml
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
import yaml


def get_config_path() -> Path:
    """
    根据 ENVIRONMENT 环境变量确定要加载的配置文件路径
    """
    env = os.getenv("ENVIRONMENT", "dev")
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "etc" / env / "config.yml"

    if not config_path.exists():
        # 如果环境配置不存在，尝试查找 etc/config.yml
        fallback_path = project_root / "etc" / "config.yml"
        if fallback_path.exists():
            return fallback_path
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    return config_path


def deep_update(source: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    深度更新字典，支持嵌套结构
    """
    for key, value in overrides.items():
        if isinstance(value, dict) and key in source and isinstance(source[key], dict):
            deep_update(source[key], value)
        else:
            source[key] = value
    return source


def load_config_from_env() -> Dict[str, Any]:
    """
    从环境变量加载配置覆盖项
    支持格式: APP_NAME, JWT_SECRET_KEY, DATABASE_URL
    支持嵌套: APP__NAME, JWT__SECRET_KEY
    """
    result: Dict[str, Any] = {}

    for key, value in os.environ.items():
        key = key.upper()
        # 只处理我们关心的配置前缀
        if key.startswith(("APP_", "JWT_", "DATABASE_", "REDIS_", "ENVIRONMENT")):
            # 转换为嵌套结构
            parts = key.replace("__", "_").split("_", 1)
            if len(parts) == 2:
                prefix, rest = parts
                prefix = prefix.lower()

                # 初始化子字典
                if prefix not in result:
                    result[prefix] = {}

                # 转换布尔值和数字
                parsed_value: Any = value
                if value.lower() == "true":
                    parsed_value = True
                elif value.lower() == "false":
                    parsed_value = False
                elif value.isdigit():
                    parsed_value = int(value)
                elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                    parsed_value = float(value)

                result[prefix][rest.lower()] = parsed_value

    return result


@dataclass
class AppConfig:
    """应用配置"""
    name: str = "server"
    version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000"])
    log_level: str = "INFO"


@dataclass
class JWTConfig:
    """JWT 配置"""
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


@dataclass
class DatabaseConfig:
    """数据库配置"""
    # mysql+aiomysql://user:password@localhost:3306/test_database
    url: str = ""


@dataclass
class RedisConfig:
    """Redis 配置"""
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0


class Settings:
    """应用配置类"""

    def __init__(self, config_path: Optional[Path] = None):
        # 加载 YAML 配置文件
        if config_path is None:
            config_path = get_config_path()

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        # 从环境变量加载覆盖项
        env_overrides = load_config_from_env()
        deep_update(config_data, env_overrides)

        # 环境标识
        self.environment: str = config_data.get("environment", "dev")

        # 解析各配置块
        self._app = self._parse_app_config(config_data.get("app", {}))
        self._jwt = self._parse_jwt_config(config_data.get("jwt", {}))
        self._database = self._parse_database_config(config_data.get("database", {}))
        self._redis = self._parse_redis_config(config_data.get("redis", {}))

    def _parse_app_config(self, data: Dict[str, Any]) -> AppConfig:
        return AppConfig(
            name=data.get("name", "server"),
            version=data.get("version", "0.1.0"),
            debug=data.get("debug", False),
            host=data.get("host", "0.0.0.0"),
            port=data.get("port", 8000),
            cors_origins=data.get("cors_origins", ["http://localhost:3000"]),
            log_level=data.get("log_level", "INFO"),
        )

    def _parse_jwt_config(self, data: Dict[str, Any]) -> JWTConfig:
        return JWTConfig(
            secret_key=data.get("secret_key", "your-secret-key-change-in-production"),
            algorithm=data.get("algorithm", "HS256"),
            access_token_expire_minutes=data.get("access_token_expire_minutes", 30),
        )

    def _parse_database_config(self, data: Dict[str, Any]) -> DatabaseConfig:
        return DatabaseConfig(
            url=data.get("url", ""),
        )

    def _parse_redis_config(self, data: Dict[str, Any]) -> RedisConfig:
        return RedisConfig(
            host=data.get("host", "localhost"),
            port=data.get("port", 6379),
            password=data.get("password", ""),
            db=data.get("db", 0),
        )

    @property
    def app(self) -> AppConfig:
        """应用配置"""
        return self._app

    @property
    def jwt(self) -> JWTConfig:
        """JWT 配置"""
        return self._jwt

    @property
    def database(self) -> DatabaseConfig:
        """数据库配置"""
        return self._database

    @property
    def redis(self) -> RedisConfig:
        """Redis 配置"""
        return self._redis


# 全局配置实例
settings = Settings()
