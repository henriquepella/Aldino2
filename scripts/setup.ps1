# Instala backend (venv + deps) e frontend (npm), gera dados de demonstração e
# popula o projeto de demonstração. Windows / PowerShell.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "==> Backend: ambiente virtual + dependências" -ForegroundColor Cyan
if (-not (Test-Path "$root\.venv")) { python -m venv "$root\.venv" }
& "$root\.venv\Scripts\python.exe" -m pip install --upgrade pip | Out-Null
& "$root\.venv\Scripts\python.exe" -m pip install -r "$root\backend\requirements.txt"

Write-Host "==> Dados de demonstração" -ForegroundColor Cyan
& "$root\.venv\Scripts\python.exe" "$root\sample_data\generate_demo.py"

if (-not (Test-Path "$root\.env")) { Copy-Item "$root\.env.example" "$root\.env" }

Write-Host "==> Seed do projeto de demonstração" -ForegroundColor Cyan
& "$root\.venv\Scripts\python.exe" "$root\scripts\seed_demo.py"

Write-Host "==> Frontend: dependências" -ForegroundColor Cyan
Push-Location "$root\frontend"
if (-not (Test-Path "$root\frontend\.env.local")) {
  "NEXT_PUBLIC_API_URL=http://localhost:8000/api" | Out-File -Encoding utf8 ".env.local"
}
npm install
Pop-Location

Write-Host ""
Write-Host "Pronto. Para iniciar:  .\scripts\dev.ps1" -ForegroundColor Green
Write-Host "O app abre direto na lista de projetos (sem login)." -ForegroundColor Green
