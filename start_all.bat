@echo off

echo Starting Ollama (TinyLLaMA model)...
start cmd /k "ollama run tinyllama"

timeout /t 5

echo Starting Backend (Flask App)...
start cmd /k "cd backend && python app.py"

timeout /t 2

echo Starting Frontend (React Dev Server)...
start cmd /k "cd frontend && npm run dev"

echo All services started.
pause
