import argparse
from codegen.generate_rust import generate_policy_code
import json
from codegen.input_generator import generate_input_struct
from fuzzing.fuzzer import main as fuzz_main
from fuzzing.merger import main as merge_main, batch_main as merge_batch_main
from fuzzing.config import TEMP_JSON_PATH
import os


def arg_adding(parser: argparse.ArgumentParser):
    parser.add_argument("--fuzzing", action="store_true", help="generate fuzzing files")
    parser.add_argument(
        "--fuzzing-rounds",
        type=int,
        default=10,
        help="number of fuzzing rounds (default: 10)",
    )
    parser.add_argument(
        "--fuzzing-collect-op",
        action="store_true",
        help="force re-collect op info for fuzzing",
    )

    parser.add_argument("--merge", action="store_true", help="merge passed policies")
    parser.add_argument(
        "--merge-level", type=int, default=1, help="merge level (default: 1)"
    )

    parser.add_argument("--merge-batch", type=int, default=400)

    parser.add_argument(
        "--fuzzing-temp-json-path",
        "--merge-temp-json-path",
        type=str,
        default="",
        help="temporary path to save mutated policies (default: empty)",
    )
    return parser


def arg_routing(args: argparse.Namespace):
    if not (args.fuzzing or args.merge or args.merge_batch):
        return 0
    basename = os.path.splitext(os.path.basename(args.policy))[0]
    output_dir = args.output or "output"

    if args.fuzzing:
        crates = generate_input_struct(
            args.policy,
            output_path=os.path.join(output_dir, "input_definition", f"{basename}.rs"),
        )
        for i, (_, j) in enumerate(
            fuzz_main(
                basename.removeprefix("Policy_"),
                args.fuzzing_rounds,
                output_dir,
                args.fuzzing_collect_op,
            )
        ):
            generate_policy_code(
                j,
                output_dir=os.path.join(output_dir, "fuzzing", "policies_code"),
                output_file=f"{basename}_fuzz_{i}.rs",
                crates=crates,
            )
    elif args.merge:
        merge_main(
            basename.removeprefix("Policy_"),
            args.fuzzing_temp_json_path,
            output_dir,
            args.merge_level,
        )
    elif args.merge_batch:
        merge_batch_main(
            args.fuzzing_temp_json_path,
            output_dir,
            args.merge_level,
            args.merge_batch,
        )
    else:
        return 0

    print(
        f"Mutated policies JSON are saved to {args.fuzzing_temp_json_path or TEMP_JSON_PATH}"
    )
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", type=str, required=False, default="IIC351")
    parser.add_argument("--rounds", "-r", type=int, required=False, default=10)
    parser.add_argument(
        "--collect-op", "-c", action="store_true", help="force re-collect op info"
    )
    parser.add_argument("--temp-json-path", type=str, required=False, default="")

    args = parser.parse_args()
    for p, j in fuzz_main(args.file, args.rounds, args.temp_json_path, args.collect_op):
        with open(p, "w") as f:
            json.dump(j, f, indent=2)
    print(f"Mutated policies are saved to {TEMP_JSON_PATH}")
