cd frontend
npm install
npm run build
cd ..
$env:HIDROALERTA_FRONTEND_DIR="$PWD\frontend\out"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
