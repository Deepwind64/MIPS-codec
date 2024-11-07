from dataclasses import dataclass
import math

class ArgsError(RuntimeError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)



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
        if type(imme) is not int or imme<-2**(max_width-1) or imme>=2**(max_width-1):
            raise ArgsError(f"Invalid immediate {imme}")
        return imme
    
    @staticmethod
    def dec2bin(dec_num: int, bin_width: int, is_unsigned=True) -> str:
        if is_unsigned:
            py_bin_str = bin(dec_num)
            if (py_bin_str[0] == '-'):
                bin_str = py_bin_str[3:]
            else:
                bin_str = py_bin_str[2:]
        else:
            if (dec_num == 0):
                bin_str = '0'
            elif (dec_num > 0):
                # 补符号位0
                bin_str = '0' + bin(dec_num)[2:] 
            else:
                # 求负数补码
                for i in range(int(math.log2(-dec_num)),32):
                    if (2**i + dec_num >= 0):
                        bin_str = bin(2**(i+1) + dec_num)[2:]
                        break

        if (bin_width < len(bin_str)):
            raise ArgsError(f"Immediate {dec_num} exceeds the data width {bin_width}.")
        else:
            # 实际位宽小于设定位宽则补符号位
            if is_unsigned:
                bin_str = '0' * (bin_width - len(bin_str)) + bin_str
            else:
                bin_str = bin_str[0] * (bin_width - len(bin_str)) + bin_str
        return bin_str
    
    @staticmethod
    def bin2dec(binary: str, is_unsigned: bool = False):
        """取反加一，转换为十进制并添加负号"""
        if is_unsigned:
            result = int(binary, 2)
        else:
            if binary[0] == '1':
                reversed_bin = ''.join(['1' if bit == '0' else '0' for bit in binary[1:]])
                result = -int(bin(int(reversed_bin, 2) + 1)[2:], 2)
            else:
                result = int(binary[1:], 2)
        
        return result


@dataclass
class RInstruction(Instruction):
    Func: str = ""
    Rs: int = -1
    Rt: int = -1
    Rd: int = -1
    Shamt: int = 0
    op: str = "000000"
    is_unsigned: bool = False
    

    def add_args(self, args: str):
        reg_amount = 3
        try:
            # type check
            f_args = [reg for reg in args.split(',')]
            
            match self.Func:
                # sll srl sra
                case "000000" | "000010" | "000011":
                    self.Rd, self.Rs = int(f_args[0][1:]), 0
                    self.Rt, self.Shamt = int(f_args[1][1:]), self.check_imme(int(f_args[2]), max_width=5)
                    reg_amount = 2
                # sllv srlv srav
                case "000100" | "000110" | "000111":
                    self.Rd, self.Rt, self.Rs = [int(reg[1:]) for reg in f_args]
                # jr
                case "001000":
                    self.Rs = int(f_args[0][1:])
                    reg_amount = 1
                case _:
                    self.Rd, self.Rs, self.Rt = [int(reg[1:]) for reg in f_args]

            # format check
            if sum(1 for reg in f_args if reg[0]=="$") != reg_amount:
                raise ArgsError(f"Invalid reg in {args}")

            # value check
            for i in (self.Rd, self.Rt, self.Rs):
                if i<0 or i>31:
                    raise ArgsError(f"Invalid reg '{i}'")
        except ArgsError as e:
            raise e
        except Exception as e:
            raise ArgsError(f"Invalid args in {args}")


    def encode(self, args: str) -> str:
        self.add_args(args)
        return self.op + "".join(self.dec2bin(i, 5) for i in (self.Rs, self.Rt, self.Rd, self.Shamt)) + self.Func

    def decode(self, binary_str: str) -> str:
        rs = int(binary_str[6:11], 2)
        rt = int(binary_str[11:16], 2)
        rd = int(binary_str[16:21], 2)
        shamt = int(binary_str[21:26], 2)
        func = binary_str[26:32]

        name = [name for name, inst in instructions["000000"].items() if inst.Func == func]

        if name:
            name = name[0]
            match name:
                case "sll" | "srl" | "sra":
                    inst_str = f"{name} ${rd},${rt},{shamt}"
                case "sllv" | "srlv" | "srav":
                    inst_str = f"{name} ${rd},${rt},${rs}"
                case "jr":
                    inst_str = f"{name} ${rs}"
                case _:
                    inst_str = f"{name} ${rd},${rs},${rt}"
        else:
            raise ArgsError("Unknown function code.")

        return inst_str
    
@dataclass
class IInstruction(Instruction):
    Rs: int = -1
    Rt: int = -1
    Imme: int = -1
    is_unsigned: bool = False

    def add_args(self, args: str):
        reg_amount = 2
        try:
            f_args = args.split(',')
            
            match self.op:
                # lui
                case "001111":
                    self.Rt, self.Imme = int(f_args[0][1:]), self.check_imme(int(f_args[1]), max_width=16)
                    reg_amount = 1
                # lw sw
                case "100011" | "101011":
                    self.Rt = int(f_args[0][1:])
                    split_index = f_args[1].index("(")
                    self.Rs = int(f_args[1][split_index+2:-1])
                    self.Imme = self.check_imme(int(f_args[1][:split_index]))
                    
                    if f_args[1][split_index:split_index+2] != "($" or f_args[1][-1] != ")":
                        raise ArgsError(f"Invalid args in {args}")
                    reg_amount = 1
                case _:
                    self.Rt, self.Rs = int(f_args[0][1:]), int(f_args[1][1:])
                    self.Imme = self.check_imme(int(f_args[2]), max_width=16)
        
            # format check
            if sum(1 for reg in f_args if reg[0]=="$") != reg_amount:
                raise ArgsError(f"Invalid reg in {args}")

            # value check
            for i in (self.Rt, self.Rs):
                if i<0 or i>31:
                    raise ArgsError(f"Invalid reg '{i}'")
        except ArgsError as e:
            raise e
        except Exception as e:
            raise ArgsError(f"Invalid args in {args}")

    def encode(self, args: str) -> str:
        self.add_args(args)
        imme_bin = self.dec2bin(self.Imme, bin_width=16, is_unsigned=self.is_unsigned)
        return self.op + self.dec2bin(self.Rs, 5) + self.dec2bin(self.Rt, 5) + imme_bin
    
    def decode(self, binary_str: str) -> str:
        op = binary_str[:6]
        rs = int(binary_str[6:11], 2)
        rt = int(binary_str[11:16], 2)
        imme = self.bin2dec(binary_str[16:], self.is_unsigned)
        
        name = [name for name, inst in instructions.items() if name != "000000" and inst.op == op]

        if name:
            name = name[0]
            match name:
                case "lui":
                    inst_str = f"{name} ${rt},{imme}"
                case "lw" | "sw":
                    inst_str = f"{name} ${rt},{imme}(${rs})"
                case _:
                    inst_str = f"{name} ${rt},${rs},{imme}"
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
    
        name = [name for name, inst in instructions.items() if name != "000000" and inst.op == op]

        if name:
            name = name[0]
            inst_str = f"{name} {address}"
        else:
            raise ArgsError("Unknown op code.")

        return inst_str

instructions = {
    "000000": {
        "add": RInstruction(Func="100000"),
        "addu": RInstruction(Func="100000"),
        "sub": RInstruction(Func="100010"),
        "subu": RInstruction(Func="100011", is_unsigned=True),
        "and": RInstruction(Func="100100"),
        "or": RInstruction(Func="100101"),
        "xor": RInstruction(Func="100110"),
        "nor": RInstruction(Func="100111"),
        "slt": RInstruction(Func="101010"),
        "sltu": RInstruction(Func="101011", is_unsigned=True),
        "sll": RInstruction(Func="000000", Rs=0),
        "srl": RInstruction(Func="000010", Rs=0),
        "sra": RInstruction(Func="000011", Rs=0),
        "sllv": RInstruction(Func="000100"),
        "srlv": RInstruction(Func="000110"),
        "srav": RInstruction(Func="000111"),
        "jr": RInstruction(Func="001000", Rt=0, Rd=0)
        },

    "addi": IInstruction(op="001000"),
    "addiu": IInstruction(op="001001", is_unsigned=True),
    "andi": IInstruction(op="001100"),
    "ori": IInstruction(op="001101"),
    "xori": IInstruction(op="001110"),
    "lui": IInstruction(op="001111", Rs=0),
    "lw": IInstruction(op="100011"),
    "sw": IInstruction(op="101011"),
    "beq": IInstruction(op="000100"),
    "bne": IInstruction(op="000101"),
    "slti": IInstruction(op="001010"),
    "sltiu": IInstruction(op="001011", is_unsigned=True),

    "j": JInstruction(op="000010"),
    "jal": JInstruction(op="000011")
}

def encode_one(instruction: str):
    split_inst = instruction.strip().lower().split()
    format_inst = instructions.get(split_inst[0])
    if not format_inst:
        # search I-Type
        format_inst = instructions["000000"].get(split_inst[0])

    if format_inst is None:
        raise ArgsError("Unknown Instrction.")
    
    # remove possible space between args
    return format_inst.encode("".join(split_inst[1:]))

def encode_batch(insts="", input_file="", output_file=""):
    encode_insts = []
    if insts and input_file:
        raise ArgsError("Can't haddle two input at a time.")

    if insts:
        for inst in insts.split("\n"):
            try:
                encode_insts.append(encode_one(inst))
            except Exception as e:
                encode_insts.append(str(e))
    elif input_file:
        ...
    else:
        raise ArgsError("No input.")
    
    if output_file:
        ...
    else:
        print(*encode_insts, sep="\n")

def decode_one(binary_str: str) -> str:
    op = binary_str[:6]
    if op == "000000":
        inner_insts = instructions[op]
    else:
        inner_insts = instructions
        
    format_inst = next((inst for inst in inner_insts.values() if 
                        isinstance(inst, Instruction) and inst.op == op), None)
    if format_inst is None:
        raise ArgsError("Unknown Instrction.")
    return format_inst.decode(binary_str)

def decode_batch(binaries: str):
    decoded_insts = []
    for binary in binaries.split("\n"):
        try:
            decoded_insts.append(decode_one(binary))
        except Exception as e:
            decoded_insts.append(str(e))
    print(*decoded_insts, sep="\n")

insts = """lui $1,100
add $1,$2,$3
sll $1,$2,10
sllv $1,$2,$3
jr $31
addi $1,$2,100
lw $1,10($2)
bne $1,$2,10
j 10000"""

bin_insts = """00111100000000010000000001100100
00000000010000110000100000100000
00000000000000100000101010000000
00000000011000100000100000000100
00000011111000000000000000001000
00100000010000010000000001100100
10001100010000010000000000001010
00010100010000010000000000001010
00001000000000000010011100010000"""

if __name__ == "__main__":
    decode_batch(binaries=bin_insts)