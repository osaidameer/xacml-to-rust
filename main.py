from ir.simple_ir import parse_xacml_simple
from codegen.generate_rust import generate_policy_code
from codegen.input_generator import generate_input_struct

def main():
    filename = "policies/Policy_D02.xml"
    ir = parse_xacml_simple(filename)
    generate_input_struct(filename, f"output/input_{filename}.rs")
    generate_policy_code(ir, f"output/output_{filename}.rs")

if __name__ == "__main__":
    main()