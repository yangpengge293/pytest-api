import logging
import os
import yaml

# 读取配置
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

log_level = getattr(logging, config.get("log_level", "INFO").upper(), logging.INFO)

# 配置日志格式
formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 控制台输出
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger = logging.getLogger("api_test")
logger.setLevel(log_level)
logger.addHandler(console_handler)
