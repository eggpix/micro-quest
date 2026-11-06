import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "src" / "main.py"

subprocess.run(
    [sys.executable, str(MAIN), *sys.argv[1:]],
    cwd=ROOT
)