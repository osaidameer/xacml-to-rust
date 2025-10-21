from ir.simple_ir import comparisons, parse_xacml_simple
from .op_provider import OpProvider
from .collect_op import infer_operend_data_type
from pathlib import Path
import os
from fuzzing.config import TEST_SET_PATH, TEMP_JSON_PATH

# def mutate_comparison(comp):
#     _, left, right = comp["op"], comp["left"], comp["right"]
#     return [random.choice(comparisons.values()), left, right]

# def mutate_operand(val):
#     if val["DataType"] == "integer":
#         val["Value"] = str(int(val["Value"]) + random.randint(-10, 10))
#     elif val["DataType"] == "string" or val["DataType"] == "anyURI":
#         # xor
#         s = list(val["Value"])
#         if len(s) > 0:
#             idx = random.randint(0, len(s) - 1)
#             s[idx] = chr(random.randint(32, 126))
#             val["Value"] = "".join(s)
#     return val


def mutate_op2(condition: dict):
    assert "op" in condition
    if condition["op"] == "bagsize":
        return condition
    condition["op"] = op_provider.get_op_from_type(*infer_operend_data_type(condition))
    left, right = condition["left"], condition["right"]
    if "op" in left:
        condition["left"] = mutate_op2(left)
    if "op" in right:
        condition["right"] = mutate_op2(right)
    return condition


def mutate_policy(j):
    # TODO: more mutator
    j["condition"] = mutate_op2(j["condition"])
    return j


def main(policy, rounds, temp_json_path, collect_op):
    """
    @param policy: policy name, e.g., IIC351
    """
    global op_provider, TEMP_JSON_PATH
    if collect_op:
        from .collect_op import main as collect_main

        collect_main()
    op_provider = OpProvider()

    if temp_json_path != "":
        TEMP_JSON_PATH = Path(temp_json_path)
    os.makedirs(TEMP_JSON_PATH, exist_ok=True)

    j = parse_xacml_simple(TEST_SET_PATH / policy / f"Policy_{policy}.xml")
    if j["type"] != "Policy":
        raise NotImplementedError("Only support single policy")
    for i in range(rounds):
        j["rules"][0] = mutate_policy(j["rules"][0])
        yield TEMP_JSON_PATH / f"{policy}_{i}.json", j