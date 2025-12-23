import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra="ignore")

    APP_NAME: str = "zai-2api"
    APP_VERSION: str = "2.0.0 (Hugging Face Space)"
    API_MASTER_KEY: str = "1"
    PORT: int = 7860  # Hugging Face Spaces 默认端口
    
    # 获取当前脚本运行的根目录
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 拼接绝对路径，防止找不到文件
    DB_PATH: str = os.path.join(BASE_DIR, "data", "zai.db")
    
    # 账号数据目录 - 统一存储所有账号的浏览器数据
    ACCOUNTS_DATA_DIR: str = os.path.join(BASE_DIR, "accounts_data")
    
    # Hugging Face Space 特定配置
    HF_SPACE: bool = os.environ.get("HF_SPACE", "true").lower() == "true"
    HF_SPACE_ID: str = os.environ.get("SPACE_ID", "")
    HF_TOKEN: str = os.environ.get("HF_TOKEN", "")
    
    # Zai 配置
    ZAI_BASE_URL: str = "https://zai.is"
    DEFAULT_MODEL: str = "gpt-5-2025-08-07"

settings = Settings()