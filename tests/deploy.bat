@echo off
REM AI Video Generator Deployment Script for Akash Network (Windows)

setlocal enabledelayedexpansion

REM Configuration
set DOCKER_USERNAME=shivapreetham
set IMAGE_NAME=ai-video-generator
set TAG=latest
set FULL_IMAGE=%DOCKER_USERNAME%/%IMAGE_NAME%:%TAG%

echo 🚀 AI Video Generator Deployment Script
echo ========================================

REM Step 1: Build Docker image
echo 📦 Building Docker image...
docker build -t %FULL_IMAGE% .

if %errorlevel% neq 0 (
    echo ❌ Docker build failed!
    exit /b 1
)

echo ✅ Docker image built successfully: %FULL_IMAGE%

REM Step 2: Test the image locally
echo 🧪 Testing Docker image locally...
docker run -d -p 8000:8000 --name ai-video-test %FULL_IMAGE%

REM Wait for container to start
timeout /t 10 /nobreak >nul

REM Test the health endpoint
curl -f http://localhost:8000/health
if %errorlevel% equ 0 (
    echo ✅ Local test passed!
    docker stop ai-video-test
    docker rm ai-video-test
) else (
    echo ❌ Local test failed!
    docker logs ai-video-test
    docker stop ai-video-test
    docker rm ai-video-test
    exit /b 1
)

REM Step 3: Push to Docker Hub
echo 📤 Pushing to Docker Hub...
echo Please login to Docker Hub first:
docker login

docker push %FULL_IMAGE%

if %errorlevel% neq 0 (
    echo ❌ Docker push failed!
    exit /b 1
)

echo ✅ Image pushed successfully to Docker Hub!

REM Step 4: Ready for Akash deployment
echo 🌐 Ready to deploy to Akash Network!
echo.
echo Next steps:
echo 1. Update akash-docker-deploy.yaml with your Docker Hub username if needed
echo 2. Set your API keys in the YAML file
echo 3. Deploy using: akash tx deployment create akash-docker-deploy.yaml --from ^<your-key^> --chain-id akashnet-2
echo.
echo Docker image ready: %FULL_IMAGE%
echo ✅ Deployment preparation complete!

pause