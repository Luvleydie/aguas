# 1. Configurar Backend (Python)
if (-Not (Test-Path ".venv")) {
    Write-Host "Creando entorno virtual de Python..."
    python -m venv .venv
    Write-Host "Instalando dependencias de Python..."
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
}

# 2. Configurar Frontend (Node)
cd frontend
Write-Host "Instalando dependencias de Node..."
npm install
Write-Host "Construyendo aplicación de React..."
npm run build
cd ..

# 3. Levantar Servidor
Write-Host "Iniciando servidor de Uvicorn..."
$env:HIDROALERTA_FRONTEND_DIR="$PWD\frontend\out"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
