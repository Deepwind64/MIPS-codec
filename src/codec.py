import argparse
import os
from pathlib import Path

from model import INSTRUCTIONS, INST_BIN_MAP
from core import ArgsError


def encode_one(instruction: str):
    split_inst = instruction.strip().lower().split()
    format_inst = INSTRUCTIONS.get(split_inst[0])
    extra = {}
    if not format_inst:
        split_name = split_inst[0].split(".")
        if split_name[0] == "cmp":
            extra["condn"] = split_name[1]
            split_name[1] = "condn"
        else:
            extra["fmt"] = split_name[-1]
            split_name[-1] = "fmt"

        format_inst = INSTRUCTIONS.get(".".join(split_name))

    if format_inst is None:
        raise ArgsError(f"Unknown Instruction {instruction}.")

    for k, v in extra.items():
        format_inst.load_value(k, v)

    # remove possible space between args
    return format_inst.encode("".join(split_inst[1:]))


def decode_one(binary_str: str) -> str:
    if len(binary_str) != 32 or any(i not in ("01") for i in binary_str):
        raise ValueError(f"Binary string '{binary_str}' is invalid.")

    op = binary_str[:6]
    item = INST_BIN_MAP.get(op)
    if item is None:
        raise ArgsError("Unknown Instruction.")

    possible_insts = []
    if isinstance(item, list):
        possible_insts.extend(item)

    if isinstance(item, dict):
        possible_insts.extend(item["_"])

        for length in item["length"]:
            tail = binary_str[-length:]
            insts = item[length].get(tail)
            if insts:
                possible_insts.extend(insts)

    results = [i.decode(binary_str) for i in possible_insts]
    return " | ".join([result for result in results if result])


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
        help="Choose the process mode: encode (assembly to binary) or decode (binary to assembly).",
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "-f", "--input_file", type=str, help="Path to the input file with instructions."
    )

    parser.add_argument(
        "-o",
        "--output_file",
        type=str,
        help="Path to the output file. If omitted, output will be printed to the console.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    process_batch(
        mode=args.mode, input_file=args.input_file, output_file=args.output_file
    )
