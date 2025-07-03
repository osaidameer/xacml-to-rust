import sys
import os
from ir.simple_ir import parse_xacml_simple
from codegen.generate_rust import generate_policy_code
from codegen.input_generator import generate_input_struct

def main(filename):
    basename = os.path.basename(filename)
    ir = parse_xacml_simple(filename)
    generate_input_struct(filename, f"output/input_policies/{basename}.rs")
    generate_policy_code(ir, f"output/output_policies/{basename}.rs")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)
    main(sys.argv[1])