@echo off
title Nirvana Intelligence Platform - Startup
color 0B
echo.
echo  ============================================================
echo   NIRVANA INTELLIGENCE PLATFORM - STARTING UP
echo  ============================================================
echo.

:: Step 1: Train / refresh ML model
echo  [1/3] Training ML model from latest telemetry...
python model.py
echo.

:: Step 2: Start Serial Reader in background (ESP32 on COM5)
echo  [2/3] Starting ESP32 serial reader on COM5...
start "Nirvana Serial Reader" cmd /k "python serial_reader.py COM5"
timeout /t 2 /nobreak >nul

:: Step 3: Start Flask server
echo  [3/3] Starting Flask server...
echo.
echo  ============================================================
echo   Dashboard: http://127.0.0.1:5000/dashboard
echo   Landing:   http://127.0.0.1:5000
echo  ============================================================
echo.
echo  Press CTRL+C to stop the server.
echo.
python app.py
