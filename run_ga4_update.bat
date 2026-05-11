@echo off
cd /d "%~dp0"

py .\scripts\fetch_ga4.py
py .\scripts\fetch_trends.py
py .\scripts\fetch_search_console.py

echo.
echo Dashboard data updated successfully.
