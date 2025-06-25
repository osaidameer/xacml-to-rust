from dataclasses import dataclass, asdict
from typing import List, Optional
import xml.etree.ElementTree as ET
import json


def strip_tag(tag: str) -> str:
    return tag.split('}')[-1] if '}' in tag else tag

def simplify_urn(urn: str) -> str:
    if '#' in urn:
        return urn.split('#')[-1]
    else:
        return urn.split(':')[-1]

class Expression:
    pass

@dataclass
class AttributeValue(Expression):
    data_type: str
    value: str

    @classmethod
    def from_xml(cls, elem: ET.Element):
        raw_type = elem.attrib["DataType"]
        simple_type = simplify_urn(raw_type)
        return cls(
            data_type=simple_type,
            value=elem.text.strip()
        )

@dataclass
class AttributeDesignator(Expression):
    attribute_id: str
    category: str
    data_type: str
    must_be_present: bool

    @classmethod
    def from_xml(cls, elem: ET.Element):
        raw_type = elem.attrib["DataType"]
        return cls(
            attribute_id=simplify_urn(elem.attrib["AttributeId"]),
            category=simplify_urn(elem.attrib["Category"]),
            data_type=simplify_urn(raw_type),
            must_be_present=elem.attrib.get("MustBePresent", "false") == "true"
        )

@dataclass
class Apply(Expression):
    function_id: str
    arguments: List[Expression]

    @classmethod
    def from_xml(cls, elem: ET.Element):
        raw_func = elem.attrib["FunctionId"]
        simple_func = simplify_urn(raw_func)
        arguments = [parse_expression(child) for child in elem]
        return cls(function_id=simple_func, arguments=arguments)

def parse_expression(elem: ET.Element) -> Expression:
    tag = strip_tag(elem.tag)
    if tag == "Apply":
        return Apply.from_xml(elem)
    elif tag == "AttributeValue":
        return AttributeValue.from_xml(elem)
    elif tag == "AttributeDesignator":
        return AttributeDesignator.from_xml(elem)
    else:
        raise ValueError(f"Unknown expression element: {tag}")

@dataclass
class Match:
    match_id: str
    attribute_value: AttributeValue
    attribute_designator: AttributeDesignator

    @classmethod
    def from_xml(cls, elem: ET.Element):
        children = list(elem)
        val = AttributeValue.from_xml(children[0])
        des = AttributeDesignator.from_xml(children[1])
        return cls(match_id=elem.attrib["MatchId"].split(":")[-1], attribute_value=val, attribute_designator=des)

@dataclass
class AllOf:
    matches: List[Match]

    @classmethod
    def from_xml(cls, elem: ET.Element):
        # Only direct children Match elements inside AllOf
        matches = [Match.from_xml(m) for m in elem.findall("{*}Match")]
        return cls(matches=matches)

@dataclass
class AnyOf:
    all_ofs: List[AllOf]

    @classmethod
    def from_xml(cls, elem: ET.Element):
        return cls(all_ofs=[AllOf.from_xml(a) for a in elem.findall("{*}AllOf")])

@dataclass
class Target:
    any_ofs: List[AnyOf]

    @classmethod
    def from_xml(cls, elem: ET.Element):
        return cls(any_ofs=[AnyOf.from_xml(a) for a in elem.findall("{*}AnyOf")])

@dataclass
class Rule:
    rule_id: str
    effect: str
    target: Optional[Target] = None
    condition: Optional[Expression] = None

    @classmethod
    def from_xml(cls, elem: ET.Element):
        target_elem = elem.find("{*}Target")
        cond_elem = elem.find("{*}Condition")
        return cls(
            rule_id=simplify_urn(elem.attrib["RuleId"]),
            effect=elem.attrib["Effect"],
            target=Target.from_xml(target_elem) if target_elem is not None else None,
            condition=parse_expression(cond_elem[0]) if cond_elem is not None else None
        )

@dataclass
class Policy:
    policy_id: str
    combining_alg: str
    rules: List[Rule]
    target: Optional[Target] = None

    @classmethod
    def from_xml(cls, elem: ET.Element):
        target_elem = elem.find("{*}Target")
        rules = [Rule.from_xml(r) for r in elem.findall("{*}Rule")]
        raw_comb_alg = elem.attrib["RuleCombiningAlgId"]
        simple_comb_alg = simplify_urn(raw_comb_alg)
        return cls(
            policy_id=simplify_urn(elem.attrib.get("PolicyId", "policy")),
            combining_alg=simple_comb_alg,
            rules=rules,
            target=Target.from_xml(target_elem) if target_elem is not None else None,
        )

def parse_xacml_complex(filename: str) -> Policy:
    tree = ET.parse(filename)
    root = tree.getroot()
    return Policy.from_xml(root)

if __name__ == "__main__":
    policy = parse_xacml_complex("../policies/Policy_D01.xml")
    print(json.dumps(asdict(policy), indent=2))
