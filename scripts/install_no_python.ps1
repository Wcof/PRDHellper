$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$helperRoot = Split-Path -Parent $scriptDir
$targetRoot = Split-Path -Parent $helperRoot
$prdRoot = if ($env:PRD_ROOT) { $env:PRD_ROOT } else { "docs/prd" }
$installDir = Join-Path $targetRoot ".agents\skills\create-prd"

$blockStart = "<!-- create-prd:start -->"
$blockEnd = "<!-- create-prd:end -->"
$blockContent = @"
$blockStart
## create-prd

当任务涉及 PRD 初始化、页面 PRD、完整 PRD、Axure HTML 导入、页面变更同步 PRD、代码与 PRD 一致性审计时：

1. 优先阅读 `.agents/skills/create-prd/SKILL.md`。
2. PRD 输出目录固定写到目标项目根目录下的 `$prdRoot`，不要写到 `PRDHellper/docs/` 或 `.agents/skills/create-prd/` 内。
3. 当前环境无 Python 时，跳过脚本命令，直接按 Skill 规则维护 `$prdRoot` 下的 PRD 文档并使用 `[TODO: ...]` 标注缺口。
4. 如果后续安装了 Python，再执行：`bash .agents/skills/create-prd/scripts/check_consistency.sh . --mode=strict`。
5. 如果仓库里还有其他 `SKILL.md` 或说明文件，不要把它们当作 create-prd 本体。

$blockEnd
"@

function Upsert-Block {
    param(
        [Parameter(Mandatory = $true)][string]$File,
        [Parameter(Mandatory = $true)][string]$Heading
    )

    $dir = Split-Path -Parent $File
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }

    if (!(Test-Path $File)) {
        Set-Content -Path $File -Value "# $Heading`r`n`r`n$blockContent`r`n" -Encoding UTF8
        return
    }

    $text = Get-Content -Path $File -Raw -Encoding UTF8
    if ($text.Contains($blockStart) -and $text.Contains($blockEnd)) {
        $pattern = [regex]::Escape($blockStart) + ".*?" + [regex]::Escape($blockEnd)
        $newText = [regex]::Replace($text, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $blockContent }, "Singleline")
        Set-Content -Path $File -Value $newText -Encoding UTF8
    } else {
        Set-Content -Path $File -Value ($text.TrimEnd() + "`r`n`r`n" + $blockContent + "`r`n") -Encoding UTF8
    }
}

Write-Host "== create-prd 无 Python 安装模式 =="
Write-Host "helper 根目录: $helperRoot"
Write-Host "目标项目根目录: $targetRoot"

if (Test-Path $installDir) {
    Remove-Item -Recurse -Force $installDir
}
New-Item -ItemType Directory -Path (Split-Path -Parent $installDir) -Force | Out-Null
Copy-Item -Path $helperRoot -Destination $installDir -Recurse -Force
if (Test-Path (Join-Path $installDir ".git")) { Remove-Item -Recurse -Force (Join-Path $installDir ".git") }
if (Test-Path (Join-Path $installDir ".pytest_cache")) { Remove-Item -Recurse -Force (Join-Path $installDir ".pytest_cache") }

Get-ChildItem -Path $installDir -Filter ".DS_Store" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

Upsert-Block -File (Join-Path $targetRoot "AGENTS.md") -Heading "AGENTS"
Upsert-Block -File (Join-Path $targetRoot "CLAUDE.md") -Heading "CLAUDE"
Upsert-Block -File (Join-Path $targetRoot ".agents\AGENTS.md") -Heading "AGENTS"
Upsert-Block -File (Join-Path $targetRoot ".claude\CLAUDE.md") -Heading "CLAUDE"

$prdAbs = Join-Path $targetRoot $prdRoot
@("pages", "system", "changelog", "audit", "imports", "templates", ".index") | ForEach-Object {
    New-Item -ItemType Directory -Path (Join-Path $prdAbs $_) -Force | Out-Null
}

Write-Host "已完成无 Python 安装："
Write-Host "- Skill 安装目录：$installDir"
Write-Host "- 引导文件：$targetRoot\AGENTS.md, $targetRoot\CLAUDE.md, $targetRoot\.agents\AGENTS.md, $targetRoot\.claude\CLAUDE.md"
Write-Host "- PRD 目录骨架：$prdAbs"
