@echo off
setlocal enabledelayedexpansion
title SHΔDØW-EXCISION: UNIVERSAL CONTROL
color 0B

echo ==========================================
echo    SHADOW-EXCISION INTERACTIVE MODULE
echo ==========================================
echo.

:: طلب معرف العملية من المستخدم
set /p TARGET_PID="[?] Enter Target PID: "

echo.
echo Select Action for PID %TARGET_PID%:
echo [1] Suspend (Freeze)
echo [2] Terminate (Kill)
echo [3] Dump Memory (Extract)
echo [4] Exit
echo.
set /p CHOICE="[>] Choose option (1-4): "

if "%CHOICE%"=="1" (
    python Shadow-Excision.py --pid %TARGET_PID% --action suspend
)
if "%CHOICE%"=="2" (
    python Shadow-Excision.py --pid %TARGET_PID% --action terminate
)
if "%CHOICE%"=="3" (
    set /p TARGET_ADDR="[?] Enter Memory Address (e.g., 0x7ffa12340000): "
    set /p DUMP_SIZE="[?] Enter Size to dump (default 4096): "
    python Shadow-Excision.py --pid %TARGET_PID% --action dump --addr !TARGET_ADDR! --size !DUMP_SIZE!
)
if "%CHOICE%"=="4" exit

echo.
echo ==========================================
echo Task Finished.
pause
