from codegen.generate_request_response_json import (
    parse_xacml_request,
    parse_xacml_response,
)
from codegen.generate_rust import generate_policy_code
from codegen.input_generator import (
    extract_inputs_from_policy,
    generate_input_struct,
    required_crates,
)
from fuzzing.config import TEMP_JSON_PATH, TEST_SET_PATH
import json
import random
import os
from pathlib import Path

from ir.simple_ir import parse_xacml_simple

OPS = ["OR", "AND"]


def collect_policy():
    with open(TEST_SET_PATH / ".." / "results.json", "r") as f:
        results = json.load(f)
    return [a for a in results.keys() if results[a][0] == "Passed"]


def parse_req(path):
    with open(path, "r") as f:
        content = f.read()
    return parse_xacml_request(content)


def parse_resp(path):
    with open(path, "r") as f:
        content = f.read()
    return parse_xacml_response(content)


def main(
    policy_name: str, new_temp_json_path: str, output_dir: str, merge_level: int = 1
):
    global TEMP_JSON_PATH
    if new_temp_json_path != "":
        TEMP_JSON_PATH = Path(new_temp_json_path)
    os.makedirs(TEMP_JSON_PATH, exist_ok=True)
    policies = collect_policy()
    policy = parse_xacml_simple(
        TEST_SET_PATH / policy_name / f"Policy_{policy_name}.xml"
    )
    policy_inputs = parse_req(
        TEST_SET_PATH / policy_name / f"Request_{policy_name}.xml"
    )
    policy_response = parse_resp(
        TEST_SET_PATH / policy_name / f"Response_{policy_name}.xml"
    )
    policy_crates = required_crates(
        TEST_SET_PATH / policy_name / f"Policy_{policy_name}.xml"
    )
    lvl = 0
    while lvl < merge_level:
        new_policy = (
            random.choice(policies).removeprefix("Policy_").removesuffix(".xml.rs")
        )
        new_policy_path = TEST_SET_PATH / new_policy
        new_policy_policy = new_policy_path / f"Policy_{new_policy}.xml"
        new_policy_request = new_policy_path / f"Request_{new_policy}.xml"
        new_policy_response = new_policy_path / f"Response_{new_policy}.xml"
        new_policy = parse_xacml_simple(new_policy_policy)
        new_policy_inp = parse_req(new_policy_request)
        new_policy_resp = parse_resp(new_policy_response)
        new_policy_crates = required_crates(new_policy_policy)

        inp_conflict = False
        for k, v in policy_inputs.items():
            for k2, v2 in new_policy_inp.items():
                if k == k2 and v != v2:
                    inp_conflict = True
                    break
            if inp_conflict:
                break
        if (
            inp_conflict
            or len(new_policy["rules"]) != 1
            or new_policy["rules"][0]["condition"] == None
        ):
            print(
                f"Skip merging {new_policy_path} due to input conflict with current policy"
            )
            continue
        top_op = random.choice(OPS)
        policy["rules"][0]["condition"] = {
            "op": top_op,
            "children": [
                policy["rules"][0]["condition"],
                new_policy["rules"][0]["condition"],
            ],
        }
        policy_inputs.update(new_policy_inp)
        # maybe consider multiple AND/OR instead of only two children?
        if top_op == "AND":
            policy_response["decision"] = (
                policy_response["decision"] and new_policy_resp["decision"]
            )
        else:
            policy_response["decision"] = (
                policy_response["decision"] or new_policy_resp["decision"]
            )
        policy_crates.update(new_policy_crates)
        print(f"Merged {new_policy_path} into current policy with {top_op}")
        lvl += 1
    with open(
        TEMP_JSON_PATH / f"Policy_{policy_name}_merged_level{merge_level}.json", "w"
    ) as f:
        json.dump(policy, f, indent=2)
    with open(
        TEMP_JSON_PATH / f"Policy_{policy_name}_merged_level{merge_level}_inputs.json",
        "w",
    ) as f:
        json.dump(policy_inputs, f, indent=2)
    with open(
        TEMP_JSON_PATH
        / f"Policy_{policy_name}_merged_level{merge_level}_response.json",
        "w",
    ) as f:
        json.dump(policy_response, f, indent=2)
    output_dir = Path(output_dir) / "merged_policies_code"
    generate_policy_code(
        policy,
        output_dir=output_dir,
        output_file=f"Policy_{policy_name}_merged_level{merge_level}.rs",
        crates=policy_crates,
    )
