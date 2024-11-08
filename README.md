# MIPS-codec

This project is a MIPS Assembly and Machine Code Converter that allows encoding and decoding between MIPS assembly instructions and their corresponding binary machine code. It supports a variety of MIPS instruction formats including R, I, and J types. The program can be run both from the command line or through Python scripts for batch processing.

## Features

- **Assembly to Machine Code**: Convert MIPS assembly instructions into their corresponding 32-bit binary machine code.
- **Machine Code to Assembly**: Decode binary machine code into human-readable MIPS assembly instructions.
- **Instruction Set**: Supports R, I, and J type MIPS instructions defined in a CSV file.
  
## Project Structure

```
MIPS-codec
│  .gitignore
│  LICENSE
│  README.md
│  examples
│      ├── assemble.txt
│      └── binary.txt
├── src
│  └── mips_codec
│      ├── core.py
│      ├── encoding.py
│      ├── instructions.csv
│      └── model.py
└── tests
    └── test_main_func.py
```

- **`example/`**: Contains sample input and output files for testing and demonstration.
- **`src/mips_codec/`**: Contains the main code for encoding, decoding, instruction handling, and parsing.
  - `core.py`: Defines the `ArgsError` class and exception handling.
  - `encoding.py`: Implements encoding and decoding logic.
  - `model.py`: Defines the `Instruction` class and its subclasses for different instruction types (R, I, J).
  - `instructions.csv`: The instruction set defining different MIPS instructions.
- **`tests/`**: Contains unit tests for the core functionality.

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
   python src/mips_codec/encoding.py encode -f ./example/assemble.txt -o ./output/binary.txt
   ```

- Decoding from file:

   ```bash
   python src/mips_codec/encoding.py decode -f ./example/binary.txt -o ./output/assemble.txt
   ```

## Testing

The project includes unit tests located in the `tests/test_main_func.py` file. These tests validate the core functionality of encoding, decoding, and error handling.

To run the tests, make sure you have **pytest** installed and use the following command:

```bash
pytest
```

## Contributing

Feel free to fork the project, submit issues, or create pull requests for improvements or bug fixes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

If you need more detailed information on MIPS instructions or the specific implementation of encoding and decoding, please refer to the `instructions.csv` file or the respective code in the `src/mips_codec/` folder.