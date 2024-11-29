import argparse
import os
from pathlib import Path

from mips_codec.model import INSTRUCTIONS, Instruction
from mips_codec.core import ArgsError


def encode_one(instruction: str):
    split_inst = instruction.strip().lower().split()
    format_inst = INSTRUCTIONS.get(split_inst[0])
    if not format_inst:
        # search I-Type
        format_inst = INSTRUCTIONS["000000"].get(split_inst[0])

    if format_inst is None:
        raise ArgsError("Unknown Instruction.")

    # remove possible space between args
    return format_inst.encode("".join(split_inst[1:]))


def decode_one(binary_str: str) -> str:
    op = binary_str[:6]
    if op == "000000":
        inner_insts = INSTRUCTIONS[op]
    else:
        inner_insts = INSTRUCTIONS

    format_inst = next(
        (
            inst
            for inst in inner_insts.values()
            if isinstance(inst, Instruction) and inst.op == op
        ),
        None,
    )
    if format_inst is None:
        raise ArgsError("Unknown Instruction.")
    return format_inst.decode(binary_str)


def read_input(input_str="", input_file=""):
    if input_file:
        try:
            with open(input_file, "r") as file:
                return file.read().strip()
        except FileNotFoundError:
            raise ArgsError(f"Input file '{input_file}' not found.")
    elif input_str:
        return input_str.strip()
    else:
        raise ArgsError("No input provided.")


def write_output(output_str, output_file=""):
    if output_file:
        output_file = Path(output_file)
        try:
            os.makedirs(output_file.parent, exist_ok=True)
            with open(output_file, "w") as file:
                file.write(output_str)
        except Exception as e:
            raise ArgsError(f"Error writing to output file: {e}")
    else:
        print(output_str)


def process_batch(mode: str, input_str="", input_file="", output_file=""):
    data = read_input(input_str, input_file)

    if mode == "encode":
        process_func = encode_one
    elif mode == "decode":
        process_func = decode_one
    else:
        raise ArgsError("Invalid Process Mode.")

    results = []
    for line in data.split("\n"):
        try:
            results.append(process_func(line))
        except Exception as e:
            results.append(str(e))

    result = "\n".join(results)
    write_output(result, output_file)
    return result


def parse_args():
    parser = argparse.ArgumentParser(
        description="MIPS Assembly and Machine Code Converter"
    )

    parser.add_argument(
        "mode",
        choices=["encode", "decode"],
        help="Choose the process mode: encode (assembly to binary) or decode (binary to assembly)."
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "-f", "--input_file", type=str,
        help="Path to the input file with instructions."
    )

    parser.add_argument(
        "-o", "--output_file", type=str,
        help="Path to the output file. If omitted, output will be printed to the console."
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    process_batch(
        mode=args.mode,
        input_file=args.input_file,
        output_file=args.output_file
    )