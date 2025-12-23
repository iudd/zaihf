#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import time
import os
import secrets
import base64
from datetime import timedelta, datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, Header, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from app.core.config import settings
from app.core.db_manager import db_manager
from app.providers.zai_provider import ZaiProvider
from app.utils.har_parser import extract_token_from_text
from app.utils.token_auto_refresh_service import auto_refresh_service

# 图片管理类
class ImageManager:
    def __init__(self):
        self.media_dir = "media"
        if not os.path.exists(self.media_dir):
            os.makedirs(self.media_dir)
        self.cleanup_task = None

    def start_cleanup_task(self):
        """启动定时清理任务"""
        if self.cleanup_task is None:
            # 仅在事件循环运行时启动清理任务
            try:
                self.cleanup_task = asyncio.create_task(self.cleanup_old_images())
            except RuntimeError:
                # 如果没有运行的事件循环，记录下来稍后处理
                logger.warning("没有运行的事件循环，稍后启动清理任务")

    async def cleanup_old_images(self):
        """定期清理30分钟前的图片"""
        while True:
            try:
                await asyncio.sleep(60 * 30)  # 每30分钟检查一次
                now = datetime.now()
                for filename in os.listdir(self.media_dir):
                    file_path = os.path.join(self.media_dir, filename)
                    if os.path.isfile(file_path):
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if now - file_time > timedelta(minutes=30):
                            try:
                                os.remove(file_path)
                            except Exception as e:
                                logger.error(f"删除旧图片失败 {file_path}: {e}")
            except Exception as e:
                logger.error(f"清理图片任务出错: {e}")

    def save_base64_image(self, base64_data: str) -> str:
        """保存base64图片并返回文件名"""
        # 移除base64前缀
        if base64_data.startswith('data:image'):
            header, base64_data = base64_data.split(',', 1)
            # 根据图片类型确定扩展名
            if 'jpeg' in header or 'jpg' in header:
                ext = 'jpg'
            elif 'png' in header:
                ext = 'png'
            elif 'gif' in header:
                ext = 'gif'
            elif 'webp' in header:
                ext = 'webp'
            else:
                ext = 'png'  # 默认为png
        else:
            ext = 'png'  # 默认为png

        # 生成唯一文件名
        filename = f"{secrets.token_urlsafe(16)}.{ext}"
        filepath = os.path.join(self.media_dir, filename)

        # 解码并保存图片
        image_data = base64.b64decode(base64_data)
        with open(filepath, 'wb') as f:
            f.write(image_data)

        return filename

    def get_image_path(self, filename: str) -> str:
        """获取图片完整路径"""
        return os.path.join(self.media_dir, filename)

image_manager = ImageManager()

# --- 全局 Provider ---
provider = ZaiProvider()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    
    # 1. 启动时检查过期 Token
    asyncio.create_task(perform_breakpoint_update())
    
    # 2. 启动自动刷新服务
    asyncio.create_task(auto_refresh_service.start())
    
    # 3. 启动图片管理清理任务
    image_manager.start_cleanup_task()
    
    # 4. 确保必要的目录存在
    import os
    from pathlib import Path
    dirs = ["data", "media", "static", "templates", "accounts_data", "zai_user_data"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True, parents=True)
    
    # 5. 显示启动信息
    if settings.HF_SPACE:
        logger.info(f"🌐 Hugging Face Space 服务地址: https://huggingface.co/spaces/{settings.HF_SPACE_ID}")
    else:
        logger.info(f"🌐 本地服务地址: http://localhost:{settings.PORT}")
    
    yield
    
    # 6. 停止服务
    auto_refresh_service.stop()
    logger.info("🛑 服务已停止")

app = FastAPI(lifespan=lifespan, title=settings.APP_NAME)
templates = Jinja2Templates(directory="templates")

# 挂载静态文件目录（用于图片等资源）
import os
import secrets
from datetime import timedelta
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, RedirectResponse
import httpx
import urllib.parse

# 创建静态文件目录（如果不存在）
static_dir = os.path.join(os.getcwd(), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 为 Zai 图片创建别名（用于处理 /media/ 路径）
media_dir = os.path.join(os.getcwd(), "media")
os.makedirs(media_dir, exist_ok=True)
app.mount("/media", StaticFiles(directory=media_dir), name="media")

# 图片代理端点 - 处理 Zai 图片的跨域问题
@app.get("/img-proxy")
async def img_proxy(url: str):
    """
    图片代理端点，用于处理 Zai 图片的跨域问题
    """
    try:
        # 验证URL是否为Zai的图片URL
        if not url.startswith(('https://zai.is/media/', 'http://zai.is/media/')):
            # 如果不是Zai的图片，检查是否是其他外部图片URL
            if url.startswith(('http://', 'https://')):
                # 对于外部图片URL，也进行代理处理
                pass
            else:
                # 如果不是URL格式，返回错误
                return JSONResponse({"error": "无效的图片URL"}, status_code=400)
        
        # 下载图片
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30)
            response.raise_for_status()
            
            # 获取内容类型
            content_type = response.headers.get('content-type', 'image/jpeg')
            
            # 返回图片
            from fastapi.responses import Response
            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=3600",  # 缓存1小时
                    "Access-Control-Allow-Origin": "*",      # 允许跨域访问
                    "Access-Control-Allow-Methods": "GET, OPTIONS",   # 允许GET和OPTIONS方法
                    "Access-Control-Allow-Headers": "*",      # 允许所有头部
                    "Access-Control-Allow-Credentials": "false"  # 不包含凭据
                }
            )
    except httpx.HTTPStatusError as e:
        logger.error(f"图片代理错误 - HTTP状态码: {e.response.status_code}")
        # 返回一个默认图片或错误
        return JSONResponse({"error": f"无法加载图片 - 状态码: {e.response.status_code}"}, status_code=404)
    except Exception as e:
        logger.error(f"图片代理错误: {e}")
        # 返回一个默认图片或错误
        return JSONResponse({"error": "无法加载图片"}, status_code=404)

# --- 鉴权 ---
async def verify_api_key(authorization: str = Header(None)):
    if settings.API_MASTER_KEY and settings.API_MASTER_KEY != "1":
        if not authorization or authorization.split(" ")[1] != settings.API_MASTER_KEY:
            raise HTTPException(status_code=403, detail="Invalid API Key")

# --- 页面路由 ---
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    accounts = db_manager.get_all_accounts()
    logs = db_manager.get_recent_logs()
    
    active_count = len([acc for acc in accounts if acc["is_active"]])
    inactive_count = len(accounts) - active_count
    
    # 根据环境设置 API URL
    if settings.HF_SPACE:
        api_url = f"https://{settings.HF_SPACE_ID.replace('/', '-')}.hf.space"
    else:
        api_url = f"http://localhost:{settings.PORT}"
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "api_url": api_url,
        "accounts": accounts,
        "active_count": active_count,
        "inactive_count": inactive_count,
        "logs": logs,
        "is_hf_space": settings.HF_SPACE,
        "space_id": settings.HF_SPACE_ID
    })

# --- API 路由 (账号管理) ---
@app.post("/api/account/login/start")
async def start_browser_login(name: str = Form(...)):
    """
    [核心功能] Web UI 触发浏览器登录
    """
    logger.info(f"🌐 Web UI 请求启动浏览器登录: {name}")
    
    # 检查重名
    accounts = db_manager.get_all_accounts()
    for acc in accounts:
        if acc['name'] == name:
            return JSONResponse(status_code=400, content={"success": False, "message": "账号名称已存在"})

    # 调用 Service 启动有头浏览器
    # 注意：这里使用 await 会阻塞 HTTP 请求直到登录完成（或超时）
    # 对于本地单人使用是完全可以的，能直接拿到结果
    result = await auto_refresh_service.login_new_account(name)
    
    return JSONResponse(result)

@app.post("/api/account/add")
async def add_account(name: str = Form(...), token: str = Form(...)):
    """手动添加 Token"""
    if not provider.verify_token(token):
        return JSONResponse(status_code=400, content={"success": False, "message": "Token 无效"})
    
    account_id = db_manager.create_account(name, token, None, 'manual')
    if account_id:
        return JSONResponse({"success": True, "message": "账号添加成功"})
    return JSONResponse(status_code=500, content={"success": False, "message": "数据库错误"})

@app.post("/api/account/extract")
async def extract_token_api(request: Request):
    data = await request.json()
    token = extract_token_from_text(data.get("content", ""))
    if token:
        return JSONResponse({"success": True, "token": token, "is_valid": provider.verify_token(token)})
    return JSONResponse({"success": False, "message": "未找到 Token"})

@app.get("/api/account/delete/{id}")
async def delete_account(id: int):
    db_manager.delete_account(id)
    return RedirectResponse("/", status_code=303)

@app.get("/api/account/toggle/{id}")
async def toggle_account(id: int):
    db_manager.toggle_account(id)
    return RedirectResponse("/", status_code=303)

@app.get("/api/logs/clear")
async def clear_logs():
    db_manager.clear_logs()
    return RedirectResponse("/", status_code=303)

# --- API 路由 (OpenAI 兼容) ---
@app.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)])
async def chat_completions(request: Request):
    start_time = time.time()
    try:
        request_data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")
        
    model = request_data.get("model", settings.DEFAULT_MODEL)
    accounts = db_manager.get_all_accounts(active_only=True)
    
    if not accounts:
        raise HTTPException(status_code=503, detail="没有可用账号")
    
    for account in accounts:
        try:
            # 直接使用 Token 请求
            response_generator = provider.chat_completion(request_data, account["token"])
            
            # 记录日志
            duration = int((time.time() - start_time) * 1000)
            db_manager.add_log(account["name"], model, "SUCCESS", duration)
            
            return StreamingResponse(response_generator, media_type="text/event-stream")
        except Exception as e:
            logger.error(f"账号 {account['name']} 失败: {e}")
            db_manager.add_log(account["name"], model, "ERROR", int((time.time() - start_time) * 1000))
            continue
            
    raise HTTPException(status_code=503, detail="所有账号均调用失败")

@app.get("/v1/models")

async def list_models():

    """返回所有支持的模型列表"""

    models = [

        {"id": "gemini-3-pro-image-preview", "object": "model", "owned_by": "zai", "name": "Nano Banana Pro"},

        {"id": "gemini-2.5-pro", "object": "model", "owned_by": "zai", "name": "Gemini 2.5 Pro"},

        {"id": "claude-opus-4-20250514", "object": "model", "owned_by": "zai", "name": "Claude Opus 4"},

        {"id": "claude-sonnet-4-5-20250929", "object": "model", "owned_by": "zai", "name": "Claude Sonnet 4.5"},

        {"id": "claude-sonnet-4-20250514", "object": "model", "owned_by": "zai", "name": "Claude Sonnet 4"},

        {"id": "claude-haiku-4-5-20251001", "object": "model", "owned_by": "zai", "name": "Claude Haiku 4.5"},

        {"id": "o1-2024-12-17", "object": "model", "owned_by": "zai", "name": "o1"},

        {"id": "o3-pro-2025-06-10", "object": "model", "owned_by": "zai", "name": "o3-pro"},

        {"id": "grok-4-1-fast-reasoning", "object": "model", "owned_by": "zai", "name": "Grok 4.1 Fast"},

        {"id": "grok-4-0709", "object": "model", "owned_by": "zai", "name": "Grok 4"},

        {"id": "o4-mini-2025-04-16", "object": "model", "owned_by": "zai", "name": "o4-mini"},

        {"id": "gpt-5-2025-08-07", "object": "model", "owned_by": "zai", "name": "GPT-5"},

        {"id": "gemini-2.5-flash-image", "object": "model", "owned_by": "zai", "name": "Nano Banana"}

    ]

    

    return {

        "object": "list", 

        "data": models

    }

# --- 刷新控制 ---
@app.post("/api/token/refresh/{account_id}")
async def refresh_token_api(account_id: int):
    success = await auto_refresh_service.refresh_token_now(account_id)
    if success:
        return JSONResponse({"success": True, "message": "刷新成功"})
    return JSONResponse(status_code=500, content={"success": False, "message": "刷新失败"})

@app.post("/api/settings/preview-mode")
async def set_preview_mode(request: Request):
    data = await request.json()
    auto_refresh_service.set_preview_mode(data.get("enabled", False))
    return JSONResponse({"success": True})

@app.post("/api/refresh/force")
async def force_refresh_all():
    """强制刷新所有浏览器账号"""
    accounts = db_manager.get_all_accounts(active_only=True)
    browser_accounts = [acc for acc in accounts if acc['token_source'] == 'browser']
    
    if not browser_accounts:
        return JSONResponse(status_code=400, content={
            "success": False,
            "message": "没有浏览器来源的账号"
        })
    
    # 异步刷新所有账号
    for account in browser_accounts:
        asyncio.create_task(auto_refresh_service.refresh_token_now(account['id']))
    
    return JSONResponse({
        "success": True,
        "message": f"已启动刷新任务，将依次刷新 {len(browser_accounts)} 个账号"
    })

@app.get("/api/account/status")
async def get_account_status():
    """获取所有账号的Token有效性状态"""
    accounts = db_manager.get_all_accounts()
    status_list = []
    
    for account in accounts:
        is_valid = provider.verify_token(account['token']) if account.get('token') else False
        status_list.append({
            "id": account['id'],
            "name": account['name'],
            "is_active": account['is_active'],
            "is_valid": is_valid,
            "total_calls": account['total_calls'],
            "token_source": account['token_source'],
            "expires_at": account.get('expires_at'),
            "data_dir": account.get('data_dir')
        })
    
    return JSONResponse({"accounts": status_list})

# --- 辅助函数 ---
@app.post("/api/service/stop")
async def stop_service():
    """停止服务"""
    logger.warning("🛑 收到停止服务请求")
    
    def shutdown():
        import os, signal
        os.kill(os.getpid(), signal.SIGTERM)
    
    # 3秒后停止
    asyncio.get_event_loop().call_later(3, shutdown)
    
    return JSONResponse({
        "success": True,
        "message": "服务将在3秒后停止..."
    })

async def perform_breakpoint_update():
    """启动时检查过期 Token"""
    from datetime import datetime
    try:
        accounts = db_manager.get_all_accounts(active_only=True)
        browser_accounts = [acc for acc in accounts if acc['token_source'] == 'browser']
        
        if not browser_accounts:
            logger.info("ℹ️ 没有浏览器账号需要检查")
            return
        
        logger.info(f"📊 检查 {len(browser_accounts)} 个浏览器账号...")
        
        for acc in browser_accounts:
            if acc.get('expires_at'):
                try:
                    exp = datetime.fromisoformat(acc['expires_at'])
                    remaining = (exp - datetime.now()).total_seconds()
                    
                    if remaining < 3600:
                        logger.warning(f"⚠️ 账号 [{acc['name']}] 即将过期（{int(remaining/60)}分钟后），开始刷新...")
                        await auto_refresh_service.refresh_token_now(acc['id'])
                    else:
                        logger.info(f"✅ 账号 [{acc['name']}] Token有效（{int(remaining/3600)}小时后过期）")
                except Exception as e:
                    logger.error(f"检查账号 [{acc['name']}] 失败: {e}")
    except Exception as e:
        logger.error(f"断点更新失败: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
