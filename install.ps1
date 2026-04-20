# Windows PowerShell 一键安装入口

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Invoke-Installer {
  param([string[]]$ArgsList)

  if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 scripts/install_skill.py @ArgsList
    return $LASTEXITCODE
  }
  if (Get-Command python -ErrorAction SilentlyContinue) {
    & python scripts/install_skill.py @ArgsList
    return $LASTEXITCODE
  }

  Write-Host "[ERROR] 未找到 Python 运行环境。请先安装 Python 3。"
  return 1
}

$code = Invoke-Installer -ArgsList $args
Write-Host ""
if ($code -eq 0) {
  Write-Host "安装流程已结束。"
} else {
  Write-Host "安装流程异常退出（exit=$code）。"
}
Write-Host ""
Read-Host "按回车键关闭窗口" | Out-Null
exit $code
