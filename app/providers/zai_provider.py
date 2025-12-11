#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zai Provider - 纯HTTP请求，不管理浏览器

架构原则：
- 接收Token，执行HTTP请求
- 不管理Token生命周期
- 不操作浏览器
- 只负责与Zai API通信
"""

import asyncio
import json
import time
import uuid
import urllib.parse
import httpx
import re
import base64
from loguru import logger
from app.core.config import settings
from app.utils.sse_utils import create_chat_completion_chunk
from app.providers.base_provider import BaseProvider

class ZaiProvider(BaseProvider):
    """
    Zai Provider - 只负责HTTP请求，不管理浏览器
    
    架构原则：
    - 接收Token，执行HTTP请求
    - 不管理Token生命周期
    - 不操作浏览器
    - 只负责与Zai API通信
    """
    
    def __init__(self):
        self.base_url = settings.ZAI_BASE_URL
        self.default_model = settings.DEFAULT_MODEL
        
    def verify_token(self, token: str) -> bool:
        """
        验证Token是否有效
        通过请求 /api/v1/chats/?page=1 接口测试
        """
        import cloudscraper
        
        if not token or len(token) < 50:
            return False
            
        scraper = cloudscraper.create_scraper()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            resp = scraper.get(f"{self.base_url}/api/v1/chats/?page=1", headers=headers, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Token验证失败: {e}")
            return False

    async def chat_completion(self, request_data: dict, token: str):
        """
        聊天完成接口 - 遵循 Zai.is 真实 API 流程
        
        支持的模型：
        - gemini-3-pro-image-preview (Nano Banana Pro)
        - gemini-2.5-pro (Gemini 2.5 Pro)
        - claude-opus-4-20250514 (Claude Opus 4)
        - claude-sonnet-4-5-20250929 (Claude Sonnet 4.5)
        - claude-sonnet-4-20250514 (Claude Sonnet 4)
        - claude-haiku-4-5-20251001 (Claude Haiku 4.5)
        - o1-2024-12-17 (o1)
        - o3-pro-2025-06-10 (o3-pro)
        - grok-4-1-fast-reasoning (Grok 4.1 Fast)
        - grok-4-0709 (Grok 4)
        - o4-mini-2025-04-16 (o4-mini)
        - gpt-5-2025-08-07 (GPT-5)
        - gemini-2.5-flash-image (Nano Banana)
        
        流程：
        1. POST /api/v1/chats/new - 创建对话
        2. POST /api/v1/chats/{chat_id} - 更新对话
        3. POST /api/chat/completions - 流式请求AI回复
        4. POST /api/chat/completed - 标记完成
        """
        if not token:
            yield f"data: {json.dumps({'error': 'No token provided'})}\n\n"
            return

        model = request_data.get("model", self.default_model)
        messages = request_data.get("messages", [])
        stream = request_data.get("stream", True)
        
        if not messages:
            yield f"data: {json.dumps({'error': 'No messages provided'})}\n\n"
            return
        
        # 构造消息历史
        user_msg_id = str(uuid.uuid4())
        assistant_msg_id = str(uuid.uuid4())
        timestamp = int(time.time())
        user_content = messages[-1]["content"]
        
        # 根据模型名称设置模型显示名称
        model_display_names = {
            "gemini-3-pro-image-preview": "Nano Banana Pro",
            "gemini-2.5-pro": "Gemini 2.5 Pro",
            "claude-opus-4-20250514": "Claude Opus 4",
            "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5",
            "claude-sonnet-4-20250514": "Claude Sonnet 4",
            "claude-haiku-4-5-20251001": "Claude Haiku 4.5",
            "o1-2024-12-17": "o1",
            "o3-pro-2025-06-10": "o3-pro",
            "grok-4-1-fast-reasoning": "Grok 4.1 Fast",
            "grok-4-0709": "Grok 4",
            "o4-mini-2025-04-16": "o4-mini",
            "gpt-5-2025-08-07": "GPT-5",
            "gemini-2.5-flash-image": "Nano Banana"
        }
        
        model_name = model_display_names.get(model, model)
        
        # 构造 Zai.is 格式的消息对象
        zai_messages = {
            user_msg_id: {
                "id": user_msg_id,
                "parentId": None,
                "childrenIds": [assistant_msg_id],
                "role": "user",
                "content": user_content,
                "timestamp": timestamp,
                "models": [model]
            },
            assistant_msg_id: {
                "parentId": user_msg_id,
                "id": assistant_msg_id,
                "childrenIds": [],
                "role": "assistant",
                "content": "",
                "model": model,
                "modelName": model_name,
                "modelIdx": 0,
                "timestamp": timestamp
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": "https://zai.is",
            "Referer": "https://zai.is/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient(timeout=120) as client:
            try:
                # 步骤1：创建新对话
                logger.debug(f"📝 步骤1: 创建新对话 ({model})...")
                new_chat_payload = {
                    "chat": {
                        "id": "",
                        "title": "新对话",
                        "models": [model],
                        "params": {},
                        "history": {
                            "messages": zai_messages,
                            "currentId": assistant_msg_id
                        },
                        "messages": list(zai_messages.values()),
                        "tags": [],
                        "timestamp": timestamp * 1000
                    },
                    "folder_id": None
                }
                
                resp1 = await client.post(
                    f"{self.base_url}/api/v1/chats/new",
                    json=new_chat_payload,
                    headers=headers
                )
                
                if resp1.status_code == 401:
                    yield f"data: {json.dumps({'error': 'Token无效或已过期'})}\n\n"
                    return
                
                resp1.raise_for_status()
                chat_data = resp1.json()
                chat_id = chat_data.get("id")
                logger.success(f"✅ 对话创建成功: {chat_id}")
                
                # 步骤2：发起流式补全
                logger.debug(f"💬 步骤2: 发起AI请求 ({model})...")
                completion_payload = {
                    "stream": True,
                    "model": model,
                    "messages": [{"role": "user", "content": user_content, "extensions": {}}],
                    "params": {},
                    "tool_servers": [],
                    "features": {
                        "image_generation": False,
                        "code_interpreter": False,
                        "web_search": False
                    },
                    "variables": {
                        "{{CURRENT_DATETIME}}": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "{{CURRENT_DATE}}": time.strftime("%Y-%m-%d"),
                        "{{CURRENT_TIME}}": time.strftime("%H:%M:%S"),
                        "{{CURRENT_WEEKDAY}}": time.strftime("%A"),
                        "{{CURRENT_TIMEZONE}}": "Asia/Shanghai",
                        "{{USER_LANGUAGE}}": "zh-CN"
                    }
                }
                
                # 发起流式请求
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat/completions",
                    json=completion_payload,
                    headers=headers
                ) as resp2:
                    request_id = f"chatcmpl-{uuid.uuid4()}"
                    full_content = ""
                    
                    logger.debug(f"📊 开始接收SSE流数据...")
                    
                    # 读取SSE流
                    async for line in resp2.aiter_lines():
                        if not line or line.startswith(":"):
                            continue
                        
                        if line.startswith("data: "):
                            data_str = line[6:]
                            
                            if data_str == "[DONE]":
                                logger.debug(f"✅ SSE流结束标记收到")
                                break
                            
                            try:
                                chunk_data = json.loads(data_str)
                                
                                # 记录原始响应数据用于调试
                                logger.debug(f"🔍 原始响应数据: {json.dumps(chunk_data, ensure_ascii=False)[:200]}...")
                                
                                # 对于 Zai 的响应格式，没有 choices 字段，直接处理 content
                                if "choices" in chunk_data and chunk_data["choices"]:
                                    # 旧格式，保持兼容性
                                    delta = chunk_data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                else:
                                    # Zai 的新格式：直接在顶层有 content
                                    content = chunk_data.get("content", "")
                                    if not content:
                                        # 检查是否有其他可能的字段
                                        choices = chunk_data.get("choices", [])
                                        if choices and "delta" in choices[0]:
                                            content = choices[0]["delta"].get("content", "")
                                
                                if content:
                                    logger.debug(f"📝 处理内容片段: {content[:200]}...")
                                    
                                    # 检查是否包含图片URL，如果是则记录检测到的图片
                                    if "![image]" in content:
                                        logger.success(f"🖼️ 检测到图片URL: {content}")
                                    
                                    full_content += content
                                    
                                    # 转换为OpenAI格式
                                    openai_chunk = create_chat_completion_chunk(request_id, model, content)
                                    
                                    logger.debug(f"📤 发送SSE块: {json.dumps(openai_chunk, ensure_ascii=False)[:200]}...")
                                    yield f"data: {json.dumps(openai_chunk)}\n\n"
                            except Exception as e:
                                logger.error(f"处理SSE数据时出错: {e}, 数据: {data_str[:100]}")
                                # 继续处理其他数据
                                pass
                    
                    # 发送结束标记
                    final_chunk = create_chat_completion_chunk(request_id, model, "", "stop")
                    yield f"data: {json.dumps(final_chunk)}\n\n"
                    yield "data: [DONE]\n\n"
                    
                    # 检查是否包含图片并记录
                    if "![image]" in full_content:
                        logger.success(f"✅ AI响应完成，包含图片，共 {len(full_content)} 字符")
                    else:
                        logger.success(f"✅ AI响应完成，共 {len(full_content)} 字符")

            except Exception as e:
                logger.error(f"API请求失败: {e}")
                error_chunk = create_chat_completion_chunk("error", model, f"Error: {str(e)}")
                yield f"data: {json.dumps(error_chunk)}\n\n"
                yield "data: [DONE]\n\n"
    
    def _extract_ai_response(self, data):
        """从Zai API响应中提取AI回复"""
        try:
            # 根据实际响应结构调整
            # 这里使用通用逻辑
            if isinstance(data, dict):
                if 'choices' in data and data['choices']:
                    return data['choices'][0].get('message', {}).get('content', '')
                elif 'content' in data:
                    return data['content']
            
            # 默认返回成功消息
            return "Zai API 调用成功。响应结构可能需要根据实际API调整。"
            
        except Exception as e:
            logger.error(f"提取AI回复失败: {e}")
            return "未能提取AI回复"
