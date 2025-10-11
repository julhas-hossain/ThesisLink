# ThesisLink Quick Start Script for Windows
# This script helps you set up and run the ThesisLink application

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ThesisLink Setup & Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-Not (Test-Path "backend\.env")) {
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "Please edit backend\.env with your configuration before continuing!" -ForegroundColor Red
    Write-Host "Required: SECRET_KEY, OPENAI_API_KEY, SMTP credentials" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter when you've configured the .env file"
}

# Check if virtual environment exists
if (-Not (Test-Path "backend\venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    Set-Location backend
    python -m venv venv
    Set-Location ..
}

# Activate virtual environment and install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Green
Set-Location backend
& ".\venv\Scripts\Activate.ps1"
pip install -r requirements.txt

# Create uploads directory
if (-Not (Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads" | Out-Null
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the application:" -ForegroundColor Yellow
Write-Host "1. Start the backend API:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "2. In a new terminal, start Celery worker:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   celery -A app.services.scheduler_service.celery_app worker --loglevel=info --pool=solo" -ForegroundColor Gray
Write-Host ""
Write-Host "3. In another terminal, start Celery beat:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   celery -A app.services.scheduler_service.celery_app beat --loglevel=info" -ForegroundColor Gray
Write-Host ""
Write-Host "OR use Docker:" -ForegroundColor Yellow
Write-Host "   docker-compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "Access the API at: http://localhost:8000" -ForegroundColor Green
Write-Host "API Documentation: http://localhost:8000/api/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Note: Make sure Redis is running for Celery to work!" -ForegroundColor Yellow
Write-Host ""
