#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugging Face Space 入口点
这个文件用于在 Hugging Face Space 上部署 ZAI-2API 服务
"""

import os
import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from loguru import logger

# 将项目根目录添加到 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ.setdefault("HOST", "0.0.0.0")
os.environ.setdefault("PORT", "7860")  # Hugging Face Spaces 默认端口

# 导入原有的应用
from main import provider, db_manager
from app.core.config import settings

# 确保 playwright 浏览器已安装（同步方式）
def ensure_playwright():
    """确保 playwright 浏览器已安装"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # 尝试获取浏览器
            try:
                browser = p.chromium.launch()
                browser.close()
                print("✅ Playwright 浏览器已就绪")
            except Exception as e:
                print(f"⚠️ Playwright 浏览器检查失败: {e}")
                print("🔄 正在安装 Playwright 浏览器...")
                os.system("playwright install chromium")
                print("✅ Playwright 浏览器安装完成")
    except ImportError as e:
        print(f"❌ Playwright 未安装: {e}")

# 启动时执行 playwright 检查
print("🔍 检查 Playwright 浏览器...")
ensure_playwright()

# 创建新的 FastAPI 应用实例
app = FastAPI(title=settings.APP_NAME, lifespan=None)

# 添加 CORS 中间件，允许跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时的初始化函数
async def startup_init():
    """
    应用启动时的初始化操作
    """
    from pathlib import Path
    
    # 确保必要的目录存在
    dirs = ["data", "media", "static", "templates", "accounts_data", "zai_user_data"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True, parents=True)
    
    # 初始化数据库
    db_manager.init_db()
    
    # 检查是否有账号
    accounts = db_manager.get_all_accounts()
    if not accounts:
        logger.warning("⚠️ 没有找到账号，请通过 Web 界面添加账号")
    
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 已在 Hugging Face Space 上启动")
    logger.info(f"🌐 服务地址: https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME")

# 在 FastAPI 应用启动时执行初始化
@app.on_event("startup")
async def on_startup():
    await startup_init()

# 导入 main.py 中的所有路由
from main import *