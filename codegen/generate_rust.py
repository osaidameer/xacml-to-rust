from jinja2 import Template
import subprocess
import os

# Load external templates
def load_template(filename):
    with open(os.path.join("templates", filename), "r") as file:
        return Template(file.read())

# Prepare templates
rule_template = load_template("rule_template.jinja")
policy_template = load_template("policy_template.jinja")
master_template = load_template("master_template.jinja")


def rust_expr(node):
    if node is None:
        return None
    if node["op"] == "regex":
        pattern = rust_operand(node["left"])
        string_to_match = rust_operand(node["right"])
        return f'Regex::new({pattern}).unwrap().is_match(&{string_to_match})'
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
        return f"inp.{op['id'].replace('-', '_')}"
    elif op["type"] == "value":
        if op["data_type"] in {"string", "anyURI", "date", "time", "dateTime"}:
            return f'"{op["value"]}"'
        return str(op["value"])
    else:
        raise ValueError(f"Unsupported operand type: {op['type']}")


def generate_policy_code(ir, output_path: str):
    """Generate Rust code from an XACML policy and write to a file."""
    rule_functions = []
    rule_ids = []
    for rule in ir["rules"]:
        rule_id = rule["rule_id"].replace("-", "_")
        rule_ids.append(rule_id)
        rendered = rule_template.render(
            target_expr=rust_expr(rule["target"]),
            cond_expr=rust_expr(rule["condition"]),
            rule_name=rule_id,
            effect=rule["effect"]
        )
        rule_functions.append(rendered)

    policy_id = ir["policy_id"].replace("-", "_")
    policy = policy_template.render(
        target_expr=rust_expr(ir["target"]),
        algorithm=ir["algorithm"],
        policy_name=policy_id,
        rule_ids=rule_ids
    )
    rendered_master = master_template.render(
        rule_functions=rule_functions,
        policy_function=policy,
        policy_name=policy_id,
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(rendered_master)

    subprocess.run(["rustfmt", output_path], check=True)
    print(f"Rust policy code generated at: {output_path}")


if __name__ == "__main__":
    pass