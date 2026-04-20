#!/usr/bin/env python3
import sys
from pathlib import Path
from prdctl import init_project

if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    mode = sys.argv[2] if len(sys.argv) > 2 else "greenfield"
    init_project(target, mode)
