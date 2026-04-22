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

echo [ERROR] 未找到 Python 运行环境。请先安装 Python 3。
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
