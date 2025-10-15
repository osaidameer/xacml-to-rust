from pathlib import Path
import json
from .collect_op import main
import random


class OpProvider:
    def __init__(self):
        op_metadata_json = Path(__file__).parent / "collected_op.json"
        if not op_metadata_json.exists():
            print("No collected_op.json found, collecting...")
            main()
        with open(op_metadata_json, "r") as f:
            self.op_map = json.load(f)

    def get_op_from_type(self, left_type, right_type):
        if left_type != right_type:
            print("Type inconsist??")
        candidates = []
        for op, types in self.op_map.items():
            if any(a for a in types if a == [left_type, right_type]):
                candidates.append(op)
        if not candidates:
            return None
        return random.choice(candidates)
