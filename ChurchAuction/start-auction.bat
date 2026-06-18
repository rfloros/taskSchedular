@echo off
REM ============================================================
REM  Church Auction launcher
REM  Double-click this file to start the auction website.
REM  Keep this window MINIMIZED during the event.
REM  Closing this window stops the server for everyone.
REM ============================================================

cd /d "%~dp0"

echo.
echo  ===========================================================
echo   CHURCH AUCTION SERVER
echo  ===========================================================
echo.
echo   On other devices (phones/tablets/laptops on the SAME WiFi),
echo   open a browser and type one of the addresses below, adding
echo   :8000 at the end.  Example:  http://192.168.1.2:8000
echo.
echo   This laptop's address(es):
ipconfig | findstr /i "IPv4"
echo.
echo   You can also use this laptop's name:  http://%COMPUTERNAME%:8000
echo.
echo   (The first time, Windows may ask to allow Python through the
echo    firewall -- click ALLOW ACCESS on Private networks.)
echo  ===========================================================
echo.

REM Open the app in this laptop's browser.
start "" http://localhost:8000

REM Start the server, reachable by other devices on the WiFi.
".venv\Scripts\python.exe" -m uvicorn web.app:app --host 0.0.0.0 --port 8000

echo.
echo  Server stopped. You can close this window.
pause
