FROM python:3.11-slim

WORKDIR /app

# torch CPU 版运行所需的 OpenMP 运行时
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

# 语义向量模型走国内镜像下载
ENV HF_ENDPOINT=https://hf-mirror.com

# 入口脚本：等待 MySQL -> 种子数据 -> 首次构建向量索引 -> 启动服务
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
