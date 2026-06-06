"""
平台后端配置 - 从环境变量读取，支持 .env 文件

开发模式：DB_TYPE=sqlite（默认）无需安装 MySQL/Redis
生产模式：DB_TYPE=mysql，需配置 MySQL 和 Redis
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """平台全局配置"""

    # ----- 数据库类型 -----
    # sqlite: 开发模式（默认，无需安装数据库）
    # mysql:  生产模式（需要 MySQL + Redis）
    DB_TYPE: str = "sqlite"

    # ----- MySQL（仅 DB_TYPE=mysql 时生效）-----
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_NAME: str = "pytest_api"

    @property
    def DATABASE_URL(self) -> str:
        if self.DB_TYPE == "mysql":
            return (
                f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
            )
        else:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "data", "pytest_api.db"
            )
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            return f"sqlite:///{db_path}"

    @property
    def IS_SQLITE(self) -> bool:
        return self.DB_TYPE != "mysql"

    # ----- Redis -----
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    @property
    def CELERY_BROKER_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB + 1}"

    # ----- 测试框架 -----
    PROJECT_ROOT: str = ""
    ALLURE_RESULTS_DIR: str = "reports/allure-results"

    # ----- 服务 -----
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
