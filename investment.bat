@echo off
REM Change to project directory
cd /d "D:\AK\Projects\Portfolio Analysis"

REM Start FastAPI in the background
start "" "C:\Users\91890\.conda\envs\myenv\python.exe" -m uvicorn main:app --reload

REM Wait a few seconds to let the server start
timeout /t 5 /nobreak

REM Open default browser to FastAPI URL
start "" "http://127.0.0.1:8000/dashboard"

pause
