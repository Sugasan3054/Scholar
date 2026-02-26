$ErrorActionPreference = "Stop"

# ==========================================
# AWS ECR Push Script for Windows PowerShell
# ==========================================

# 事前設定 (ご自身の環境に合わせて変更してください)
$AwsRegion = "ap-northeast-1"
$AwsAccountId = "417418331277" # ← ここをあなたの12桁のAWSアカウントIDに変更
$RepoName = "scholar-ai-app"

$EcrUrl = "${AwsAccountId}.dkr.ecr.${AwsRegion}.amazonaws.com"

Write-Host "Logging in to Amazon ECR..." -ForegroundColor Cyan
aws ecr get-login-password --region $AwsRegion | docker login --username AWS --password-stdin $EcrUrl

Write-Host "=========================================="
Write-Host "Building and Pushing Backend Image (linux/amd64)" -ForegroundColor Cyan
Write-Host "=========================================="
# APIキーは .env に分離されているため、イメージ内には含まれません（安全です）。
# App Runnerが標準要件とする linux/amd64 でビルドします。
docker build --platform linux/amd64 -t "${EcrUrl}/${RepoName}:backend-latest" ./backend
docker push "${EcrUrl}/${RepoName}:backend-latest"

Write-Host "=========================================="
Write-Host "Building and Pushing Frontend Image (linux/amd64)" -ForegroundColor Cyan
Write-Host "=========================================="
docker build --platform linux/amd64 -t "${EcrUrl}/${RepoName}:frontend-latest" ./frontend
docker push "${EcrUrl}/${RepoName}:frontend-latest"

Write-Host "Done! Images have been pushed to ECR." -ForegroundColor Green
Write-Host "ECR URI (Backend) : ${EcrUrl}/${RepoName}:backend-latest"
Write-Host "ECR URI (Frontend): ${EcrUrl}/${RepoName}:frontend-latest"
