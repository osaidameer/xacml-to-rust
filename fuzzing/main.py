import sys
sys.path.append("..")

from ir.simple_ir import comparisons, parse_xacml_simple
import argparse
import random
import json

def mutate_comparison(comp):
    _, left, right = comp["op"], comp["left"], comp["right"]
    return [random.choice(comparisons.values()), left, right]

def mutate_operand(val):
    if val["DataType"] == "integer":
        val["Value"] = str(int(val["Value"]) + random.randint(-10, 10))
    elif val["DataType"] == "string" or val["DataType"] == "anyURI":
        # xor
        s = list(val["Value"])
        if len(s) > 0:
            idx = random.randint(0, len(s) - 1)
            s[idx] = chr(random.randint(32, 126))
            val["Value"] = "".join(s)
    return val

def mutate_policy(j):
    # TODO
    # pick a type of mutation and apply
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", type=str, required=False, default="IIC351")
    parser.add_argument("--rounds", "-r", type=int, required=False, default=10)
    
    args = parser.parse_args()
    j = parse_xacml_simple(f"../policies/Policy_{args.file}.xml")
    if j["type"] != "Policy":
        raise NotImplementedError("Only support single policy")
    for _ in range(args.rounds):
        j["rules"] = mutate_policy(j["rules"])
    json.dump(j, indent=2)

