@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0import_sqlite_data.ps1" %*
if errorlevel 1 pause
