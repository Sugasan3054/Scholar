FROM python:3.11-slim

WORKDIR /app

# PyMuPDFに必要なシステムの依存関係をインストールする場合がありますが
# slimイメージでもバイナリが提供されていれば不要なことが多いです

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# AWS ECR等のクラウド用: コンテナ内にソースコードをすべてコピーする
COPY . .

ENV PORT=8000
EXPOSE $PORT

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --reload"]
