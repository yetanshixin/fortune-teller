"""应用配置：从环境变量 / .env 读取。"""
import os

from dotenv import load_dotenv

# 加载 backend/.env（若存在）
load_dotenv()

# DeepSeek 大模型接入配置
# API Key 请通过 backend/.env（本地，已被 .gitignore 忽略）或环境变量（Render）配置，不要硬编码在代码里。
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")

# 支持切换的模型列表
ALLOWED_MODELS = ["deepseek-v4-pro", "deepseek-flash"]

# 服务监听配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
