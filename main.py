import sys
import os
import argparse
from ir.simple_ir import parse_xacml_simple
from codegen.generate_rust import generate_policy_code
from codegen.input_generator import generate_input_struct
from codegen.generate_request_response_json import generate_request_json, generate_response_json


def main():
    parser = argparse.ArgumentParser(description='Compiler for ZKZT')
    parser.add_argument('input', help='input file')
    parser.add_argument('-r', '--request', help='request file')
    parser.add_argument('-s', '--response',  help='response file')
    args = parser.parse_args()

    basename = os.path.basename(args.input)
    ir = parse_xacml_simple(args.input)
    crates = generate_input_struct(args.input, f"output/input_definition/{basename[:-4]}.rs")
    generate_policy_code(ir, "output/policies_code/", f"{basename[:-4]}.rs", crates)

    if args.request:
        generate_request_json(request_file=args.request, output_path=f"output/requests/{basename[:-4]}.json")
    if args.response:
        generate_response_json(response_file=args.response, output_path=f"output/responses/{basename[:-4]}.json")

if __name__ == "__main__":
    main()
