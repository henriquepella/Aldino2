# Sobe backend (uvicorn, porta 8000) e frontend (next dev, porta 3000) em janelas separadas.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

$backend = "cd '$root\backend'; & '$root\.venv\Scripts\python.exe' -m uvicorn app.main:app --reload --port 8000"
$frontend = "cd '$root\frontend'; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontend

Write-Host "Backend : http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "Login demo: demo@demo.local / demo12345" -ForegroundColor Green
