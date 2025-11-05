from lxml import etree
from typing import Dict, List, Union, Optional
import json

"""
Standard comparison and arithmetic functions. Currently type conversion functions, high-order bag functions
"""
comparisons = {
    "greater-than-or-equal": ">=",
    "greater-than": ">",
    "less-than-or-equal": "<=",
    "less-than": "<",
    "equal": "==",
    "not-equal": "!=",
    "subtract": "-",
    "add": "+",
    "multiply": "*",
    "divide": "/",
    "regexp-match": "regex",
    "or": "||",
    "and": "&&",
    "not": "!",
    "mod": "%",
    "normalize-space": "space",
    "normalize-to-lower-case": "lower",
    "substring": "substring",
    "starts-with": "startswith",
    "ends-with": "endswith",
    "contains": "contains",
    "round": "round",
    "abs": "abs",
    "floor": "floor",
    "integer-to-double": "double",
    "double-to-integer": "integer",
    "bag": "bag", # SHALL take any number of arguments of ‘type’ and return a bag of ‘type’ values
    "bag-size": "bagsize", # SHALL take a bag of ‘type’ values as an argument and return size
    "is-in": "isin", # SHALL take argument of type as first argument, bag of values as the second argument
    "intersection": "intersection",
    "at-least-one-member-of": "onememberof",
    "union": "union",
    "subset": "subset",
    "set-equals": "setequals"
}


IR = Dict[str, Union[str, List[Dict], Dict, None]]

def simplify_urn(urn: str) -> str:
    if '#' in urn:
        return urn.split('#')[-1]
    else:
        return urn.split(':')[-1]

def create_ir() -> IR:
    """Initialize the IR structure."""
    # Added type support to incorporate PolicySets
    return {
        "type": "",
        "id": "",
        "algorithm": "",
        "target": None,
        "policies": [],
        "rules": []
    }


def parse_xacml_simple(xml_file: str) -> IR:
    """Parse XACML 3.0 XML into an IR."""
    tree = etree.parse(xml_file)
    root = tree.getroot()

    # Namespace handling for XACML 3.0
    ns = {
        "xacml": "urn:oasis:names:tc:xacml:3.0:core:schema:wd-17"
    }

    ir = create_ir()
    root_tag = etree.QName(root.tag).localname

    # If PolicySet, parse through all child policies, otherwise follow original flow of parsing a single policy
    # Currently assuming that no PolicySets will be nested inside a PolicySet (no existing test cases either)
    if root_tag == "PolicySet":
        ir["type"] = "PolicySet"
        ir["id"] = simplify_urn(root.get("PolicySetId"))
        ir["algorithm"] = simplify_urn(root.get("PolicyCombiningAlgId"))

        # Parse PolicySet Target
        target_elem = root.find(".//xacml:Target", namespaces=ns)
        if target_elem is not None:
            ir["target"] = parse_target(target_elem, ns)

        for policy_elem in root.findall(".//xacml:Policy", namespaces=ns):
            ir["policies"].append(parse_policy(policy_elem, ns))

    elif root_tag == "Policy":
        ir = parse_policy(root, ns)

    else:
        raise ValueError(f"Unexpected root element: {root_tag}")

    #print(json.dumps(ir, indent=2))
    return ir


def parse_policy(policy_elem, ns) -> Optional[Dict]:
    policy_ir = create_ir()
    policy_ir["type"] = "Policy"
    policy_ir["id"] = simplify_urn(policy_elem.get("PolicyId"))
    policy_ir["algorithm"] = simplify_urn(policy_elem.get("RuleCombiningAlgId"))

    target_elem = policy_elem.find("xacml:Target", namespaces=ns)
    if target_elem is not None:
        policy_ir["target"] = parse_target(target_elem, ns)

    for rule_elem in policy_elem.findall("xacml:Rule", namespaces=ns):
        rule_ir = parse_rule(rule_elem, ns)
        policy_ir["rules"].append(rule_ir)

    return policy_ir


def parse_target(target_elem, ns) -> Optional[Dict]:
    """
    Parse a <Target> element into symbolic logic tree IR.
    Returns None if the target is empty (i.e., matches all).
    """
    # catching case of empty target, "None" used later in the codegen to not render a target function if not required
    anyof_elems = target_elem.findall("xacml:AnyOf", namespaces=ns)
    if not anyof_elems:
        return None

    return {
        "op": "AND",
        "children": [parse_anyof(anyof_elem, ns) for anyof_elem in anyof_elems]
    }


def parse_anyof(anyof_elem, ns) -> Dict:
    """Parse an <AnyOf> element into an OR expression of AllOfs."""
    allof_elems = anyof_elem.findall("xacml:AllOf", namespaces=ns)
    return {
        "op": "OR",
        "children": [parse_allof(allof_elem, ns) for allof_elem in allof_elems]
    }


def parse_allof(allof_elem, ns) -> Dict:
    """Parse an <AllOf> element into an AND expression of Matches."""
    match_elems = allof_elem.findall("xacml:Match", namespaces=ns)
    return {
        "op": "AND",
        "children": [parse_match(match_elem, ns) for match_elem in match_elems]
    }


def parse_match(match_elem, ns) -> Dict:
    """Parse a <Match> element into a comparison using the standard `comparisons` mapping."""
    match_id = match_elem.get("MatchId")

    # Map the MatchId to a comparison operator
    op_symbol = None
    for key, symbol in comparisons.items():
        if match_id.endswith(f"{key}"):
            op_symbol = symbol
            break

    if op_symbol is None:
        raise ValueError(f"Unsupported MatchId: {match_id}")

    # Extract the operands
    attr_value_elem = match_elem.find("xacml:AttributeValue", namespaces=ns)
    attr_designator_elem = match_elem.find(".//xacml:AttributeDesignator", namespaces=ns)

    if attr_value_elem is None or attr_designator_elem is None:
        raise ValueError("Invalid Match: missing AttributeValue or AttributeDesignator")

    children = list(match_elem)
    # enforcing length of children in match, accordingly to XACML 3.0 spec, no nesting allowed in match
    if len(children) != 2:
        raise ValueError(f"Invalid Match: expected 2 children, got {len(children)}")

    left = parse_operand(children[0], ns)
    right = parse_operand(children[1], ns)

    return {
        "op": op_symbol,
        "left": left,
        "right": right
    }


def parse_rule(rule_elem, ns) -> Dict:
    """Parse a Rule element into IR format."""
    rule = {
        "rule_id": simplify_urn(rule_elem.get("RuleId")),
        "effect": simplify_urn(rule_elem.get("Effect")),
        "target": None,
        "condition": None
    }

    target_elem = rule_elem.find(".//xacml:Target", namespaces=ns)
    if target_elem is not None:
        rule["target"] = parse_target(target_elem, ns)

    # Rule Condition (optional)
    condition_elem = rule_elem.find(".//xacml:Condition", namespaces=ns)
    if condition_elem is not None:
        rule["condition"] = parse_condition(condition_elem, ns)

    return rule

"""
def parse_attribute(attr_elem, ns) -> Dict:
    #Parse an Attribute element into IR format.
    attr_id = attr_elem.get("AttributeId")
    data_type = attr_elem.get("DataType")
    values = [v.text for v in attr_elem.findall(".//xacml:AttributeValue", namespaces=ns)]

    return {
        "id": simplify_urn(attr_id),
        "data_type": simplify_urn(data_type),
        "values": values,
    }
"""

def parse_condition(condition_elem, ns) -> Optional[Dict]:
    """Parse a Condition element into IR format."""
    apply_elem = condition_elem.find(".//xacml:Apply", namespaces=ns)
    if apply_elem is None:
        return None

    return parse_apply(apply_elem, ns)


def parse_apply(apply_elem, ns) -> Dict:
    """Recursively parse Apply/Condition logic"""
    function_id = apply_elem.get("FunctionId")
    children = list(apply_elem)
    children = [child for child in children if child.tag is not None and not callable(child.tag)]

    # Skipping one-and-only functions for simplicity right now, no bag implementation yet (just pass through the first child)
    if "one-and-only" in function_id:
        if len(children) != 1:
            raise ValueError(f"one-and-only requires exactly 1 argument, got {len(children)}")

        #print(children[0].get("AttributeId"))
        return parse_operand(children[0], ns)

    """
    Checking for complete matches as operations like "equal" "or" "and" are also part of other function names, can't use 
    "in" thus returning early through exact match if found.
    """
    simplified_function_id = simplify_urn(function_id)

    if comparisons.get(simplified_function_id, None) is not None:
        if simplified_function_id in ["floor", "round", "integer-to-double", "double-to-integer"]:
            return {
                "op": comparisons[simplified_function_id],
                "operand": parse_operand(children[0], ns)
            }
        return {
            "op": comparisons[simplified_function_id],
            "left": parse_operand(children[0], ns),
            "right": parse_operand(children[1], ns)
        }


    for op_name, op_symbol in comparisons.items():
        #print(function_id)
        if function_id.endswith(f"{op_name}"):
            if op_name in ("bag", "is-in", "bag-size"):
                return {
                    "op": op_symbol,
                    "args": [parse_operand(child, ns) for child in children],
                }
            if len(children) == 1:
                return {
                    "op": op_symbol,
                    "operand": parse_operand(children[0], ns)
                }
            elif len(children) == 2:
                return {
                    "op": op_symbol,
                    "left": parse_operand(children[0], ns),
                    "right": parse_operand(children[1], ns)
                }
            elif len(children) == 3:
                return {
                    "op": op_symbol,
                    "first": parse_operand(children[0], ns),
                    "second": parse_operand(children[1], ns),
                    "third": parse_operand(children[2], ns)
                }
            else:
                raise ValueError(f"Unsupported child count in Apply: {function_id}")
    # Catch error for unsupported functions
    raise ValueError(f"Unsupported XACML function (and not one-and-only): {function_id}")


def parse_operand(elem, ns) -> Optional[Dict]:
    if elem is None:
        return None

    tag = elem.tag.split('}')[-1]

    if tag == "Apply":
        return parse_apply(elem, ns)
    # used to distinguish between literals and attributes to be picked from request. Currently, NO support for AttributeSelector as AttributeSelector uses xpath
    elif tag == "AttributeValue":
        return {
            "type": "value",
            "data_type": simplify_urn(elem.get("DataType")),
            "value": elem.text or ""
        }
    elif tag == "AttributeDesignator":
        bag_functions = ["bag", "bag-size", "is-in", "union", "intersection", "subset", "set-equals",
                         "at-least-one-member-of"]
        is_vector = False
        for ancestor in reversed(elem.xpath("ancestor::*[local-name()='Apply']")):
            func_id = ancestor.get("FunctionId", "")
            if func_id.endswith("bag"):
                break
            elif any(vf in func_id for vf in bag_functions):
                is_vector = True
                break

        #print(simplify_urn(elem.get("AttributeId")))
        return {
            "type": "attribute",
            "id": simplify_urn(elem.get("AttributeId")),
            "data_type": simplify_urn(elem.get("DataType")),
            "category": simplify_urn(elem.get("Category")),
            "is_vector": is_vector,
        }
    else:
        raise ValueError(f"Unsupported operand type: {tag}")


if __name__ == "__main__":

    ir = parse_xacml_simple("../test_policy.xml")
    print(json.dumps(ir, indent=2))
    print("IR generated successfully!")
    """
    import os
    base_dir = "../policy_test_set"

    # Output file to store all IRs
    output_file = "all_ir.json"
    all_irs = {}

    # Loop through IIC120 to IIC163
    for i in range(311, 312):
        key = f"IIF{i}"
        folder = os.path.join(base_dir, key)
        filename = f"Policy_{key}.xml"
        file_path = os.path.join(folder, filename)

        if os.path.exists(file_path):
            print(f"Processing {key}...")
            try:
                ir = parse_xacml_simple(file_path)
                print(json.dumps(ir, indent=2))
                all_irs[key] = ir
            except Exception as e:
                print(f"❌ Failed to parse {key}: {e}")
        else:
            print(f"⚠️ File not found: {file_path}")

    # Write everything to one JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_irs, f, indent=2)

    print(f"\n All IRs written to {output_file}")
    """