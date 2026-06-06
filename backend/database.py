"""
SQLAlchemy 数据库连接与会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from backend.config import settings

# SQLite 不支持连接池参数，需区分处理
if settings.IS_SQLITE:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        echo=False,
    )

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
