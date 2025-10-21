import os
import argparse
from ir.simple_ir import parse_xacml_simple
from codegen.generate_rust import generate_policy_code
from codegen.input_generator import generate_input_struct
from codegen.generate_request_response_json import (
    generate_request_json,
    generate_response_json,
)
from fuzzing.__main__ import arg_routing, arg_adding


def main():
    parser = argparse.ArgumentParser(description="xacml-to-rust")
    parser.add_argument("policy", help="policy file")
    parser.add_argument("-r", "--request", help="request file")
    parser.add_argument("-s", "--response", help="response file")
    parser.add_argument("-o", "--output", help="output directory (default: output)")

    parser = arg_adding(parser)

    args = parser.parse_args()

    if arg_routing(args):
        # handled in arg_routing
        return

    basename = os.path.splitext(os.path.basename(args.policy))[0]
    print(f"Processing policy: {basename}")
    output_dir = args.output or "output"
    crates = generate_input_struct(
        args.policy,
        output_path=os.path.join(output_dir, "input_definition", f"{basename}.rs"),
    )
    ir = parse_xacml_simple(args.policy)
    generate_policy_code(
        ir,
        output_dir=os.path.join(output_dir, "policies_code"),
        output_file=f"{basename}.rs",
        crates=crates,
    )

    if args.request:
        generate_request_json(
            request_file=args.request,
            output_path=os.path.join(output_dir, "requests", f"{basename}.json"),
        )
    if args.response:
        generate_response_json(
            response_file=args.response,
            output_path=os.path.join(output_dir, "responses", f"{basename}.json"),
        )


if __name__ == "__main__":
    main()
