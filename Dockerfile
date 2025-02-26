FROM python:3.9-slim

WORKDIR /app

# 複製依賴清單
COPY requirements.txt .

# 安裝套件
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 設定環境變數
ENV FLASK_APP=run.py
ENV FLASK_DEBUG=0

# 開放 5000 埠
EXPOSE 5000

# 啟動應用程式
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]