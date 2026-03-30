import json
from pathlib import Path
from typing import Dict, List

DATASET_PATH = Path("data") / "eval_dataset.json"


def load_eval_dataset() -> List[Dict[str, str]]:
    with DATASET_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)