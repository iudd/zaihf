# 使用官方 Python 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    wget \
    gnupg \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器
RUN python -m playwright install chromium
RUN python -m playwright install-deps

# 创建必要的目录
RUN mkdir -p /app/data /app/media /app/static /app/templates /app/accounts_data /app/zai_user_data

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright
ENV HF_SPACE=true
ENV PORT=7860

# 暴露端口
EXPOSE 7860

# 启动命令
CMD ["python", "app.py"]