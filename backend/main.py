"""
FastAPI 主入口
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import engine, Base
from backend.api import cases, suites, executions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时自动建表"""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="接口自动化测试平台",
    description="基于 pytest + HttpClient 的可视化接口测试平台，支持手动/定时/CI 三种执行方式",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS（允许 Vue 前端跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(cases.router, prefix="/api")
app.include_router(suites.router, prefix="/api")
app.include_router(executions.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "测试平台后端运行正常"}


@app.get("/api/environments")
def list_environments():
    """获取所有可用环境列表"""
    import yaml
    config_path = os.path.join(
        settings.PROJECT_ROOT or os.path.dirname(os.path.dirname(__file__)),
        "config", "config.yaml",
    )
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    envs = list(cfg.get("environments", {}).keys())
    active = cfg.get("active_env", "")
    return {"environments": envs, "active_env": active}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
