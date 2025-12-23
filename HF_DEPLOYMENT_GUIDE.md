# 🚀 Hugging Face Space 部署指南

## 📋 概述

本指南详细说明如何将 ZAI-2API 项目部署到 Hugging Face Space，实现零配置、即开即用的 API 服务。

## 🔧 修改清单

### 1. 新增文件

| 文件名 | 作用 | 说明 |
|--------|------|------|
| `app.py` | Hugging Face Space 入口点 | 提供 HF Space 特定的启动逻辑 |
| `README_HF.md` | HF Space 专用文档 | 针对云端部署的使用指南 |
| `.hf_space_config.yml` | HF Space 配置 | 定义 Space 的基本信息和设置 |
| `Dockerfile` | 容器构建配置 | 确保 HF Space 正确构建和运行 |
| `HF_DEPLOYMENT_GUIDE.md` | 本文件 | 部署指南 |

### 2. 修改的文件

| 文件名 | 修改内容 | 目的 |
|--------|----------|------|
| `app/core/config.py` | 添加 HF Space 特定配置 | 适应云端环境 |
| `main.py` | 调整启动逻辑和 URL 生成 | 支持 HF Space 的 URL 格式 |
| `requirements.txt` | 更新依赖版本和添加新依赖 | 确保所有依赖在 HF Space 上可用 |
| `README.md` | 添加 HF Space 部署章节 | 提供多种部署方式选择 |

## 🚀 部署步骤

### 1. 准备 GitHub 仓库

1. 将所有修改提交到你的 GitHub 仓库
2. 确保仓库是公开的（HF Space 通常不支持私有仓库模板）

### 2. 创建 Hugging Face Space

1. 访问 [Hugging Face Spaces](https://huggingface.co/spaces)
2. 点击 "Create new Space"
3. 选择 "Duplicate this space"
4. 输入你的 GitHub 仓库地址
5. 或者点击 [直接使用模板](https://huggingface.co/new-space?template=lza6/zai.is-2api-python)

### 3. 配置 Space

1. **Space 设置**:
   - Space 名称：例如 `my-zai-api`
   - 可见性：公开（推荐）
   - 硬件：CPU basic（免费）或 CPU upgrade（付费）
   - SDK：Docker

2. **环境变量**（可选）:
   - `API_MASTER_KEY`: 自定义 API 密钥（默认为 "1"）
   - `PORT`: 服务端口（默认为 7860）

### 4. 等待部署

- Space 会自动构建和部署
- 通常需要 2-5 分钟完成
- 构建日志可以在 Space 页面查看

## 🔍 验证部署

1. 访问你的 Space URL
2. 检查是否能看到仪表板界面
3. 尝试添加一个 Zai.is 账号
4. 测试 API 接口是否正常工作

## 📝 使用指南

### 添加账号

1. 在 Space 页面点击 "🌐 启动浏览器登录"
2. 在弹出窗口完成 Discord 登录
3. 关闭浏览器，Token 自动保存

### 使用 API

```bash
curl -X POST "https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer 1" \
     -d '{
           "model": "gpt-5-2025-08-07",
           "messages": [{"role": "user", "content": "你好"}]
         }'
```

## ⚠️ 注意事项

### 资源限制

- Hugging Face Space 有 CPU 和内存限制
- 并发请求过多可能导致服务缓慢
- 建议添加多个账号实现负载均衡

### 数据持久性

- 账号数据存储在 Space 的持久化存储中
- 重启 Space 不会丢失数据
- 但删除 Space 会丢失所有数据

### 安全性

- HF Space 默认公开访问
- 建议使用 API Master Key 进行访问控制
- 不要在 Space 上存储敏感信息

## 🛠️ 故障排除

### 构建失败

1. 检查 `requirements.txt` 是否正确
2. 查看 Space 的构建日志
3. 确认 Dockerfile 是否正确配置

### 运行时错误

1. 查看 Space 的运行日志
2. 检查浏览器自动登录是否成功
3. 确认 Token 是否有效

### 性能问题

1. 添加更多账号实现负载均衡
2. 升级到更高配置的硬件
3. 减少并发请求数量

## 📈 高级配置

### 自定义域名

在 Space 设置中可以配置自定义域名：
1. 进入 Space 的设置页面
2. 添加自定义域名
3. 配置 DNS 记录
4. 启用 HTTPS

### CI/CD 集成

可以设置 GitHub Actions 自动更新 Space：
1. 在 GitHub 仓库中添加 Secrets
2. 创建 GitHub Actions 工作流
3. 配置自动部署脚本

---

## 🤝 贡献

如果你有任何问题或建议，欢迎：

1. 在 GitHub 上提交 Issue
2. 提交 Pull Request 改进代码
3. 在 Hugging Face 社区讨论

---

**最后更新**: 2025年12月23日  
**版本**: 2.0.0 (Hugging Face Space)