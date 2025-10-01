import sys
sys.path.append("..")

from ir.simple_ir import parse_xacml_simple
import glob
import json
from tqdm import tqdm
from pathlib import Path

TEST_SET_PATH = Path("../policy_test_set").absolute()

op_map = {}

def collect_entry(comp):
    if not comp:
        return
    print(comp)
    if "op" not in comp or "left" not in comp or "right" not in comp:
        return
    # TODO bagsize
    op, left, right = comp["op"], comp["left"], comp["right"]
    if "op" in left:
        collect_entry(left)
        left["data_type"] = "boolean"
    if "op" in right:
        collect_entry(right)
        right["data_type"] = "boolean"
    collect_operand_types(op, left, right)

def collect_operand_types(op, left, right):
    global op_map
    if op not in op_map:
        op_map[op] = {"left": set(), "right": set()}
    op_map[op]["left"].add(left["data_type"])
    op_map[op]["right"].add(right["data_type"])

if __name__ == "__main__":
    # parse all policy to see what operand type are used with what operator
    print(f"Collect info from {TEST_SET_PATH}")
    for f in tqdm(glob.glob("*/Policy_*.xml", root_dir=TEST_SET_PATH, recursive=True)):
        try:
            j = parse_xacml_simple(TEST_SET_PATH / f)
        except Exception as e:
            if "Unsupported XACML" in str(e):
                continue
            print(f"Failed to parse {f}")
            raise e
        if j["type"] != "Policy":
            continue
        for rule in j["rules"]:
            comp = rule["condition"]
            if comp:
                collect_entry(comp)
            target = rule["target"]
            if target:
                # TODO
                pass

    with open("collected_op.json", "w") as f:
        json.dump(op_map, f, indent=2)