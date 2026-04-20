#!/usr/bin/env bash
# macOS / Linux 一键安装入口

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

exec python3 scripts/install_skill.py "$@"
