# 使用官方 Python 基礎映像
FROM python:3.12-slim
# 安裝構建依賴，包含編譯器和其他必要工具
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    clang \
    meson \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*
# 設置工作目錄
WORKDIR /app

# 複製當前目錄的所有文件到容器內
COPY . /app

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 安裝完依賴後，使用 gunicorn 啟動應用
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
