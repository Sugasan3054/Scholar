FROM python:3.11-slim

WORKDIR /app

# PyMuPDFに必要なシステムの依存関係をインストールする場合がありますが
# slimイメージでもバイナリが提供されていれば不要なことが多いです

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
