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
Write-Host "Building and Pushing Monolith Image (linux/amd64)" -ForegroundColor Cyan
Write-Host "=========================================="
# APIキーは .env に分離されているため、イメージ内には含まれません（安全です）。
# App Runnerが標準要件とする linux/amd64 でビルドします。
docker build --platform linux/amd64 -t "${EcrUrl}/${RepoName}:latest" .
docker push "${EcrUrl}/${RepoName}:latest"

Write-Host "Done! Image has been pushed to ECR." -ForegroundColor Green
Write-Host "ECR URI : ${EcrUrl}/${RepoName}:latest"
