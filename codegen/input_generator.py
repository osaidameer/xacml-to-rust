from lxml import etree as ET
import os

def strip_tag(tag):
    return tag.split('}')[-1] if '}' in tag else tag

def rust_type(xsd_type):
    mapping = {
        "string": "String",
        "integer": "i32",
        "boolean": "bool",
        "double": "f64",
        "anyURI": "String"
    }
    return mapping.get(xsd_type.split('#')[-1].lower(), "String")

def extract_inputs_from_policy(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    inputs = {}

    for elem in root.iter():
        #print(f"DEBUG: {elem} | tag type: {type(elem.tag)}")
        if not isinstance(elem.tag, str):
            continue
        tag = strip_tag(elem.tag)
        if tag == "AttributeDesignator":
            attr_id = elem.attrib.get("AttributeId", "").strip()
            data_type = elem.attrib.get("DataType", "").strip()
            if attr_id and data_type:
                name = attr_id.split(":")[-1].replace("-", "_")
                inputs[name] = data_type

    return [{"name": name, "data_type": dtype} for name, dtype in inputs.items()]

def generate_rust_struct(attributes):
    fields = "\n".join(
        f"    pub {attr['name']}: {rust_type(attr['data_type'])},"
        for attr in attributes
    )
    params = ", ".join(
        f"{attr['name']}: {rust_type(attr['data_type'])}" for attr in attributes
    )
    assigns = "\n".join(
        f"            {attr['name']}," for attr in attributes
    )

    return f"""\
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
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

def generate_input_struct(xml_path: str, output_path: str):
    """Generate Rust Inputs struct from an XACML policy file."""
    attributes = extract_inputs_from_policy(xml_path)
    rust_code = generate_rust_struct(attributes)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(rust_code)

    print(f"Rust Inputs struct generated in {output_path}")


# Optional standalone run
if __name__ == "__main__":
    input_xml = "../policies/example_input.xml"
    output_file = f"inputs_{os.path.basename(input_xml).replace('.xml', '.rs')}"
    generate_input_struct(input_xml, output_file)
