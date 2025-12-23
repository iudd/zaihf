#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugging Face Space 入口点
这个文件用于在 Hugging Face Space 上部署 ZAI-2API 服务
"""

import os
import sys
import asyncio
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse

# 将项目根目录添加到 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ.setdefault("HOST", "0.0.0.0")
os.environ.setdefault("PORT", "7860")  # Hugging Face Spaces 默认端口

# 导入原有的应用
from main import app, provider, db_manager
from app.core.config import settings

# 添加 CORS 中间件，允许跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加一个简单的首页，用于在 Hugging Face Space 上显示
@app.get("/", response_class=HTMLResponse)
async def hf_home():
    """
    Hugging Face Space 的首页
    重定向到原始的仪表板
    """
    return RedirectResponse(url="/dashboard")

# 添加一个新的路由，确保在 Hugging Face Space 上正常工作
@app.get("/health")
async def health_check():
    """
    健康检查端点，用于 Hugging Face Space 监控
    """
    return {"status": "healthy", "service": settings.APP_NAME, "version": settings.APP_VERSION}

# 启动时的初始化函数
async def startup_init():
    """
    应用启动时的初始化操作
    """
    import os
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
        print("⚠️ 没有找到账号，请通过 Web 界面添加账号")
    
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 已在 Hugging Face Space 上启动")
    print(f"🌐 服务地址: https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME")

# 在 FastAPI 应用启动时执行初始化
@app.on_event("startup")
async def on_startup():
    await startup_init()

# 确保 playwright 浏览器已安装
async def ensure_playwright():
    """确保 playwright 浏览器已安装"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # 尝试获取浏览器，如果不存在则会触发自动下载
            try:
                browser = p.chromium.launch()
                browser.close()
                print("✅ Playwright 浏览器已就绪")
            except Exception as e:
                print("🔄 正在安装 Playwright 浏览器...")
                os.system("playwright install chromium")
                print("✅ Playwright 浏览器安装完成")
    except ImportError:
        print("❌ Playwright 未安装")
        
# 在后台线程中检查 playwright
threading.Thread(target=lambda: asyncio.run(ensure_playwright()), daemon=True).start()

if __name__ == "__main__":
    import uvicorn
    
    # 打印启动信息
    print("=" * 50)
    print("🚀 ZAI-2API for Hugging Face Space")
    print("=" * 50)
    
    # 启动服务
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7860)),
        reload=False,  # 在生产环境中不使用热重载
        log_level="info"
    )