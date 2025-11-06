from operator import truediv

from jinja2 import Template
from codegen.input_generator import rustify_name
import subprocess
import os
import re
import compile_regex
import hashlib

right_f64_dict = {"INF": "f64::INFINITY", "-INF": "f64::NEG_INFINITY", "NaN": "f64::NAN"}
regex_dict = dict()
data_type_dict = {
    "date": "NaiveDate",
    "time": "NaiveTime",
    "dateTime": "DateTime<FixedOffset>"
}
parse_funcs = {
    "time": "parse_time",
    "yearMonthDuration": "parse_duration",
    "dayTimeDuration": "parse_duration",
}
field_to_jwt_mapping = {
    "access_subject_subject_id": "sub",
    "access_subject_role": "role",
    "access_subject_age": "age"
}

# Load external templates
def load_template(filename):
    with open(os.path.join("templates", filename), "r") as file:
        return Template(file.read())

# Prepare templates
rule_template = load_template("rule_template.jinja")
policy_template = load_template("policy_template.jinja")
policyset_template = load_template("policyset_template.jinja")
master_template = load_template("master_template.jinja")
helper_template = load_template("helper_template.jinja")

def registe_regex(pattern):
    compiled_bytes = compile_regex.create_dfa_bytes(pattern)
    h = hashlib.md5()
    h.update(pattern.encode('utf-8'))
    p_hash = h.hexdigest().upper()
    reg_name = "RE_" + p_hash
    #print(reg_name)
    global regex_dict
    if reg_name in regex_dict.keys():
        assert compiled_bytes == regex_dict[reg_name], "Error: Regist two regular expression with same name"
    else:
        regex_dict[reg_name] = compiled_bytes
    return reg_name

def handle_regex(node):
    pattern = rust_operand(node["left"], for_regex=True)
    string_to_match = rust_operand(node["right"])
    # print(string_to_match)
    regex_name = registe_regex(pattern)
    return f'eval_regex(&{string_to_match}, &{regex_name})'
    # return f'Regex::new(r{pattern}).unwrap().is_match(&{string_to_match})'

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
    if node["op"] in ("<", "<=", ">", ">=") and right.startswith('"') and not right.endswith("unwrap()"):
        left = left + ".as_str()"
    if right in {"INF", "-INF", "NaN"}:
        right = right_f64_dict[right]
    return f"{left} {node['op']} {right}"

def handle_bag(node):
    args = node["args"]
    values = []
    for item in args:
        val = rust_operand(item)
        if val.startswith('"') and val.endswith('"') and ("Naive" not in val) and ("DateTime" not in val):
            values.append("&" + val + ".to_string()")
        elif val.startswith("inp."):
            values.append("&" + val)
        elif "parse_time" in val:
            values.append(val)
        elif "parse_duration" in val:
            values.append(val)
        else:
            values.append("&" + val)
    return f"vec![{",".join(values)}]"

def handle_bagsize(node):
    args = node["args"]
    expression = rust_operand(args[0])
    if "parse_time(x))" in expression:
        expression = expression.replace(".iter().map(|x| parse_time(x)).collect()", "")
    elif "parse_duration(x))" in expression:
        expression = expression.replace(".iter().map(|x| parse_duration(x)).collect()", "")
    return f"{expression}.len()"

def handle_isin(node):
    args = node["args"]
    search_value = rust_operand(args[0])
    if search_value.startswith('"') and search_value.endswith('"'):
        search_value = f"{search_value}.to_string()"

    if args[1]["data_type"].lower() in {"time", "daytimeduration", "yearmonthduration"}:
        return rust_operand(args[1]).replace(".collect()", f".any(|dt| dt == {rust_operand(args[0])})")
    return f"{rust_operand(args[1])}.contains(&{search_value})"

def handle_set_helper(left, right):
    left_iter = "iter()." if left.startswith("inp.") else "into_iter()."
    right_iter = "iter()." if right.startswith("inp.") else "into_iter()."

    if "collect" in left:
        left_iter = ""
        left = left.replace(".collect()", "")
    if "collect" in right:
        right_iter = ""
        right = right.replace(".collect()", "")
    return left, right, left_iter, right_iter

def handle_set_boolean(node, method):
    left, right, left_iter, right_iter = handle_set_helper(rust_operand(node["left"]), rust_operand(node["right"]))
    if method != "equal": # subset case
        return f"{left}.{left_iter}collect::<HashSet<_>>().{method}(&{right}.{right_iter}collect::<HashSet<_>>()){" == false" if method == "is_disjoint" else ""}"
    return f"{left}.{left_iter}collect::<HashSet<_>>() == {right}.{right_iter}collect::<HashSet<_>>()"

def handle_set_non_boolean(node, method):
    left, right, left_iter, right_iter = handle_set_helper(rust_operand(node["left"]), rust_operand(node["right"]))
    return f"{left}.{left_iter}collect::<HashSet<_>>().{method}(&{right}.{right_iter}collect::<HashSet<_>>()).cloned().collect::<Vec<_>>()"

helper_functions = {
    "regex": (handle_regex, None),
    "space": (handle_string_normalization, "trim"), "lower": (handle_string_normalization, "to_lowercase"),
    "startswith": (handle_string_matches, "starts_with"), "endswith": (handle_string_matches, "ends_with"), "contains": (handle_string_matches, "contains"),
    "substring": (handle_substring, None),
    "AND": (handle_boolean, None), "OR": (handle_boolean, None),
    "abs": (handle_arithmetic, "abs"), "floor": (handle_arithmetic, "floor"), "round": (handle_arithmetic, "round"),
    "integer": (handle_conversion, "as i32"), "double": (handle_conversion, "as f64"),
    "bag": (handle_bag, None),
    "bagsize": (handle_bagsize, None),
    "isin": (handle_isin, None),
    "intersection": (handle_set_non_boolean, "intersection"), "union": (handle_set_non_boolean, "union"),
    "onememberof": (handle_set_boolean, "is_disjoint"), "subset": (handle_set_boolean, "is_subset"), "setequals": (handle_set_boolean, "equal"),
}

def rust_expr(node):
    if node is None:
        return None
    handler, method = helper_functions.get(node["op"], (handle_default, None))
    if method:
        return handler(node, method)
    return handler(node)


def rust_operand(op, for_regex=False):
    global data_type_dict, parse_funcs

    if "op" in op and "type" not in op:
        return f"({rust_expr(op)})"

    if op["type"] == "attribute":

        field_name = f"inp.{rustify_name(op['category'])}_{rustify_name(op['id'])}"

        def rust_parse_call(func_name):
            if op["is_vector"]:
                return f"{field_name}.iter().map(|x| {func_name}(x)).collect()"
            return f"{func_name}(&{field_name})"

        if op["data_type"] in parse_funcs:
            return rust_parse_call(parse_funcs[op["data_type"]])

        return f"{field_name}"

    elif op["type"] == "value":
        string_types = {"string", "anyURI", "rfc822Name", "hexBinary", "base64Binary"}
        date_types = {"date", "dateTime"}
        duration_types = {"yearMonthDuration", "dayTimeDuration"}
        data_type = op["data_type"]
        value = op["value"]

        if data_type in string_types:
            if for_regex:
                return value
            return f'"{value}"'

        if data_type in date_types:
            rust_type = data_type_dict[data_type]
            return f'"{value}".parse::<{rust_type}>().unwrap()'

        if data_type == "time":
            return f'parse_time("{value}")'

        if data_type in duration_types:
            return f'parse_duration("{value}")'

        return str(value)

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
def render_policy(policy, output_dir):
    rule_functions = []
    rule_ids = []
    policy_id = re.sub(r'[^a-zA-Z0-9_]', '_', policy['id'])
    for rule in policy["rules"]:
        rule_id, rule_fn = render_rule(rule, policy_id)
        rule_ids.append(rule_id)
        rule_functions.append(rule_fn)

    policy_fn = policy_template.render(
        target_expr=rust_expr(policy["target"]) if policy["target"] else "true",
        algorithm=policy["algorithm"],
        policy_name=policy_id,
        rule_ids=rule_ids
    )
    global regex_dict
    regex_claim = []
    # creating directory incase it does not exist already
    os.makedirs(os.path.dirname(output_dir), exist_ok=True)
    for k, v in regex_dict.items():
        regex_claim.append(f'static {k}: &[u8] = include_bytes!("{k}.bin");')
        with open(os.path.join(output_dir, f'{k}.bin'), 'wb') as f:
            f.write(v)
    return policy_id, rule_functions, policy_fn, regex_claim

def generate_policy_code(ir, output_dir: str, output_file: str, crates, fields, jwt=False):
    output_path = os.path.join(output_dir, output_file)
    rule_functions = []
    policy_functions = []
    policy_ids = []
    regex_claims = []
    #jwt_fields = ', '.join(f'"{f}"' for f in fields)
    jwt_fields = []

    for field_name, data_type in fields.items():
        if (field_name.lower() == "access_subject_subject_id" or field_name.lower() == "access_subject_role" ) and data_type.lower() == "string":
            jwt_fields.append(field_to_jwt_mapping[field_name])
        if field_name.lower() == "access_subject_age" and data_type in {"f64", "i32"}:
            jwt_fields.append(field_to_jwt_mapping[field_name])

    # print(jwt_fields)

    if ir["type"] == "Policy":
        policy_id, rule_functions, policy_fn, regex_claim = render_policy(ir, output_dir)

        helper_function = helper_template.render(
            regex=crates["regex"],
            regex_claims=regex_claim,
            jwt=jwt,
            jwt_fields=jwt_fields,
            time=crates["time"],
            duration=crates["duration"],
        )

        rendered_master = master_template.render(
            set=crates["set"],
            time=crates["time"],
            date=crates["datetime"],
            duration=crates["duration"],
            helper_functions=helper_function,
            rule_functions=rule_functions,
            policy_functions=[policy_fn],
            policyset_function="",
            policy_name=policy_id,
            policyset_name="",
            jwt=jwt,
        )
    elif ir["type"] == "PolicySet":
        policies_with_targets = []
        for policy in ir["policies"]:
            policy_id, rule_fns, policy_fn, regex_claim = render_policy(policy, output_dir)
            #if policy["target"]:
                # print(policy["target"], policy_id)
            policies_with_targets.append(policy_id)
            policy_ids.append(policy_id)
            policy_functions.append(policy_fn)
            rule_functions.extend(rule_fns)
            regex_claims = regex_claim

        #print(policies_with_targets)
        policyset_name = re.sub(r'[^a-zA-Z0-9_]', '_', ir["id"])
        policyset_fn = policyset_template.render(
            target_expr=rust_expr(ir["target"]),
            policy_ids=policy_ids,
            algorithm=ir["algorithm"],
            policyset_name=policyset_name,
            policies_with_targets=policies_with_targets
        )

        helper_function = helper_template.render(
            regex=crates["regex"],
            regex_claims=regex_claims,
            jwt=jwt,
            jwt_fields=jwt_fields,
            time=crates["time"],
            duration=crates["duration"],
        )

        rendered_master = master_template.render(
            set=crates["set"],
            time=crates["time"],
            date=crates["datetime"],
            duration=crates["duration"],
            helper_functions=helper_function,
            rule_functions=rule_functions,
            policy_functions=policy_functions,
            policyset_function=policyset_fn,
            policy_name="",
            policyset_name=policyset_name,
            jwt=jwt,
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
