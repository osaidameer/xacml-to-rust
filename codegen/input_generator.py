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
        "date": "String",
        "dateTime": "String",
        "time": "String",
        "daytimeduration": "String",
        "yearmonthduration": "String",
        "base64binary": "Vec<u8>"
    }
    print(xsd_type)
    base_type = mapping.get(xsd_type.split('#')[-1].lower(), "String")
    return f"Vec<{base_type}>" if is_vector else base_type

def rustify_name(data):
    return re.sub(r'[^a-zA-Z0-9_]', '_', data.split(":")[-1])

def extract_inputs_from_policy(xml_file):
    tree = ET.parse(xml_file)
    bag_functions = ["bag", "bag-size", "is-in", "union", "intersection", "subset"]
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
                #print(func_id)
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
    """
    input_xml = "../policies/example_input.xml"
    output_file = f"inputs_{os.path.basename(input_xml).replace('.xml', '.rs')}"
    generate_input_struct(input_xml, output_file)
    """
    base_dir = r"C:\Users\Osaid\Desktop\ZKZT\core-develop\pdp-testutils\src\test\resources\conformance\xacml-3.0-from-2.0-ct\mandatory"
    # Loop through IIC120 to IIC163
    for i in range(120, 164):
        if i != 129:
            continue
        key = f"IIC{i}"
        folder = os.path.join(base_dir, key)
        filename = f"Policy_{key}.xml"
        file_path = os.path.join(folder, filename)

        if os.path.exists(file_path):
            print(f"Processing {key}...")
            attributes = extract_inputs_from_policy(file_path)
            rust_code = generate_rust_struct(attributes)
            print(rust_code)
        else:
            print(f"⚠️ File not found: {file_path}")