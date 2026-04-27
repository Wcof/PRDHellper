@echo off
setlocal

REM PRDHellper 双击安装入口（Windows CMD）
cd /d "%~dp0"

echo == PRDHellper 一键安装（双击入口）==
echo.

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 install.py
  goto :end
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python install.py
  goto :end
)

echo [WARN] 未找到 Python，切换到无 Python 安装模式。
where powershell >nul 2>nul
if %ERRORLEVEL%==0 (
  powershell -ExecutionPolicy Bypass -File "%~dp0scripts\install_no_python.ps1"
  goto :end
)

echo [ERROR] 未找到 Python 或 PowerShell，无法执行安装。
set ERR=1
goto :done

:end
set ERR=%ERRORLEVEL%

:done
echo.
if %ERR%==0 (
  echo 安装流程已结束。
) else (
  echo 安装流程异常退出（exit=%ERR%）。
)
echo.
pause
exit /b %ERR%
