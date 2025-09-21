import json
import os
from lxml import etree

def cast_value(value, datatype):
    if not datatype:
        return value
    if datatype.endswith("#integer"):
        return int(value)
    elif datatype.endswith("#double") or datatype.endswith("#float") or datatype.endswith("#decimal"):
        return float(value)
    elif datatype.endswith("#boolean"):
        return value.lower() == "true"
    else:
        return value

def parse_xacml_request(xml_string):
    ns = {'xacml': 'urn:oasis:names:tc:xacml:3.0:core:schema:wd-17'}
    root = etree.fromstring(xml_string.encode("utf-8"))
    attribute_dict = {}

    attributes = root.xpath(".//xacml:Attribute", namespaces=ns)
    if not attributes:
        print("No attribute elements in request file")
        return None

    for attr in attributes:
        parent = attr.getparent()
        category = parent.attrib.get("Category")
        attr_id_full = attr.get("AttributeId")
        if attr_id_full:
            key = category.split(":")[-1].replace("-", "_") + "_" + attr_id_full.split(":")[-1].replace("-", "_")

            for value_elem in attr.xpath("xacml:AttributeValue", namespaces=ns):
                raw_value = value_elem.text
                datatype = value_elem.get("DataType")
                casted_value = cast_value(raw_value, datatype)

                if key not in attribute_dict:
                    attribute_dict[key] = casted_value
                else:
                    if isinstance(attribute_dict[key], list):
                        attribute_dict[key].append(casted_value)
                    else:
                        attribute_dict[key] = [attribute_dict[key], casted_value]

    return attribute_dict

def parse_xacml_response(xml_string):
    ns = {'xacml': 'urn:oasis:names:tc:xacml:3.0:core:schema:wd-17'}
    root = etree.fromstring(xml_string.encode("utf-8"))

    decision = root.find(".//xacml:Decision", namespaces=ns).text
    if decision is None:
        print("No decision in response file")
        return None

    result = {
        "decision": decision,
    }
    return result

def generate_json(input_file, output_path, parser_func):
    with open(input_file, "r", encoding="utf-8") as file:
        xml_content = file.read()

    json_data = parser_func(xml_content)
    if json_data is None:
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as out_file:
        json.dump(json_data, out_file, indent=4)


def generate_request_json(request_file, output_path):
    generate_json(request_file, output_path, parse_xacml_request)
    print("Generated request json file at {}".format(output_path))

def generate_response_json(response_file, output_path):
    generate_json(response_file, output_path, parse_xacml_response)
    print("Generated response json file at: {}".format(output_path))
