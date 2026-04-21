#!/usr/bin/env python3
"""PRDHellper unified installer entrypoint.

Single cross-platform installer launcher for macOS/Linux/Windows.
"""
from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    installer = repo_root / "scripts" / "install_skill.py"
    if not installer.exists():
        print(f"[ERROR] installer not found: {installer}")
        return 2

    system = platform.system().lower()
    if system.startswith("darwin"):
        system_name = "macOS"
    elif system.startswith("windows"):
        system_name = "Windows"
    elif system.startswith("linux"):
        system_name = "Linux"
    else:
        system_name = platform.system() or "Unknown"

    print(f"== PRDHellper installer ({system_name}) ==")
    print("入口已统一为 install.py（跨平台自动识别系统）。")

    args = list(sys.argv[1:])
    if "--wizard" in args:
        args = [a for a in args if a != "--wizard"]
        cmd = [sys.executable, str(installer), *args]
    else:
        cmd = [sys.executable, str(installer), "--one-click", *args]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
