from codegen.generate_request_response_json import (
    parse_xacml_request,
    parse_xacml_response,
)
from codegen.generate_rust import generate_policy_code
from codegen.input_generator import (
    extract_inputs_from_policy,
    generate_rust_struct,
    required_crates,
    rust_type,
)
from fuzzing.config import TEMP_JSON_PATH, TEST_SET_PATH
import json
import random
import os
from pathlib import Path
from glob import glob
import csv
import hashlib
import logging
import shutil
from jinja2 import Template

LOGGER = logging.getLogger(__name__)

try:
    from tqdm import tqdm

    HAS_TQDM = True
except ImportError:
    tqdm = lambda x: x
    HAS_TQDM = False

from ir.simple_ir import parse_xacml_simple

OPS = ["OR", "AND"]


def collect_policy() -> list[str]:
    with open(TEST_SET_PATH / ".." / "results.json", "r") as f:
        results: dict = json.load(f)
    return [
        a
        for a in results.keys()
        if not isinstance(results[a], list) or results[a][0] != "Passed"
    ]


def parse_req(path):
    with open(path, "r") as f:
        content = f.read()
    return parse_xacml_request(content)


def parse_resp(path):
    with open(path, "r") as f:
        content = f.read()
    return parse_xacml_response(content)


def get_ast_depth_size(ast: dict) -> tuple[int, int]:
    if "children" not in ast or not ast["children"]:
        return (1, 1)

    depths = []
    total_size = 1

    for child in ast["children"]:
        child_depth, child_size = get_ast_depth_size(child)
        depths.append(child_depth)
        total_size += child_size

    max_depth = max(depths) if depths else 0
    return (1 + max_depth, total_size)


def batch_main(
    new_temp_json_path: str,
    output_dir: str,
    merge_level: int = 1,
    batch_size: int = 400,
):
    policies = collect_policy()
    picked_policies = policies[:]
    random.shuffle(picked_policies)

    LOGGER.info(
        f"Generate {batch_size} merged policies in batch mode, from total {len(policies)} available policies"
    )
    if HAS_TQDM:
        pbar = tqdm(total=batch_size)
    i = 0
    while i < batch_size:
        if len(picked_policies) == 0:
            LOGGER.critical("Ran out of policies to merge")
            break
        policy_name = picked_policies.pop().removeprefix("Policy_").removesuffix(".rs")
        if (
            main(
                policy_name,
                new_temp_json_path,
                output_dir,
                merge_level,
                policies=policies[:],
            )
            == 0
        ):
            i += 1
            if HAS_TQDM:
                pbar.update(1)
    if HAS_TQDM:
        pbar.close()

    LOGGER.info("Generating summary CSV file...")
    # policy name, input file full name, response file full name, policy full name, depth, size
    rows = [
        [
            "base_policy_name",
            "input_file",
            "response_file",
            "policy_file",
            "rust_file",
            "ast_depth",
            "ast_size",
            "input_file_sha256",
            "response_file_sha256",
            "policy_file_sha256",
            "rust_file_sha256",
        ]
    ]
    for f in tqdm(glob(str((TEMP_JSON_PATH / f"*_level{merge_level}.json")))):
        with open(f, "r") as fp:
            policy = json.load(fp)
        depth, size = get_ast_depth_size(policy["rules"][0]["condition"])
        policy_name = (
            Path(f)
            .stem.removeprefix("Policy_")
            .removesuffix(f"_merged_level{merge_level}")
        )
        shutil.copyfile(
            Path(output_dir)
            / "merged_policies_code"
            / f"Policy_{policy_name}_merged_level{merge_level}.rs",
            TEMP_JSON_PATH / f"Policy_{policy_name}_merged_level{merge_level}.rs",
        )
        item = [
            policy_name,
            f"Policy_{policy_name}_merged_level{merge_level}_inputs.json",
            f"Policy_{policy_name}_merged_level{merge_level}_response.json",
            Path(f).name,
            f"Policy_{policy_name}_merged_level{merge_level}.rs",
            depth,
            size,
        ]
        for file_path in item[1:5]:
            with open(TEMP_JSON_PATH / file_path, "rb") as file_to_hash:
                file_data = file_to_hash.read()
                file_hash = hashlib.sha256(file_data).hexdigest()
                item.append(file_hash)
        rows.append(item)

    with open(
        TEMP_JSON_PATH / f"merged_level{merge_level}_summary.csv", "w", newline=""
    ) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    LOGGER.info(f"Summary CSV file generated, row count: {len(rows) - 1}")


def get_inp_struct_and_crates(
    policy_name: str,
) -> tuple[list[str], dict]:
    p = TEST_SET_PATH / policy_name / f"Policy_{policy_name}.xml"
    attributes = extract_inputs_from_policy(p)
    crates = required_crates(p)
    return (attributes, crates)


def update_inp(
    base_inp: tuple[list[str], dict],
    new_inp: tuple[list[str], dict],
) -> tuple[list[str], dict]:
    base_struct, base_crates = base_inp
    new_struct, new_crates = new_inp
    for k in base_crates.keys():
        base_crates[k] = base_crates[k] or new_crates[k]
    base_struct.extend(new_struct)
    return (base_struct, base_crates)


def generate_inp(
    inp: tuple[list[str], dict],
    output_path: str,
):
    crates = inp[1]
    fields, params, assigns = generate_rust_struct(inp[0])

    with open(os.path.join("templates", "input_template.jinja"), "r") as file:
        input_template = Template(file.read())

    input_rendered = input_template.render(
        time=crates["time"],
        date=crates["datetime"],
        duration=crates["duration"],
        fields=fields,
        params=params,
        assigns=assigns,
    )
    with open(output_path, "w") as f:
        f.write(input_rendered)

    print(f"Rust Inputs struct generated in {output_path}")


def main(
    policy_name: str,
    new_temp_json_path: str,
    output_dir: str,
    merge_level: int = 1,
    policies: list[str] = None,
):
    global TEMP_JSON_PATH
    if new_temp_json_path != "":
        TEMP_JSON_PATH = Path(new_temp_json_path)
    os.makedirs(TEMP_JSON_PATH, exist_ok=True)
    if policies is None:
        policies = collect_policy()
    policy = parse_xacml_simple(
        TEST_SET_PATH / policy_name / f"Policy_{policy_name}.xml"
    )
    if len(policy["rules"]) != 1 or policy["rules"][0]["condition"] is None:
        LOGGER.warning(f"Cannot merge policy {policy_name} without condition")
        return 1
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
    # remove dup
    if f"Policy_{policy_name}.rs" not in policies:
        LOGGER.warning(
            "Warning: current policy not in result.json(it doesn't pass test)"
        )
    policies.remove(f"Policy_{policy_name}.rs")
    base_inp = get_inp_struct_and_crates(policy_name)
    while lvl < merge_level and len(policies) > 0:
        new_policy = random.choice(policies)
        # remove dup
        policies.remove(new_policy)
        new_policy_name = new_policy.removeprefix("Policy_").removesuffix(".rs")
        new_policy_path = TEST_SET_PATH / new_policy_name
        new_policy_policy = new_policy_path / f"Policy_{new_policy_name}.xml"
        new_policy_request = new_policy_path / f"Request_{new_policy_name}.xml"
        new_policy_response = new_policy_path / f"Response_{new_policy_name}.xml"
        new_policy = parse_xacml_simple(new_policy_policy)
        new_policy_inp = parse_req(new_policy_request)
        new_policy_resp = parse_resp(new_policy_response)
        new_policy_crates = required_crates(new_policy_policy)

        new_inp = get_inp_struct_and_crates(new_policy_name)

        inp_conflict = False
        for t in base_inp[0]:
            name, type_, is_vector = t.values()
            for t2 in new_inp[0]:
                name2, type2, is_vector2 = t2.values()
                # if there are same name but different value, type or is_vector -> conflict
                if name == name2 and (
                    policy_inputs.get(name) != new_policy_inp.get(name2)
                    or type_ != type2
                    or is_vector != is_vector2
                ):
                    inp_conflict = True
                    break
            if inp_conflict:
                break
        if (
            inp_conflict
            or len(new_policy["rules"]) != 1
            or new_policy["rules"][0]["condition"] == None
        ):
            LOGGER.debug(
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
        LOGGER.debug(f"Current input struct: {base_inp}")
        LOGGER.debug(f"New input struct to merge: {new_inp}")
        LOGGER.debug(f"Merged {new_policy_path} into current policy with {top_op}")
        base_inp = update_inp(base_inp, new_inp)
        LOGGER.debug(f"Updated input struct: {base_inp}")
        lvl += 1
    if lvl != merge_level:
        LOGGER.warning(
            f"WARNING: Only merged {lvl} times, less than requested {merge_level} times. Possibly due to input conflicts."
        )
    with open(
        TEMP_JSON_PATH / f"Policy_{policy_name}_merged_level{lvl}.json", "w"
    ) as f:
        json.dump(policy, f, indent=2)
    with open(
        TEMP_JSON_PATH / f"Policy_{policy_name}_merged_level{lvl}_inputs.json",
        "w",
    ) as f:
        json.dump(policy_inputs, f, indent=2)
    with open(
        TEMP_JSON_PATH / f"Policy_{policy_name}_merged_level{lvl}_response.json",
        "w",
    ) as f:
        json.dump(policy_response, f, indent=2)
    output_dir = Path(output_dir) / "merged_policies_code"
    fields_with_datatypes = {}
    for attr in base_inp[0]:
        fields_with_datatypes[attr["name"]] = rust_type(
            attr["data_type"], attr["is_vector"]
        )
    generate_policy_code(
        policy,
        output_dir=output_dir,
        output_file=f"Policy_{policy_name}_merged_level{lvl}.rs",
        crates=policy_crates,
        fields=fields_with_datatypes,
    )
    generate_inp(
        base_inp,
        output_dir / f"Policy_{policy_name}_merged_level{lvl}_inputs.rs",
    )
    return 0
