import re
import json
import urllib.parse
from typing import Optional

def extract_token_from_text(text: str) -> Optional[str]:
    """
    从 cURL、HAR、请求头或 Cookie 字符串中提取 Bearer Token 或 token 字段。
    增强版本，支持更多格式的 Token 提取。
    """
    if not text:
        return None
        
    text = text.strip()
    
    # 1. 匹配 Authorization: Bearer ...
    match = re.search(r'Bearer\s+([a-zA-Z0-9\.\-_]+)', text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # 2. 匹配 Cookie 中的 token=...
    match = re.search(r'token=([a-zA-Z0-9\.\-_]+)', text)
    if match:
        return match.group(1)
    
    # 3. 匹配 localStorage 格式 {"token": "..."}
    match = re.search(r'"token"\s*:\s*"([a-zA-Z0-9\.\-_]+)"', text)
    if match:
        return match.group(1)
    
    # 4. 暴力匹配 JWT (eyJ...)
    # 查找所有 eyJ 开头的长字符串
    candidates = re.findall(r'(eyJ[a-zA-Z0-9\.\-_]{50,})', text)
    for c in candidates:
        if c.count('.') >= 2:  # JWT 至少有两个点
            return c
    
    # 5. 尝试匹配 cURL 中的各种格式
    curl_patterns = [
        r'-H\s+["\']authorization:\s*Bearer\s+([a-zA-Z0-9\.\-_]+)["\']',
        r'-H\s+["\']Authorization:\s*Bearer\s+([a-zA-Z0-9\.\-_]+)["\']',
        r'--header\s+["\']authorization:\s*Bearer\s+([a-zA-Z0-9\.\-_]+)["\']',
        r'--header\s+["\']Authorization:\s*Bearer\s+([a-zA-Z0-9\.\-_]+)["\']'
    ]
    
    for pattern in curl_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    # 6. 尝试解析 JSON 格式
    try:
        json_data = json.loads(text)
        if isinstance(json_data, dict):
            for key in ['token', 'access_token', 'auth_token', 'bearer_token', 'authToken']:
                if key in json_data and json_data[key]:
                    token_value = json_data[key]
                    if isinstance(token_value, str) and len(token_value) > 50:
                        return token_value
    except:
        pass
    
    # 7. 直接匹配完整的 JWT
    if text.startswith("eyJ") and len(text) > 100:
        if re.match(r'^[a-zA-Z0-9\.\-_]+$', text):
            return text
    
    return None