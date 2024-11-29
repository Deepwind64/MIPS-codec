# MIPS-codec

This project is a MIPS Assembly and Machine Code Converter that allows encoding and decoding between MIPS assembly instructions and their corresponding binary machine code. It basically supports all instruction from the MIPS32® Instruction Set Manual Revision 6, see [Instruction CSV Introduction](#introduction-to-instruction-set-csv) for detail info. The program can be run both from the command line or through Python scripts for batch processing.

## Features

- **Assembly to Machine Code**: Convert MIPS assembly instructions into their corresponding 32-bit binary machine code.
- **Machine Code to Assembly**: Decode binary machine code into human-readable MIPS assembly instructions.
- **Instruction Set**: Supports R, I, and J type MIPS instructions defined in a CSV file.
  
## Project Structure

```plain-text
MIPS-codec
│  .gitignore
│  LICENSE
│  README.md
├─ examples
│     ├── assemble.txt
│     └── binary.txt
└─ src
    ├── core.py
    ├── codec.py
    ├── instructions.csv
    └── model.py

```

- **`example/`**: Contains sample input and output files for testing and demonstration.
- **`src/`**: Contains the main code for encoding, decoding, instruction handling, and parsing.
  - `core.py`: Defines the `ArgsError` class and exception handling.
  - `codec.py`: Implements encoding and decoding logic.
  - `model.py`: Defines the `Instruction` class and its subclasses for different instruction types (R, I, J).
  - `instructions.csv`: The instruction set defining different MIPS instructions.

## Installation

Clone the repository or download the files and place them in a directory.

Python version 3.10 or higher is required.

## Usage

### Command-line Interface

You can use the converter from the command line. There are two modes available: `encode` and `decode`.

### Available Arguments

- **`mode`**: Specifies the operation mode:
  - `encode`: Converts assembly code to binary machine code.
  - `decode`: Converts binary machine code to assembly code.

- **`-f, --input_file`**: Path to the input file containing instructions.

- **`-o, --output_file`**: Path to the output file. If not provided, the result is printed to the console.

### Example Usage

- Encoding from file:

   ```bash
   python src/codec.py encode -f ./example/assemble.txt -o ./output/binary.txt
   ```

- Decoding from file:

   ```bash
   python src/codec.py.py decode -f ./example/binary.txt -o ./output/assemble.txt
   ```

## Introduction to Instruction Set CSV  

Refer to The [MIPS32® Instruction Set Manual, Revision 6.06](https://s3-eu-west-1.amazonaws.com/downloads-mips/documents/MD00086-2B-MIPS32BIS-AFP-6.06.pdf)

### Included Instructions

This CSV file includes all instruction cases from MIPS Release 6 except for the following:

- All `Assembly Idioms` are not included:
  - `B`, `BGTC`, `BLEC`, `BGTUC`, `BLEUC`, `EHB`, `JR`, `JR.HB`, `LUI`, `NOP`
- Instructions that cannot be uniquely determined or converted based on machine code are not included:
  - Instructions containing exception codes that cannot be specified through assembly instructions: `BREAK`, `SYSCALL`, `TEQ`, `TGE`, `TGEU`, `TLT`, `TLTU`, `TNE`
  - Implementation-specific codes: `WAIT`, `COP2`
- Some instructions marked as deprecated in this version: `NAL, SSNOP`
- For instructions with multiple input methods like `JALR rs`, `JALR rd, rs`, only the method with the most inputs is implemented.
- The hint field of `JALR`, `JALR.HB` is set to 00000/0000.

### Main Addressing Modes Included

- Register Immediate Addressing: `ADD`
- Relative Addressing: `ADDIUPC`
- Base Addressing: `LBE`

### Meaning of Each Field

A `Field` is consisted of `Name`, `Length`, `Value`.

Name  

- Name is for human reading only and will not play a role in program parsing.

Length

- `0`: Indicates that this value does not appear in the final machine code and is an intermediate value
- Positive Integer

Value

- Regular binary number / 0
- `?[options]`: The value is determined internally by the program, each letter in options corresponds to a valid field value
- `- num`: Represents a value that needs to be entered by the user, num indicates the order of the value within the instruction, there can be multiple nums separated by commas
- `+ num`: Indicates that the input value must be greater than 0
- `~`: Indicates that the value enclosed in parentheses at the end of the instruction (base address)
- `Expression`: Indicates that the value is calculated using an expression formed from variables that have appeared before

### General Format of Fmt

| Binary Value | Format | Description |
|--------------|--------|-------------|
| 10000        | S      | Single-precision floating point (32-bit) |
| 10001        | D      | Double-precision floating point (64-bit) |
| 10011        | W      | 32-bit integer (Word)    |
| 10100        | L      | 64-bit integer (Long word)|

## Contributing

Feel free to fork the project, submit issues, or create pull requests for improvements or bug fixes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
