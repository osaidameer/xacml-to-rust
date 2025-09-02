from lxml import etree as ET
import os
import re

def strip_tag(tag):
    return tag.split('}')[-1] if '}' in tag else tag

def rust_type(xsd_type, is_vector=False):
    mapping = {
        "string": "String",
        "integer": "i32",
        "boolean": "bool",
        "double": "f64",
        "anyuri": "String",
        "date": "NaiveDate",
        "datetime": "DateTime<FixedOffset>",
        "time": "String",
        "datetimeduration": "String",
        "yearmonthduration": "String",
        "base64binary": "Vec<u8>"
    }
    #print(xsd_type)
    base_type = mapping.get(xsd_type.split('#')[-1].lower(), "String")
    return f"Vec<{base_type}>" if is_vector else base_type

def rustify_name(data):
    return re.sub(r'[^a-zA-Z0-9_]', '_', data.split(":")[-1])

def extract_inputs_from_policy(xml_file):
    tree = ET.parse(xml_file)
    bag_functions = ["bag", "bag-size", "is-in", "union", "intersection", "subset", "set-equals", "at-least-one-member-of"]
    inputs = {}

    for elem in tree.xpath("//*[local-name()='AttributeDesignator']"):
        attr_id = elem.get("AttributeId", "").strip()
        attr_cat = elem.get("Category", "").strip()
        data_type = elem.get("DataType", "").strip()

        if attr_id and data_type:
            name = f"{rustify_name(attr_cat)}_{rustify_name(attr_id)}"
            is_vector = False

            for ancestor in reversed(elem.xpath("ancestor::*[local-name()='Apply']")):
                func_id = ancestor.get("FunctionId", "")
                if func_id.endswith("bag"):
                    break
                elif any(vf in func_id for vf in bag_functions):
                    is_vector = True
                    break

            inputs[name] = {"name": name, "data_type": data_type, "is_vector": is_vector}

    return list(inputs.values())

def generate_rust_struct(attributes):
    fields = "\n".join(
        f"    pub {attr['name']}: {rust_type(attr['data_type'], attr['is_vector'])},"
        for attr in attributes
    )
    params = ", ".join(
        f"{attr['name']}: {rust_type(attr['data_type'], attr['is_vector'])}" for attr in attributes
    )
    assigns = "\n".join(
        f"            {attr['name']}," for attr in attributes
    )

    return f"""\
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {{
{fields}
}}

impl Inputs {{
    pub fn new({params}) -> Self {{
        Self {{
{assigns}
        }}
    }}
}}
"""

def parse_functions(xml_file):
    tree = ET.parse(xml_file)
    functions = set()

    for elem in tree.xpath("//*[local-name()='Apply']"):
        func_id = elem.get("FunctionId")
        if func_id:
            functions.add(func_id.split(":")[-1].lower())

    for elem in tree.xpath(".//*[local-name()='Match']"):
        match_id = elem.get("MatchId")
        if match_id:
            functions.add(match_id.split(":")[-1].lower())

    return functions

def parse_data(xml_file: str):
    tree = ET.parse(xml_file)
    data_types = set()

    # AttributeDesignator types
    for elem in tree.xpath("//*[local-name()='AttributeDesignator']"):
        dt = elem.get("DataType")
        if dt:
            data_types.add(dt.split("#")[-1].lower())

    # AttributeValue types
    for elem in tree.xpath("//*[local-name()='AttributeValue']"):
        dt = elem.get("DataType")
        if dt:
            data_types.add(dt.split("#")[-1].lower())

    return data_types

def required_crates(xml_file):
    data_types = parse_data(xml_file)
    functions = parse_functions(xml_file)
    print(data_types)
    print(functions)

    crates = {
        "regex": any("regexp" in f for f in functions),
        "set": any("subset" in f or "set" in f or "one-member-of" in f or "union" in f or "intersection" in f for f in functions),
        "datetime": any(dt in data_types for dt in ["date", "datetime"]),
        "time": "time" in data_types or any("time" in func for func in functions),
        "duration": any(dt in data_types for dt in ["datetimeduration", "yearmonthduration"]),
    }

    return crates

def generate_input_struct(xml_path: str, output_path: str):
    """Generate Rust Inputs struct from an XACML policy file."""
    attributes = extract_inputs_from_policy(xml_path)
    rust_code = generate_rust_struct(attributes)
    crates = required_crates(xml_path)
    print(crates)

    #"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(rust_code)

    print(f"Rust Inputs struct generated in {output_path}")
    return crates
    #"""

# Optional standalone run
if __name__ == "__main__":
    """
    input_xml = "../policies/example_input.xml"
    output_file = f"inputs_{os.path.basename(input_xml).replace('.xml', '.rs')}"
    generate_input_struct(input_xml, output_file)
    """
    base_dir = r"C:\Users\Osaid\Desktop\ZKZT\core-develop\pdp-testutils\src\test\resources\conformance\xacml-3.0-from-2.0-ct\mandatory"
    # Loop through IIC120 to IIC163
    for i in range(0, 164):
        if i != 8:
            continue
        key = f"IIB00{i}"
        folder = os.path.join(base_dir, key)
        filename = f"Policy_{key}.xml"
        file_path = os.path.join(folder, filename)

        if os.path.exists(file_path):
            print(f"Processing {key}...")
            attributes = extract_inputs_from_policy(file_path)
            rust_code = generate_rust_struct(attributes)
            generate_input_struct(file_path, "")
            print(rust_code)
        else:
            print(f"⚠️ File not found: {file_path}")