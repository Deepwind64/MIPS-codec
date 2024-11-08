from dataclasses import dataclass
import math
import csv
from pathlib import Path

from mips_codec.core import ArgsError


@dataclass
class Instruction:
    op: str

    def add_args(self, args: str):
        raise NotImplementedError()

    def encode(self, list) -> str:
        raise NotImplementedError()

    def decode(self, binary_str: str) -> str:
        raise NotImplementedError()

    @staticmethod
    def check_imme(imme: int, max_width=16) -> int:
        if (
                type(imme) is not int
                or imme < -(2 ** (max_width - 1))
                or imme >= 2 ** (max_width - 1)
        ):
            raise ArgsError(f"Invalid immediate {imme}")
        return imme

    @staticmethod
    def dec2bin(dec_num: int, bin_width: int, is_unsigned=True) -> str:
        if is_unsigned:
            py_bin_str = bin(dec_num)
            if py_bin_str[0] == "-":
                bin_str = py_bin_str[3:]
            else:
                bin_str = py_bin_str[2:]
        else:
            if dec_num == 0:
                bin_str = "0"
            elif dec_num > 0:
                # 补符号位0
                bin_str = "0" + bin(dec_num)[2:]
            else:
                # 求负数补码
                for i in range(int(math.log2(-dec_num)), 32):
                    if 2 ** i + dec_num >= 0:
                        bin_str = bin(2 ** (i + 1) + dec_num)[2:]
                        break

        if bin_width < len(bin_str):
            raise ArgsError(f"Immediate {dec_num} exceeds the data width {bin_width}.")
        else:
            # 实际位宽小于设定位宽则补符号位
            if is_unsigned:
                bin_str = "0" * (bin_width - len(bin_str)) + bin_str
            else:
                bin_str = bin_str[0] * (bin_width - len(bin_str)) + bin_str
        return bin_str

    @staticmethod
    def bin2dec(binary: str, is_unsigned: bool = False):
        """取反加一，转换为十进制并添加负号"""
        if is_unsigned:
            result = int(binary, 2)
        else:
            if binary[0] == "1":
                reversed_bin = "".join(
                    ["1" if bit == "0" else "0" for bit in binary[1:]]
                )
                result = -int(bin(int(reversed_bin, 2) + 1)[2:], 2)
            else:
                result = int(binary[1:], 2)

        return result


@dataclass
class RInstruction(Instruction):
    func: str = ""
    rs: int = -1
    rt: int = -1
    rd: int = -1
    shamt: int = 0
    op: str = "000000"
    is_unsigned: bool = False

    def add_args(self, args: str):
        reg_amount = 3
        try:
            # type check
            f_args = [reg for reg in args.split(",")]

            match self.func:
                # sll srl sra
                case "000000" | "000010" | "000011":
                    self.rd, self.rs = int(f_args[0][1:]), 0
                    self.rt, self.shamt = int(f_args[1][1:]), self.check_imme(
                        int(f_args[2]), max_width=5
                    )
                    reg_amount = 2
                # sllv srlv srav
                case "000100" | "000110" | "000111":
                    self.rd, self.rt, self.rs = [int(reg[1:]) for reg in f_args]
                # jr
                case "001000":
                    self.rs = int(f_args[0][1:])
                    reg_amount = 1
                case _:
                    self.rd, self.rs, self.rt = [int(reg[1:]) for reg in f_args]

            # format check
            if sum(1 for reg in f_args if reg[0] == "$") != reg_amount:
                raise ArgsError(f"Invalid reg in {args}")

            # value check
            for i in (self.rd, self.rt, self.rs):
                if i < 0 or i > 31:
                    raise ArgsError(f"Invalid reg '{i}'")
        except ArgsError as e:
            raise e
        except Exception as e:
            raise ArgsError(f"Invalid args in {args}")

    def encode(self, args: str) -> str:
        self.add_args(args)
        return (
                self.op
                + "".join(
            self.dec2bin(i, 5) for i in (self.rs, self.rt, self.rd, self.shamt)
        )
                + self.func
        )

    def decode(self, binary_str: str) -> str:
        rs = int(binary_str[6:11], 2)
        rt = int(binary_str[11:16], 2)
        rd = int(binary_str[16:21], 2)
        shamt = int(binary_str[21:26], 2)
        func = binary_str[26:32]

        name = [
            name for name, inst in INSTRUCTIONS["000000"].items() if inst.func == func
        ]

        if name:
            name = name[0]
            match name:
                case "sll" | "srl" | "sra":
                    inst_str = f"{name} ${rd}, ${rt}, {shamt}"
                case "sllv" | "srlv" | "srav":
                    inst_str = f"{name} ${rd}, ${rt}, ${rs}"
                case "jr":
                    inst_str = f"{name} ${rs}"
                case _:
                    inst_str = f"{name} ${rd}, ${rs}, ${rt}"
        else:
            raise ArgsError("Unknown function code.")

        return inst_str


@dataclass
class IInstruction(Instruction):
    rs: int = -1
    rt: int = -1
    Imme: int = -1
    is_unsigned: bool = False

    def add_args(self, args: str):
        reg_amount = 2
        try:
            f_args = args.split(",")

            match self.op:
                # lui
                case "001111":
                    self.rt = int(f_args[0][1:])
                    self.Imme = self.check_imme(int(f_args[1]), max_width=16)
                    reg_amount = 1
                # lw sw
                case "100011" | "101011":
                    self.rt = int(f_args[0][1:])
                    split_index = f_args[1].index("(")
                    self.rs = int(f_args[1][split_index + 2: -1])
                    self.Imme = self.check_imme(int(f_args[1][:split_index]))

                    if (
                            f_args[1][split_index: split_index + 2] != "($"
                            or f_args[1][-1] != ")"
                    ):
                        raise ArgsError(f"Invalid args in {args}")
                    reg_amount = 1
                case _:
                    self.rt, self.rs = int(f_args[0][1:]), int(f_args[1][1:])
                    self.Imme = self.check_imme(int(f_args[2]), max_width=16)

            # format check
            if sum(1 for reg in f_args if reg[0] == "$") != reg_amount:
                raise ArgsError(f"Invalid reg in {args}")

            # value check
            for i in (self.rt, self.rs):
                if i < 0 or i > 31:
                    raise ArgsError(f"Invalid reg '{i}'")
        except ArgsError as e:
            raise e
        except Exception:
            raise ArgsError(f"Invalid args in {args}")

    def encode(self, args: str) -> str:
        self.add_args(args)
        imme_bin = self.dec2bin(self.Imme, bin_width=16, is_unsigned=self.is_unsigned)
        return self.op + self.dec2bin(self.rs, 5) + self.dec2bin(self.rt, 5) + imme_bin

    def decode(self, binary_str: str) -> str:
        op = binary_str[:6]
        rs = int(binary_str[6:11], 2)
        rt = int(binary_str[11:16], 2)
        imme = self.bin2dec(binary_str[16:], self.is_unsigned)

        name = [
            name
            for name, inst in INSTRUCTIONS.items()
            if name != "000000" and inst.op == op
        ]

        if name:
            name = name[0]
            match name:
                case "lui":
                    inst_str = f"{name} ${rt}, {imme}"
                case "lw" | "sw":
                    inst_str = f"{name} ${rt}, {imme}(${rs})"
                case _:
                    inst_str = f"{name} ${rt}, ${rs}, {imme}"
        else:
            raise ArgsError("Unknown op code.")

        return inst_str


@dataclass
class JInstruction(Instruction):
    address: int = -1

    def add_args(self, args: str):
        try:
            self.address = int(args)
        except Exception as e:
            raise ArgsError(f"Invalid address {args}")

    def encode(self, args: str) -> str:
        self.add_args(args)
        addr_bin = self.dec2bin(self.address, bin_width=26, is_unsigned=True)
        return self.op + addr_bin

    def decode(self, binary_str: str) -> str:
        op = binary_str[:6]
        address = int(binary_str[6:], 2)

        name = [
            name
            for name, inst in INSTRUCTIONS.items()
            if name != "000000" and inst.op == op
        ]

        if name:
            name = name[0]
            inst_str = f"{name} {address}"
        else:
            raise ArgsError("Unknown op code.")

        return inst_str


def load_instructions_from_csv(csv_file):
    instructions = {}
    with open(csv_file, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            name, inst_type, op = row["name"], row["type"], row["op"]
            reg_dict = {key: int(row[key]) for key in ("rd", "rs", "rt") if row[key]}
            func = row["func"] if row["func"] else None
            is_unsigned = row["is_unsigned"] == "True"

            match inst_type:
                case "R":
                    instructions.setdefault("000000", {})[name] = RInstruction(
                        func=func,
                        is_unsigned=is_unsigned,
                        **reg_dict
                    )
                case "I":
                    instructions[name] = IInstruction(op=op, is_unsigned=is_unsigned, **reg_dict)
                case "J":
                    instructions[name] = JInstruction(op=op)
                case _:
                    raise ValueError(f"Unknown instruction type: {inst_type}")

    return instructions


INSTRUCTIONS = load_instructions_from_csv(Path(__file__).parent / "instructions.csv")
