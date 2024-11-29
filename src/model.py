from dataclasses import dataclass
import math
import csv
import logging
from pathlib import Path
from enum import Enum, auto

from core import ArgsError, InstTableError


class FMT(Enum):
    S = "10000"
    D = "10001"
    W = "10011"
    L = "10100"


class CONDN(Enum):
    AF = "00000"
    UN = "00001"
    EQ = "00010"
    UEQ = "00011"
    LT = "00100"
    ULT = "00101"
    LE = "00110"
    ULE = "00111"
    SAF = "01000"
    SUN = "01001"
    SEQ = "01010"
    SUEQ = "01011"
    SLT = "01100"
    SULT = "01101"
    SLE = "01110"
    SULE = "01111"
    AT = "10000"
    OR = "10001"
    UNE = "10010"
    NE = "10011"
    UGE = "10100"
    OGE = "10101"
    UGT = "10110"
    OGT = "10111"
    SAT = "11000"
    SOR = "11001"
    SUNE = "11010"
    SNE = "11011"
    SUGE = "11100"
    SOGE = "11101"
    SUGT = "11110"
    SOGT = "11111"


class FieldType(Enum):
    GPR = auto()
    FPR = auto()
    BASE = auto()
    FMT = auto()
    CONDN = auto()
    EXPR = auto()
    IMME = auto()


@dataclass
class Field:
    name: str
    length: int
    type = FieldType.IMME
    value: str = ""
    input_order: int = 0
    pos_flag = False
    input_options = []
    expression: str = ""

    @staticmethod
    def parse(field_str: str):
        split_field = field_str.split()
        field = Field(name=split_field[0], length=int(split_field[1]))
        if split_field[2:]:
            field.parse_value(split_field[2:])

        return field

    def parse_value(self, value: list):
        if len(value) == 1 and value[0] != "?":
            match value[0]:
                case "0":
                    self.value = self.length * "0"
                case "~":
                    self.type = FieldType.BASE
                case _:
                    if all(l.isdigit() for l in value[0]):
                        if self.length != len(value[0]):
                            raise InstTableError(
                                "Field Length Doesn't Match The Given Value."
                            )
                        self.value = value[0]
                    else:
                        self.type = FieldType.EXPR
                        self.expression = value[0]
        else:
            value_sign = value[0]
            match value_sign:
                case "?":
                    match self.name:
                        case "fmt":
                            self.type = FieldType.FMT
                            self.input_options = list(value[1])
                        case "condn":
                            self.type = FieldType.CONDN
                case "+" | "-":
                    match self.name:
                        case "rt" | "rs" | "rd":
                            self.type = FieldType.GPR
                        case "ft" | "fs" | "fd":
                            self.type = FieldType.FPR
                    self.input_order = int(value[1])
                    if value_sign == "+":
                        self.pos_flag = True
                case _:
                    raise ValueError(f"Invalid Value: {" ".join(value)} Found.")

    def load_value(self, value=None, value_map=None):
        if self.value:
            raise ValueError("Field Value Exsited.")

        if value == None:
            # expression support
            if value_map:
                int_value = eval(self.expression, value_map)
                self.value = Instruction.dec2bin(int_value, self.length)
                value_map[self.name] = int_value
        else:
            match self.type:
                case FieldType.GPR:
                    try:
                        assert value[0] == "r"
                        self.value = Instruction.dec2bin(int(value[1:]), self.length)
                    except AssertionError | ValueError:
                        raise ValueError("Invalid Input for GPR Field.")

                case FieldType.FPR:
                    try:
                        assert value[0] == "f"
                        self.value = Instruction.dec2bin(int(value[1:]), self.length)
                    except AssertionError | ValueError:
                        raise ValueError("Invalid Input for FPR Field.")

                case FieldType.BASE:
                    try:
                        self.value = Instruction.dec2bin(int(value), self.length)
                    except ValueError:
                        raise ValueError("Invalid Input for BASE Field.")

                case FieldType.FMT:
                    try:
                        self.value = FMT._member_map_[value.upper()].value
                    except KeyError:
                        raise ValueError(
                            "Invalid Input for FMT Part in Instruction Name."
                        )

                case FieldType.CONDN:
                    try:
                        self.value = CONDN._member_map_[value.upper()].value
                    except KeyError:
                        raise ValueError(
                            "Invalid Input for CONDN Part in Instruction Name."
                        )

                case FieldType.IMME:
                    try:
                        tmp_value = int(value)
                        if tmp_value < 0:
                            raise ValueError(f"Invalid value {tmp_value}")
                        if self.pos_flag and tmp_value == 0:
                            raise ValueError(
                                f"Field {self.name} needs a positive value."
                            )

                        self.value = Instruction.dec2bin(
                            tmp_value,
                            self.length if self.length else 32,
                            is_unsigned=False,
                        )
                    except ValueError:
                        raise ValueError("Invalid Input for this Field.")

    def get_value(self) -> str:
        if not self.value:
            raise RuntimeError(f"Field '{self.name}' has no value.")
        return self.value if self.length else ""

    def restore_value(self, value: str) -> bool:
        """
        Read value from binary str
        :Return: True means the value is OK, False means something goes wrong.
        """
        match self.type:
            case FieldType.FMT:
                if value not in [i.value for i in FMT._member_map_.values()]:
                    return False
                self.value = value

            case FieldType.CONDN:
                if value not in [i.value for i in CONDN._member_map_.values()]:
                    return False
                self.value = value

            case FieldType.EXPR:
                raise NotImplementedError(
                    "Decoding for expression included instruction hasn't been supported yet."
                )

            case _:
                if self.pos_flag and self.length * "0" == value:
                    return False
                self.value = value
        return True

    def get_origin_value(self):
        match self.type:
            case FieldType.GPR:
                return f"r{Instruction.bin2dec(self.value)}"
            case FieldType.FPR:
                return f"f{Instruction.bin2dec(self.value)}"
            case FieldType.BASE:
                return f"({Instruction.bin2dec(self.value)})"
            case FieldType.IMME:
                return str(Instruction.bin2dec(self.value, is_unsigned=False))

    def __repr__(self) -> str:
        return self.name


class Instruction:
    def __init__(self, name: str, fields: list[Field]):
        self.name = name
        self.fields = fields
        self.field_map = {f.name: f for f in fields}
        input_queue = [
            (i, field.input_order)
            for i, field in enumerate(self.fields)
            if field.input_order
        ]
        self.input_queue = [i[0] for i in sorted(input_queue, key=lambda item: item[1])]
        self.base_flag = False
        base_order = [i for i, f in enumerate(self.fields) if f.type == FieldType.BASE]
        if base_order:
            self.base_flag = True
            self.input_queue.append(base_order[0])
        self.auto_load = [f.name for f in fields if f.expression]

    def load_value(self, field_name, value):
        for f in self.fields:
            if f.name == field_name:
                f.load_value(value)
                break
        else:
            raise ValueError(f"Expected Field {field_name} Was Not Found.")

    def encode(self, args: str) -> str:
        split_args = [s.strip() for s in args.split(",")]
        if self.base_flag:
            index = split_args[-1].find("(")
            if index == -1:
                raise ValueError(f"Instruction {self.name} Has No Base.")
            base = split_args[-1][index + 1 : -1]
            split_args[-1] = split_args[-1][:index]
            split_args.append(base)

        for i, input_field in enumerate(self.input_queue):
            self.fields[input_field].load_value(split_args[i])

        # support exp in inst.
        if self.auto_load:
            value_map = {
                f.name: Instruction.bin2dec(f.value, True)
                for f in self.fields
                if f.value
            }
            for name in self.auto_load:
                self.field_map[name].load_value(value_map=value_map)

        return "".join(f.get_value() for f in self.fields)

    def decode(self, binary_str: str) -> str:
        progress = 0
        name_field: Field | None = None

        for f in self.fields:
            if f.length:
                working_str = binary_str[progress : progress + f.length]
                if f.value:
                    if working_str != f.value:
                        return ""
                else:
                    if not f.restore_value(working_str):
                        return ""

                progress += f.length
                if f.type in (FieldType.FMT, FieldType.CONDN):
                    name_field = f

        if name_field:
            match name_field.type:
                case FieldType.FMT:
                    self.name = (
                        self.name[:-3] + FMT._value2member_map_[name_field.value].name
                    )
                case FieldType.CONDN:
                    name_part = self.name.split(".")
                    self.name = ".".join(
                        [
                            name_part[0],
                            CONDN._value2member_map_[name_field.value].name,
                            name_part[2],
                        ]
                    )

        result = []

        for i in self.input_queue:
            f = self.fields[i]
            result.append(f.get_origin_value())
        if self.base_flag:
            result[-2] = result[-2] + result[-1]
            result.pop()

        return self.name.upper() + " " + ", ".join(result)

    def __repr__(self) -> str:
        return f"Inst {self.name}, fields: {self.fields}"

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
                    if 2**i + dec_num >= 0:
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
    def bin2dec(binary: str, is_unsigned: bool = True):
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


class InstructionLoader:
    @staticmethod
    def check_instruction_length(fields: list):
        """check if the sum of the length of the fields is 32"""
        total_length = sum(field.length for field in fields)
        if total_length != 32:
            raise ValueError("Invalid Length Value Found.")

    @staticmethod
    def from_csv(csv_file):
        instructions = {}
        with open(csv_file, mode="r") as file:
            reader = csv.reader(file)
            line_count = 0
            for row in reader:
                if line_count == 0:
                    line_count += 1
                    continue
                row = [i.lower().strip() for i in row]
                name, inst_type = row[0], row[1]
                fields = [Field.parse(f) for f in row[2:] if f]
                InstructionLoader.check_instruction_length(fields)
                instructions[name] = Instruction(name=name, fields=fields)
                line_count += 1
        logging.info(f"Load {line_count} instructions successfully.")

        return instructions

    @staticmethod
    def get_last(inst: Instruction):
        last_value = None
        for f in reversed(inst.fields[1:]):
            if f.input_order:
                return last_value
            if not last_value:
                last_value = f.value
            else:
                last_value = f.value + last_value
        return last_value

    @staticmethod
    def build_map(insts: dict[str, Instruction]):
        map = {}

        # op as primary index
        for i in insts.values():
            op = i.fields[0].value
            map.setdefault(op, [])
            map[op].append(i)

        # func/last fix code as secondary index
        for k, v in map.items():
            if len(v) == 1:
                continue

            inner_map = {"_": []}
            for i in v:
                last = InstructionLoader.get_last(i)
                if not last:
                    inner_map["_"].append(i)
                    continue

                inner_map.setdefault(last, [])
                inner_map[last].append(i)
            # length index
            length_map = {}
            for key, value in inner_map.items():
                if key == "_":
                    length_map["_"] = value
                else:
                    length_map.setdefault(len(key), {})
                    length_map[len(key)][key] = value

            length_list = list(length_map.keys())
            length_list.remove("_")
            length_map["length"] = sorted(length_list, reverse=True)
            map[k] = length_map

        return map


INSTRUCTIONS = InstructionLoader.from_csv(Path(__file__).parent / "instructions.csv")
INST_BIN_MAP = InstructionLoader.build_map(INSTRUCTIONS)
