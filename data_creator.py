import json
from pathlib import Path

dict = {}
for x in range(10):
    dict["2025-12-2"+str(x)] = True

folder = Path('history_files/')
for file in folder.iterdir():
    with open (file, "w") as f:
        json.dump(dict, f, indent=2)