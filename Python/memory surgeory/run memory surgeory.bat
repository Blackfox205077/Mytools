@echo off
title SHΔDØW CORE - Memory Surgeon Control Center v8.0
color 0A
cls

echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║     SHΔDØW CORE - Memory Surgeon Control Center v8.0               ║
echo ║     Ultimate Edition - PPL Detection ^| Hollowing ^| Entropy       ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.

:: ============================================================================
:: التحقق من وجود Python
:: ============================================================================
echo [*] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.7 or higher from https://python.org
    echo.
    pause
    exit /b 1
)
echo [✓] Python found: 
python --version
echo.

:: ============================================================================
:: التحقق من المكتبات المطلوبة
:: ============================================================================
echo [*] Checking required libraries...
echo.

:: التحقق من psutil
echo [*] Checking psutil...
python -c "import psutil" 2>nul
if errorlevel 1 (
    echo [!] psutil not found. Installing...
    pip install psutil
    if errorlevel 1 (
        echo [ERROR] Failed to install psutil
        pause
        exit /b 1
    )
) else (
    echo [✓] psutil found
)

:: التحقق من yara-python
echo [*] Checking yara-python...
python -c "import yara" 2>nul
if errorlevel 1 (
    echo [!] yara-python not found. Installing...
    pip install yara-python
    if errorlevel 1 (
        echo [ERROR] Failed to install yara-python
        echo [!] You may need to install Visual C++ Build Tools
        pause
        exit /b 1
    )
) else (
    echo [✓] yara-python found
)

:: التحقق من customtkinter
echo [*] Checking customtkinter...
python -c "import customtkinter" 2>nul
if errorlevel 1 (
    echo [!] customtkinter not found. Installing...
    pip install customtkinter
    if errorlevel 1 (
        echo [ERROR] Failed to install customtkinter
        pause
        exit /b 1
    )
) else (
    echo [✓] customtkinter found
)

echo.
echo [✓] All required libraries are installed
echo.

:: ============================================================================
:: التحقق من صلاحيات المسؤول
:: ============================================================================
net session >nul 2>&1
if errorlevel 1 (
    echo [⚠] WARNING: Not running as Administrator!
    echo [⚠] Some memory regions may not be accessible.
    echo [⚠] PPL Detection may have limited access.
    echo [⚠] For full functionality, please run as Administrator.
    echo.
    choice /C YN /M "Continue anyway? "
    if errorlevel 2 (
        echo.
        echo [*] Exiting...
        pause
        exit /b 0
    )
) else (
    echo [✓] Running with Administrator privileges
    echo [✓] PPL Detection and memory access: FULL
)

echo.

:: ============================================================================
:: التحقق من وجود الملفات
:: ============================================================================
echo [*] Checking for required files...
echo.

:: التحقق من الملف الرئيسي (الإصدار V8.0)
if exist "memory_surgeon_v80.py" (
    echo [✓] Main tool file found: memory_surgeon_v80.py
) else if exist "memory_surgeon_v8.py" (
    echo [✓] Main tool file found: memory_surgeon_v8.py
    set MAIN_FILE=memory_surgeon_v8.py
) else if exist "memory_surgeon.py" (
    echo [✓] Main tool file found: memory_surgeon.py
    set MAIN_FILE=memory_surgeon.py
) else (
    echo [ERROR] Main tool file not found!
    echo Please make sure one of these files exists:
    echo   - memory_surgeon_v80.py
    echo   - memory_surgeon_v8.py
    echo   - memory_surgeon.py
    echo.
    pause
    exit /b 1
)

:: التحقق من ملف الواجهة الرسومية
if exist "gui_interface_v80.py" (
    echo [✓] GUI interface file found: gui_interface_v80.py
    set GUI_FILE=gui_interface_v80.py
) else if exist "gui_interface_v8.py" (
    echo [✓] GUI interface file found: gui_interface_v8.py
    set GUI_FILE=gui_interface_v8.py
) else if exist "gui_interface.py" (
    echo [✓] GUI interface file found: gui_interface.py
    set GUI_FILE=gui_interface.py
) else (
    echo [ERROR] GUI interface file not found!
    echo Please make sure one of these files exists:
    echo   - gui_interface_v80.py
    echo   - gui_interface_v8.py
    echo   - gui_interface.py
    echo.
    pause
    exit /b 1
)

echo.

:: ============================================================================
:: إنشاء المجلدات اللازمة
:: ============================================================================
echo [*] Creating required directories...
if not exist "Forensics_Reports" mkdir Forensics_Reports
if not exist "Forensics_Dumps" mkdir Forensics_Dumps
echo [✓] Directories created: Forensics_Reports, Forensics_Dumps
echo.

:: ============================================================================
:: عرض معلومات الإصدار والمميزات
:: ============================================================================
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                    MEMORY SURGEON PRO V8.0                          ║
echo ║                    ULTIMATE EDITION FEATURES                        ║
echo ╠══════════════════════════════════════════════════════════════════════╣
echo ║  ✓ PPL Detection           - Protected Process Light detection     ║
echo ║  ✓ Process Hollowing       - Memory vs Disk comparison             ║
echo ║  ✓ Entropy Analysis        - High entropy = injected code          ║
echo ║  ✓ YARA with Context       - Pattern detection with surroundings   ║
echo ║  ✓ Network Indicators      - IPs, URLs, Domains highlighting       ║
echo ║  ✓ Real-time Monitoring    - Live system statistics                ║
echo ║  ✓ Forensic Reports        - JSON reports with all details         ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.

:: ============================================================================
:: عرض خيارات التشغيل
:: ============================================================================
echo SELECT LAUNCH MODE:
echo.
echo [1] Launch GUI Interface (Recommended)
echo [2] Launch Console Mode (CLI)
echo [3] Launch with Admin Check Only
echo [4] Exit
echo.
choice /C 1234 /N /M "Enter your choice (1-4): "

if errorlevel 4 goto :exit
if errorlevel 3 goto :admin_check
if errorlevel 2 goto :console_mode
if errorlevel 1 goto :gui_mode

:: ============================================================================
:: الوضع 1: تشغيل الواجهة الرسومية
:: ============================================================================
:gui_mode
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                    LAUNCHING GUI INTERFACE                          ║
echo ║                    SHΔDØW CORE V8.0                                 ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo [*] GUI Interface: %GUI_FILE%
echo [*] Main Tool: %MAIN_FILE%
echo.
echo [*] Starting GUI...
echo [*] Please wait...
echo.

:: تشغيل الواجهة الرسومية
start /b python %GUI_FILE%

:: التحقق من نجاح التشغيل
if errorlevel 1 (
    echo [ERROR] Failed to launch GUI interface!
    echo.
    pause
    exit /b 1
)

echo [✓] SHΔDØW CORE is running...
echo [*] The GUI window should appear shortly
echo.
echo [*] To close the tool, close the GUI window
echo.

:: انتظار حتى يتم إغلاق النافذة
:wait_gui
timeout /t 2 /nobreak >nul
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "python.exe" >nul
if not errorlevel 1 goto :wait_gui

echo.
echo [✓] SHΔDØW CORE has been closed
goto :summary

:: ============================================================================
:: الوضع 2: وضع سطر الأوامر (CLI)
:: ============================================================================
:console_mode
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                    CONSOLE MODE - MEMORY SURGEON V8.0               ║
echo ║                    Command Line Interface                           ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo [*] Running console mode...
echo [*] Main Tool: %MAIN_FILE%
echo.
echo SELECT SCAN TYPE:
echo.
echo [1] Full System Scan (Recommended)
echo [2] Scan Specific Process
echo [3] Process Hollowing Analysis Only
echo [4] Back to Main Menu
echo.
choice /C 1234 /N /M "Enter your choice (1-4): "

if errorlevel 4 goto :console_mode
if errorlevel 3 goto :hollowing_only
if errorlevel 2 goto :scan_process
if errorlevel 1 goto :full_scan

:full_scan
echo.
echo [*] Starting full system scan...
echo [*] This may take several minutes...
echo.
python %MAIN_FILE% --scan
goto :console_done

:scan_process
echo.
set /p PID="Enter Process PID: "
echo.
echo [*] Scanning process PID: %PID%
echo.
python %MAIN_FILE% --pid %PID%
goto :console_done

:hollowing_only
echo.
set /p PID="Enter Process PID: "
echo.
echo [*] Analyzing process PID: %PID% for hollowing...
echo.
python %MAIN_FILE% --hollowing %PID%
goto :console_done

:console_done
echo.
echo [*] Console scan completed.
echo.
pause
goto :console_mode

:: ============================================================================
:: الوضع 3: فحص الصلاحيات فقط
:: ============================================================================
:admin_check
cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                    ADMINISTRATOR PRIVILEGES CHECK                   ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
net session >nul 2>&1
if errorlevel 1 (
    echo [❌] NOT running as Administrator!
    echo.
    echo [⚠] Limitations without Admin:
    echo     - Cannot read protected process memory
    echo     - Limited PPL detection
    echo     - Some memory regions inaccessible
    echo     - Hollowing detection may be incomplete
    echo.
    echo [*] To run as Administrator:
    echo     1. Right-click on this batch file
    echo     2. Select "Run as administrator"
    echo.
) else (
    echo [✓] Running as Administrator!
    echo.
    echo [✓] Full capabilities available:
    echo     - Full memory access
    echo     - Complete PPL detection
    echo     - All memory regions readable
    echo     - Accurate hollowing detection
    echo.
)
pause
goto :main_menu

:: ============================================================================
:: الملخص النهائي
:: ============================================================================
:summary
echo.
echo ╔══════════════════════════════════════════════════════════════════════╗
echo ║                    SCAN SUMMARY                                      ║
echo ╚══════════════════════════════════════════════════════════════════════╝
echo.
echo [*] Reports saved in: Forensics_Reports\
echo [*] Memory dumps saved in: Forensics_Dumps\
echo.
echo [*] To view reports:
echo     - JSON format: Open with any text editor
echo     - Use WinDbg for .dmp files
echo.
echo [*] For detailed analysis:
echo     - Check the Forensics_Reports folder
echo     - Review the JSON report for complete details
echo.
pause
goto :exit

:: ============================================================================
:: الخروج
:: ============================================================================
:exit
echo.
echo [*] Exiting SHΔDØW CORE...
echo.
timeout /t 2 /nobreak >nul
exit /b 0

:: ============================================================================
:: القائمة الرئيسية (للعودة)
:: ============================================================================
:main_menu
cls
goto :gui_mode
