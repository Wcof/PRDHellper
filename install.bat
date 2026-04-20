@echo off
setlocal

REM Windows 一键安装入口（CMD / 双击）
cd /d "%~dp0"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 scripts\install_skill.py %*
  goto :end
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python scripts\install_skill.py %*
  goto :end
)

echo [ERROR] 未找到 Python 运行环境。请先安装 Python 3。
set ERR=1
goto :pause_end

:end
set ERR=%ERRORLEVEL%

:pause_end
echo.
if %ERR%==0 (
  echo 安装流程已结束。
) else (
  echo 安装流程异常退出（exit=%ERR%）。
)
echo.
pause
exit /b %ERR%
