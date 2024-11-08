import unittest
from pathlib import Path

from mips_codec.core import ArgsError
from mips_codec.encoding import encode_one, decode_one, process_batch
import os


class TestMIPSCodec(unittest.TestCase):

    def test_encode_one_valid(self):
        """Test encoding a valid MIPS instruction to machine code."""
        instruction = "add $1, $2, $3"
        result = encode_one(instruction)
        expected_result = "00000000010000110000100000100000"
        self.assertEqual(result, expected_result)

    def test_encode_one_invalid(self):
        """Test encoding an invalid MIPS instruction."""
        instruction = "invalid_instruction $1, $2, $3"
        with self.assertRaises(ArgsError):
            encode_one(instruction)

    def test_decode_one_valid(self):
        """Test decoding a valid machine code to MIPS instruction."""
        binary_str = "00000000010000110000100000100000"
        result = decode_one(binary_str)
        expected_result = "add $1, $2, $3"
        self.assertEqual(result, expected_result)

    def test_decode_one_invalid(self):
        """Test decoding an invalid binary string."""
        binary_str = "11111111111111111111111111111111"
        with self.assertRaises(ArgsError):
            decode_one(binary_str)

    def test_process_batch_encode_mode(self):
        """Test batch processing in encode mode."""
        input_str = "add $1, $2, $3\nsll $1,$2,10"
        expected_output = "00000000010000110000100000100000\n00000000000000100000101010000000"
        result = process_batch("encode", input_str=input_str)
        self.assertEqual(result.strip(), expected_output)

    def test_process_batch_decode_mode(self):
        """Test batch processing in decode mode."""
        input_str = "00000000010000110000100000100000\n00000000000000100000101010000000"
        expected_output = "add $1, $2, $3\nsll $1, $2, 10"
        result = process_batch("decode", input_str=input_str)
        self.assertEqual(result.strip(), expected_output)

    def test_process_batch_invalid_mode(self):
        """Test batch processing with an invalid mode."""
        with self.assertRaises(ArgsError):
            process_batch("invalid_mode")

    def test_file_input_output(self):
        """Test file-based input and output for encoding and decoding."""
        input_file = Path("test/assemble.txt")
        output_file = Path("test/binary.txt")

        os.makedirs(input_file.parent, exist_ok=True)

        with open(input_file, "w") as f:
            f.write("add $1, $2, $3\nsll $1, $2, 10")

        process_batch("encode", input_file=input_file, output_file=output_file)

        with open(output_file, "r") as f:
            output = f.read().strip()

        expected_output = "00000000010000110000100000100000\n00000000000000100000101010000000"
        self.assertEqual(output, expected_output)

        os.remove(input_file)
        os.remove(output_file)
        os.removedirs(input_file.parent)

    def test_error_handling_in_file_operations(self):
        """Test error handling for missing files."""
        with self.assertRaises(ArgsError):
            process_batch("encode", input_file="non_existent_file.txt")

    def test_check_immediate_range(self):
        """Test immediate value range checking."""
        from mips_codec.model import Instruction

        # Test a valid immediate
        self.assertEqual(Instruction.check_imme(15, 5), 15)

        # Test an out-of-range immediate
        with self.assertRaises(ArgsError):
            Instruction.check_imme(32, 5)

    def test_instruction_decoding_methods(self):
        """Test decoding methods for R, I, and J instructions."""
        from mips_codec.model import RInstruction, IInstruction, JInstruction

        r_inst = RInstruction(func="100000")
        self.assertEqual(r_inst.decode("00000000010000110000100000100000"), "add $1, $2, $3")

        i_inst = IInstruction(op="001000")
        self.assertEqual(i_inst.decode("00100000010000010000000001100100"), "addi $1, $2, 100")

        j_inst = JInstruction(op="000010")
        self.assertEqual(j_inst.decode("00001000000000000010011100010000"), "j 10000")


if __name__ == "__main__":
    unittest.main()
