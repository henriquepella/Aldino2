# Espelha o código-fonte de C:\Users\henri\aldino para a pasta do projeto no
# OneDrive/Documentos. Necessário porque o Acesso Controlado a Pastas do Windows
# bloqueia gravações de algumas ferramentas nessa pasta — o PowerShell/robocopy não.
#
# Não copia: .venv, node_modules, .next, caches, banco de dados, dados gerados
# em backend/storage/users (a pasta storage/ em si e o .gitkeep são preservados).
$src = "C:\Users\henri\aldino"
$dst = "C:\Users\henri\OneDrive\Documentos\Projeto Aldino atualizado"

$xd = @(
  "$src\.venv", "$src\.git",
  "$src\frontend\node_modules", "$src\frontend\.next", "$src\frontend\out",
  "$src\backend\storage\users",
  ".pytest_cache", ".ruff_cache", "__pycache__", ".turbo", ".mypy_cache"
)
$xf = @("*.pyc", "*.db", "*.db-shm", "*.db-wal", "*.sqlite3",
        "pip-install.log", ".DS_Store", "Thumbs.db", "*.log")

# /E copia subpastas (inclui vazias); não apaga nada no destino.
robocopy $src $dst /E /R:1 /W:1 /NFL /NDL /NJH /NP /XD $xd /XF $xf
$code = $LASTEXITCODE

# robocopy: 0-7 = sucesso (bit 0=copiou, 1=extras, 2=incompat.); 8+ = erro
if ($code -ge 8) {
  Write-Error "robocopy falhou (código $code)"
  exit 1
}
$n = (Get-ChildItem $dst -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Host "Sincronizado: $n arquivos em $dst  (robocopy código $code)" -ForegroundColor Green
