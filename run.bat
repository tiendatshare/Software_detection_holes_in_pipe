@echo off
cd /d "%~dp0"
echo Dang khoi dong Pipe Defect Inspector...
venv\Scripts\python.exe main.py
if %errorlevel% neq 0 (
    echo.
    echo Loi khi chay app. Nhan phim bat ky de dong...
    pause > nul
)
