FROM python:3.11-slim

WORKDIR /app

# プロジェクトルートの要件ファイル（frontend + backend統合版）をコピー
COPY requirements.txt .

# 依存関係のインストール（必要に応じてコンパイラ等のシステムパッケージを追加可能）
RUN pip install --no-cache-dir -r requirements.txt

# AWS ECR等のクラウド用: コンテナ内に全ソースコードをコピーする
COPY . .

# NLTKデータの事前ダウンロード等が必要な場合のプレースホルダ
# RUN python -m nltk.downloader punkt

ENV PORT=8501
EXPOSE $PORT

# Gradioを起動する
CMD ["python", "frontend/app.py"]
