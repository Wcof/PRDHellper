from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_help_runs():
    result = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'prdctl.py'), '--help'], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'create-prd' in result.stdout
