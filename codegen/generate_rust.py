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

def handle_regex(node):
    global USES_REGEX
    USES_REGEX = True
    pattern = rust_operand(node["left"])
    string_to_match = rust_operand(node["right"])
    return f'Regex::new(r{pattern}).unwrap().is_match(&{string_to_match})'

def handle_string_normalization(node, method):
    attribute = rust_operand(node["operand"])
    return f"({attribute}.{method}().to_string())"

def handle_string_matches(node, method):
    left = rust_operand(node["left"])
    right = rust_operand(node["right"])
    return f"({right}.{method}({left}))"

def handle_substring(node):
    string = rust_operand(node["first"])
    start = rust_operand(node["second"])
    end = rust_operand(node["third"])
    return f"substring_helper({"&" if "inp" in string else ""}{string}, {start}, {end}).unwrap_or(\"\")"

def handle_boolean(node):
    joiner = " && " if node["op"] == "AND" else " || "
    return f"({joiner.join(rust_expr(child) for child in node['children'])})"

def handle_arithmetic(node, method):
    attribute = rust_operand(node["operand"])
    return f"({attribute}.{method}())"

def handle_conversion(node, method):
    attribute = rust_operand(node["operand"])
    return f"({attribute} {method})"


def handle_default(node):
    left = rust_operand(node["left"])
    right = rust_operand(node["right"])
    return f"{left} {node['op']} {right}"

helper_functions = {
    "regex": (handle_regex, None),
    "space": (handle_string_normalization, "trim"), "lower": (handle_string_normalization, "to_lowercase"),
    "startswith": (handle_string_matches, "starts_with"),
    "endswith": (handle_string_matches, "ends_with"),
    "contains": (handle_string_matches, "contains"),
    "substring": (handle_substring, None),
    "AND": (handle_boolean, None),
    "OR": (handle_boolean, None),
    "abs": (handle_arithmetic, "abs"), "floor": (handle_arithmetic, "floor"), "round": (handle_arithmetic, "round"),
    "integer": (handle_conversion, "as i32"), "double": (handle_conversion, "as f64"),
}

def rust_expr(node):
    if node is None:
        return None
    handler, method = helper_functions.get(node["op"], (handle_default, None))
    if method:
        return handler(node, method)
    return handler(node)

def rust_operand(op):
    if "op" in op and "type" not in op:
        return f"({rust_expr(op)})"
    if op["type"] == "attribute":
        return f"inp.{re.sub(r'[^a-zA-Z0-9_]', '_', op['id'])}"
    elif op["type"] == "value":
        if op["data_type"] in {"string", "anyURI", "date", "time", "dateTime", "rfc822Name"}:
            return f'"{op["value"]}"'
        return str(op["value"])
    else:
        raise ValueError(f"Unsupported operand type: {op['type']}")


def render_rule(rule, policy_id):
    rule_id = rule["rule_id"].replace("-","_")
    cond_expr = rust_expr(rule["condition"])
    helper = cond_expr is not None and "substring" in cond_expr
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