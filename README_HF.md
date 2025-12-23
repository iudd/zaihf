# 🚀 Zai-2API: Hugging Face Space 部署版

[![Hugging Face Spaces](https://img.shields.io/badge/🤖%20Hugging%20Face-Spaces-blue.svg)](https://huggingface.co/spaces)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-green?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

---

## 📖 简介

这是 **Zai-2API** 的 Hugging Face Space 部署版本，提供了一个无需本地安装、即开即用的 Zai.is API 代理服务。

> **🌟 主要功能**: 将 Zai.is 平台的 AI 模型转换为 OpenAI 兼容的 API 接口，支持自动刷新 Token、多账号管理、图片代理等高级功能。

---

## 🎯 快速开始

### 1. 访问 Space

点击以下链接访问已部署的 Space：

```
https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
```

### 2. 添加 Zai.is 账号

1. 在 Space 页面中，点击 **"🌐 启动浏览器登录"** 按钮
2. 在弹出的浏览器窗口中完成 Discord 登录
3. 登录成功后关闭浏览器，Token 将自动保存

### 3. 使用 API

Space 启动后，你可以使用以下 API：

- **模型列表**: `GET /v1/models`
- **对话接口**: `POST /v1/chat/completions`
- **账号管理**: 通过 Web 界面管理多个 Zai.is 账号

---

## 🔧 API 使用示例

### Python 客户端

```python
import openai

# 配置 OpenAI 客户端指向 Hugging Face Space
client = openai.OpenAI(
    api_key="1",  # 默认密钥
    base_url="https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/v1"
)

# 发送聊天请求
response = client.chat.completions.create(
    model="gpt-5-2025-08-07",
    messages=[
        {"role": "user", "content": "你好，请介绍一下自己"}
    ]
)

print(response.choices[0].message.content)
```

### cURL 示例

```bash
curl -X POST "https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer 1" \
     -d '{
           "model": "gpt-5-2025-08-07",
           "messages": [{"role": "user", "content": "你好"}]
         }'
```

---

## 🛠️ 技术特性

### 🌐 Web 界面

- **账号管理**: 添加、删除、切换 Zai.is 账号
- **Token 状态**: 实时显示 Token 有效性
- **使用日志**: 查看 API 调用历史
- **图片代理**: 自动处理 AI 生成的图片

### 🔄 自动化功能

- **Token 自动刷新**: 7×24 小时自动保活
- **浏览器自动登录**: 无需手动干预
- **负载均衡**: 多账号自动轮询
- **健康监控**: 自动检测账号状态

### 🛡️ 安全特性

- **反检测技术**: 绕过平台自动化检测
- **持久化存储**: 浏览器状态本地保存
- **跨域支持**: 解决图片显示问题

---

## 📋 支持的模型

| 模型 ID | 显示名称 | 提供商 | 能力 |
|---------|----------|--------|------|
| `gpt-5-2025-08-07` | GPT-5 | OpenAI | 最新 GPT-5 模型 |
| `claude-opus-4-20250514` | Claude Opus 4 | Anthropic | 最强推理模型 |
| `claude-sonnet-4-5-20250929` | Claude Sonnet 4.5 | Anthropic | 平衡型智能助手 |
| `gemini-3-pro-image-preview` | Nano Banana Pro | Google | 多模态视觉模型 |
| `o3-pro-2025-06-10` | o3-pro | OpenAI | 推理优化版本 |
| `grok-4-1-fast-reasoning` | Grok 4.1 Fast | xAI | 快速推理版本 |
| `gemini-2.5-pro` | Gemini 2.5 Pro | Google | 专业文本处理 |
| `claude-haiku-4-5-20251001` | Claude Haiku 4.5 | Anthropic | 快速轻量级模型 |
| `o1-2024-12-17` | o1 | OpenAI | 数学推理专用 |
| `o4-mini-2025-04-16` | o4-mini | OpenAI | 轻量快速版本 |
| `grok-4-0709` | Grok 4 | xAI | 标准版本 |
| `gemini-2.5-flash-image` | Nano Banana | Google | 快速图像处理 |

---

## 🚨 注意事项

### 使用限制

1. **账号有效性**: 必须使用有效的 Zai.is 账号
2. **请求频率**: 避免过高频率请求，防止账号被封
3. **资源限制**: Hugging Face Space 有计算资源限制
4. **数据隐私**: 请勿发送敏感信息

### 常见问题

**Q: 浏览器登录失败怎么办？**
A: 确保浏览器能够正常访问 zai.is，并完成 Discord 验证。

**Q: Token 频繁过期？**
A: 系统会自动刷新，但请确保网络连接稳定。

**Q: API 响应缓慢？**
A: 可以添加多个账号实现负载均衡，提高响应速度。

---

## 📚 本地部署

如果你想在本地部署此项目，可以：

1. 克隆仓库：
   ```bash
   git clone https://github.com/YOUR_USERNAME/zai.is-2api-python.git
   cd zai.is-2api-python
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. 运行服务：
   ```bash
   python app.py
   ```

---

## 📞 技术支持

- **项目主页**: [GitHub 仓库](https://github.com/YOUR_USERNAME/zai.is-2api-python)
- **问题反馈**: [GitHub Issues](https://github.com/YOUR_USERNAME/zai.is-2api-python/issues)
- **Hugging Face Space**: [Space 主页](https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME)

---

## ⚖️ 免责声明

本项目仅供技术研究和学习交流使用。使用者应对自己的行为负全部责任。开发者不对因使用本项目而产生的任何直接或间接损失负责。

> **技术本身是中立的，但技术的使用应有边界。让我们共同维护一个健康、合法的技术生态。** 🌱

---

## 🌟 致谢

感谢以下开源项目和社区的支持：

- **Hugging Face** - 提供 Spaces 平台
- **FastAPI** - 高性能 Web 框架
- **Playwright** - 浏览器自动化工具
- **Zai.is** - 提供优质的 AI 服务

---

**最后更新**: 2025年12月23日  
**版本**: 2.0.0 (Hugging Face Space)