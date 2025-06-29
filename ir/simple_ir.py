from lxml import etree
from typing import Dict, List, Union, Optional
import json

# Standard comparison functions
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
    "mod": "%"
}

IR = Dict[str, Union[str, List[Dict]]] # Type alias for the IR

def simplify_urn(urn: str) -> str:
    if '#' in urn:
        return urn.split('#')[-1]
    else:
        return urn.split(':')[-1]

def create_ir() -> IR:
    """Initialize the IR structure."""
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

    print(json.dumps(ir, indent=2))
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
    anyof_elems = target_elem.findall("xacml:AnyOf", namespaces=ns)
    if not anyof_elems:
        return None  # Target with no AnyOf means "match all"

    return {
        "op": "AND",
        "children": [parse_anyof(anyof_elem, ns) for anyof_elem in anyof_elems]
    }


def parse_anyof(anyof_elem, ns) -> Dict:
    """
    Parse an <AnyOf> element into an OR expression of AllOfs.
    """
    allof_elems = anyof_elem.findall("xacml:AllOf", namespaces=ns)
    return {
        "op": "OR",
        "children": [parse_allof(allof_elem, ns) for allof_elem in allof_elems]
    }


def parse_allof(allof_elem, ns) -> Dict:
    """
    Parse an <AllOf> element into an AND expression of Matches.
    """
    match_elems = allof_elem.findall("xacml:Match", namespaces=ns)
    return {
        "op": "AND",
        "children": [parse_match(match_elem, ns) for match_elem in match_elems]
    }


def parse_match(match_elem, ns) -> Dict:
    """
    Parse a <Match> element into a comparison using the standard `comparisons` mapping.
    """
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


def parse_attribute(attr_elem, ns) -> Dict:
    """Parse an Attribute element into IR format."""
    attr_id = attr_elem.get("AttributeId")
    data_type = attr_elem.get("DataType")
    values = [v.text for v in attr_elem.findall(".//xacml:AttributeValue", namespaces=ns)]

    return {
        "id": simplify_urn(attr_id),
        "data_type": simplify_urn(data_type),
        "values": values
    }


def parse_condition(condition_elem, ns) -> Optional[Dict]:
    """Parse a Condition element into IR format."""
    apply_elem = condition_elem.find(".//xacml:Apply", namespaces=ns)
    if apply_elem is None:
        return None

    return parse_apply(apply_elem, ns)


def parse_apply(apply_elem, ns) -> Dict:
    """Recursively parse Apply/Condition logic with XACML 3.0 support."""
    function_id = apply_elem.get("FunctionId")
    children = list(apply_elem)

    # Skip one-and-only functions (just pass through the first child)
    if "one-and-only" in function_id:
        if len(children) != 1:
            raise ValueError(f"one-and-only requires exactly 1 argument, got {len(children)}")
        return parse_operand(children[0], ns)

    # Check for comparison operators (both partial and full URN matches)
    simplified_function_id = simplify_urn(function_id)
    if comparisons.get(simplified_function_id, None) is not None:
        return {
            "op": comparisons[simplified_function_id],
            "left": parse_operand(children[0], ns),
            "right": parse_operand(children[1], ns)
        }

    for op_name, op_symbol in comparisons.items():
        #print(function_id)
        if function_id.endswith(f"{op_name}"):
            return {
                "op": op_symbol,
                "left": parse_operand(children[0], ns),
                "right": parse_operand(children[1], ns)
            }

    # If we get here, it's an unsupported function that we can't ignore
    raise ValueError(f"Unsupported XACML function (and not one-and-only): {function_id}")


def parse_operand(elem, ns) -> Dict:
    """Parse an operand with support for nested Apply elements."""
    if elem is None:
        return None

    tag = elem.tag.split('}')[-1]  # Remove namespace prefix

    if tag == "Apply":
        return parse_apply(elem, ns)
    elif tag == "AttributeValue":
        return {
            "type": "value",
            "data_type": simplify_urn(elem.get("DataType")),
            "value": elem.text
        }
    elif tag == "AttributeDesignator":
        return {
            "type": "attribute",
            "id": simplify_urn(elem.get("AttributeId")),
            "data_type": simplify_urn(elem.get("DataType")),
            "category": simplify_urn(elem.get("Category"))
        }
    else:
        raise ValueError(f"Unsupported operand type: {tag}")


if __name__ == "__main__":
    # Parse XACML file
    ir = parse_xacml_simple("../policies/Policy_D13.xml")

    print(json.dumps(ir, indent=2))

    print("IR generated successfully!")