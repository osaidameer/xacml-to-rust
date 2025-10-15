import os
import argparse
from ir.simple_ir import parse_xacml_simple
from codegen.generate_rust import generate_policy_code
from codegen.input_generator import generate_input_struct
from codegen.generate_request_response_json import generate_request_json, generate_response_json
from fuzzing.__main__ import main as fuzzing_main


def main():
    parser = argparse.ArgumentParser(description='xacml-to-rust')
    parser.add_argument('policy', help='policy file')
    parser.add_argument('-r', '--request', help='request file')
    parser.add_argument('-s', '--response',  help='response file')
    parser.add_argument('-o', '--output', help='output directory (default: output)')

    parser.add_argument('--fuzzing', action='store_true', help='generate fuzzing files')
    parser.add_argument('--fuzzing-rounds', type=int, default=10, help='number of fuzzing rounds (default: 10)')
    parser.add_argument('--fuzzing-temp-json-path', type=str, default='', help='temporary path to save mutated policies (default: empty)')
    parser.add_argument('--fuzzing-collect-op', action='store_true', help='force re-collect op info for fuzzing')
    
    args = parser.parse_args()
    basename = os.path.splitext(os.path.basename(args.policy))[0]
    print(f"Processing policy: {basename}")
    output_dir = args.output or "output"
    crates = generate_input_struct(args.policy, output_path=os.path.join(output_dir, "input_definition", f"{basename}.rs"))
    
    if not args.fuzzing:
        ir = parse_xacml_simple(args.policy)
        generate_policy_code(ir, output_dir=os.path.join(output_dir, "policies_code"), output_file=f"{basename}.rs", crates=crates)

        if args.request:
            generate_request_json(request_file=args.request, output_path=os.path.join(output_dir, "requests" ,f"{basename}.json"))
        if args.response:
            generate_response_json(response_file=args.response, output_path=os.path.join(output_dir, "responses" ,f"{basename}.json"))
    else:
        for i, (_, j) in enumerate(fuzzing_main(basename.removeprefix("Policy_"), args.fuzzing_rounds, args.fuzzing_temp_json_path, args.fuzzing_collect_op)):
            generate_policy_code(j, output_dir=os.path.join(output_dir, "fuzzing", "policies_code"), output_file=f"{basename}_fuzz_{i}.rs", crates=crates)
        print(f"Mutated policies JSON are saved to {args.fuzzing_temp_json_path or 'the specified temporary path'}")
        print(f"Fuzzing policies code are saved to {os.path.join(output_dir, 'fuzzing', 'policies_code')}")

if __name__ == "__main__":
    main()
