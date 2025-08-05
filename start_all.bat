@echo off
echo Starting Backend...
start cmd /k "cd backend && python app.py"

timeout /t 2

echo Starting Frontend...
start cmd /k "cd frontend && npm run dev"

echo All services started.
pause
