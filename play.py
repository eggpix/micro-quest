"""

RUN THIS FILE TO PLAY MICRO QUEST


Arguments:
-l, --last: Load the last played game
-f, --file: Quickly load a game from file path

"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "src" / "main.py"

subprocess.run(
    [sys.executable, str(MAIN), *sys.argv[1:]],
    cwd=ROOT
)