from ir.simple_ir import parse_xacml_simple
import json
from tqdm import tqdm
from pathlib import Path

TEST_SET_PATH = Path(__file__).parent / ".." / "policy_test_set"

op_map = {}


def infer_operend_data_type(condition: dict):
    left, right = condition["left"], condition["right"]
    lt, rt = "", ""
    if "data_type" not in left:
        if "op" in left:
            if left["op"] == "bagsize":
                lt = "integer"
            else:
                lt = "boolean"
    else:
        lt = left["data_type"]
    if "data_type" not in right:
        if "op" in right:
            if right["op"] == "bagsize":
                rt = "integer"
            else:
                rt = "boolean"
    else:
        rt = right["data_type"]
    return lt, rt


def collect_entry(comp):
    if not comp:
        return
    if "op" not in comp or "left" not in comp or "right" not in comp:
        return
    op, left, right = comp["op"], comp["left"], comp["right"]
    if "op" in left:
        collect_entry(left)
    if "op" in right:
        collect_entry(right)
    left["data_type"], right["data_type"] = infer_operend_data_type(comp)
    collect_operand_types(op, left, right)


def collect_operand_types(op, left, right):
    global op_map
    if op not in op_map:
        op_map[op] = set()
    op_map[op].add((left["data_type"], right["data_type"]))


def main():
    # parse all policy to see what operand type are used with what operator
    print(f"Collect info from {TEST_SET_PATH}")
    with open(TEST_SET_PATH / ".." / "results.json", "r") as f:
        results = json.load(f)

    for f in tqdm(results.keys()):
        f = (
            f.removeprefix("Policy_").removesuffix(".xml.rs")
            + "/"
            + f.removesuffix(".rs")
        )
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
    for op in op_map:
        op_map[op] = list(op_map[op])

    with open(Path(__file__).parent / "collected_op.json", "w") as f:
        json.dump(op_map, f, indent=2)


if __name__ == "__main__":
    main()
