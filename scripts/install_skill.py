#!/usr/bin/env python3
"""
安装 create-prd Skill。

推荐：安装到当前业务项目的 .agents/skills/create-prd，供 Codex 仓库级使用。
也可安装到 ~/.claude/skills/create-prd，供 Claude Code 用户级使用。
"""
from prdctl import main

if __name__ == "__main__":
    main()
