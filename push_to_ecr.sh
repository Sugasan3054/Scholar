#!/bin/bash

# ==========================================
# AWS ECR Push Script (Multi-Platform build)
# ==========================================

# 事前設定 (ご自身の環境に合わせて変更してください)
AWS_REGION="ap-northeast-1"
AWS_ACCOUNT_ID="YOUR_12_DIGIT_ACCOUNT_ID" # ← ここをあなたの12桁のAWSアカウントIDに変更
REPO_NAME="scholar-ai-app"

# ECRリポジトリのURL構築
ECR_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Logging in to Amazon ECR..."
# AWS CLIを利用して認証トークンを取得し、Dockerにログイン
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URL}

# ※あらかじめAWSコンソールで ECR リポジトリ (scholar-ai-app) を作成しておく必要があります。
# CLIで作成する場合:
# aws ecr create-repository --repository-name ${REPO_NAME} --region ${AWS_REGION}

echo "=========================================="
echo "Building and Pushing Backend Image (linux/amd64)"
echo "=========================================="
# APIキー等の機密情報は config.py で分離されているため、イメージ内には一切含まれません（安全です）。
# AWS等クラウド環境の必須要件であるマルチプラットフォーム指定(linux/amd64)でビルドします。
docker build --platform linux/amd64 -t ${ECR_URL}/${REPO_NAME}:backend-latest ./backend
docker push ${ECR_URL}/${REPO_NAME}:backend-latest

echo "=========================================="
echo "Building and Pushing Frontend Image (linux/amd64)"
echo "=========================================="
docker build --platform linux/amd64 -t ${ECR_URL}/${REPO_NAME}:frontend-latest ./frontend
docker push ${ECR_URL}/${REPO_NAME}:frontend-latest

echo "Done! Images have been pushed to ECR."
echo "ECR URI (Backend) : ${ECR_URL}/${REPO_NAME}:backend-latest"
echo "ECR URI (Frontend): ${ECR_URL}/${REPO_NAME}:frontend-latest"
