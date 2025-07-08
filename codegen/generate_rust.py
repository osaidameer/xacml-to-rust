from jinja2 import Template
import subprocess
import os
import re

USES_REGEX = False

# Load external templates
def load_template(filename):
    with open(os.path.join("templates", filename), "r") as file:
        return Template(file.read())

# Prepare templates
rule_template = load_template("rule_template.jinja")
policy_template = load_template("policy_template.jinja")
policyset_template = load_template("policyset_template.jinja")
master_template = load_template("master_template.jinja")


def rust_expr(node):
    global USES_REGEX
    if node is None:
        return None
    if node["op"] == "regex":
        USES_REGEX = True
        pattern = rust_operand(node["left"])
        string_to_match = rust_operand(node["right"])
        return f'Regex::new(r{pattern}).unwrap().is_match(&{string_to_match})'
    if node["op"] == "space":
        attribute = rust_operand(node["operand"])
        return f"({attribute}.trim().to_string())"
    if node["op"] == "lower":
        attribute = rust_operand(node["operand"])
        return f"({attribute}.to_lowercase().to_string())"
    if node["op"] == "startswith":
        left = rust_operand(node["left"])
        right = rust_operand(node["right"])
        return f"({right}.starts_with({left}))"
    if node["op"] == "endswith":
        left = rust_operand(node["left"])
        right = rust_operand(node["right"])
        return f"({right}.ends_with({left}))"
    if node["op"] == "contains":
        left = rust_operand(node["left"])
        right = rust_operand(node["right"])
        return f"({right}.contains({left}))"
    if node["op"] == "substring":
        first = rust_operand(node["first"])
        second = rust_operand(node["second"])
        third = rust_operand(node["third"])
        return f"substring_helper({"&" if "inp" in first else ""}{first}, {second}, {third}).unwrap_or(\"\")"
    if node["op"] in {"AND", "OR"}:
        joiner = " && " if node["op"] == "AND" else " || "
        return f"({joiner.join(rust_expr(child) for child in node['children'])})"
    else:
        left = rust_operand(node["left"])
        right = rust_operand(node["right"])
        return f"{left} {node['op']} {right}"


def rust_operand(op):
    if "op" in op and "type" not in op:
        return f"({rust_expr(op)})"
    if op["type"] == "attribute":
        return f"inp.{re.sub(r'[^a-zA-Z0-9_]', '_', op['id'])}"
    elif op["type"] == "value":
        if op["data_type"] in {"string", "anyURI", "date", "time", "dateTime"}:
            return f'"{op["value"]}"'
        return str(op["value"])
    else:
        raise ValueError(f"Unsupported operand type: {op['type']}")


def render_rule(rule, policy_id):
    rule_id = rule["rule_id"].replace("-","_")
    cond_expr = rust_expr(rule["condition"])
    helper = False
    if "substring" in cond_expr:
        helper = True
    return rule_id, rule_template.render(
        policy_name=policy_id,
        target_expr=rust_expr(rule["target"]),
        cond_expr=cond_expr,
        substring_helper=helper,
        rule_name=rule_id,
        effect=rule["effect"]
    )


# separated policy rendering function from original function to support PolicySet
def render_policy(policy):
    rule_functions = []
    rule_ids = []
    policy_id = re.sub(r'[^a-zA-Z0-9_]', '_', policy['id'])
    for rule in policy["rules"]:
        rule_id, rule_fn = render_rule(rule, policy_id)
        rule_ids.append(rule_id)
        rule_functions.append(rule_fn)

    policy_fn = policy_template.render(
        target_expr=rust_expr(policy["target"]),
        algorithm=policy["algorithm"],
        policy_name=policy_id,
        rule_ids=rule_ids
    )

    return policy_id, rule_functions, policy_fn


def generate_policy_code(ir, output_path: str):
    global USES_REGEX
    rule_functions = []
    policy_functions = []
    policy_ids = []

    if ir["type"] == "Policy":
        policy_id, rule_functions, policy_fn = render_policy(ir)
        rendered_master = master_template.render(
            regex=USES_REGEX,
            rule_functions=rule_functions,
            policy_functions=[policy_fn],
            policyset_function="",
            policy_name=policy_id,
            policyset_name=""
        )
    elif ir["type"] == "PolicySet":
        for policy in ir["policies"]:
            policy_id, rule_fns, policy_fn = render_policy(policy)
            policy_ids.append(policy_id)
            policy_functions.append(policy_fn)
            rule_functions.extend(rule_fns)

        policyset_name = re.sub(r'[^a-zA-Z0-9_]', '_', ir["id"])
        policyset_fn = policyset_template.render(
            target_expr=rust_expr(ir["target"]),
            policy_ids=policy_ids,
            algorithm=ir["algorithm"],
            policyset_name=policyset_name
        )

        rendered_master = master_template.render(
            regex=USES_REGEX,
            rule_functions=rule_functions,
            policy_functions=policy_functions,
            policyset_function=policyset_fn,
            policy_name="",
            policyset_name=policyset_name
        )

    else:
        raise ValueError(f"Unsupported Parent Type {ir['type']}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(rendered_master)

    subprocess.run(["rustfmt", output_path], check=True)
    print(f"Rust policy code generated at: {output_path}")


if __name__ == "__main__":
    pass