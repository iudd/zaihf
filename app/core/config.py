import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra="ignore")

    APP_NAME: str = "zai-2api"
    APP_VERSION: str = "2.0.0 (Local)"
    API_MASTER_KEY: str = "1"
    PORT: int = 8000
    
    # [修改] 获取当前脚本运行的根目录
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # [修改] 拼接绝对路径，防止找不到文件
    DB_PATH: str = os.path.join(BASE_DIR, "data", "zai.db")
    
    # 账号数据目录 - 统一存储所有账号的浏览器数据
    ACCOUNTS_DATA_DIR: str = os.path.join(BASE_DIR, "accounts_data")
    
    # Zai 配置
    ZAI_BASE_URL: str = "https://zai.is"
    DEFAULT_MODEL: str = "gpt-5.1-chat-latest"

settings = Settings()