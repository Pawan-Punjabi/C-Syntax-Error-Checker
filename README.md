C Syntax Checker (lightweight)

This small Python project provides a lightweight C syntax checker and a Tkinter GUI.

## Abstract
The C Syntax Checker is a specialized tool designed to assist developers and students in identifying common syntax errors in C programming. By utilizing a heuristic-based approach and regular expressions, it provides immediate feedback on issues such as invalid identifiers, missing semicolons, and unclosed literals. This project aims to bridge the gap between writing code and the full compilation process, offering a faster way to catch frequent mistakes.

## Advantages
- **Immediate Feedback**: Quickly identifies common errors without needing a full compiler.
- **Educational Tool**: Helps beginners understand C syntax rules through clear error reporting.
- **Lightweight**: Low system requirements and fast execution.
- **Portability**: Built with Python, making it easy to run across different environments.
- **User-Friendly**: Provides both a web interface and a Tkinter-based GUI for ease of use.

Features
- Remove comments and basic preprocessing
- Heuristic checks: invalid identifiers, missing semicolons, unclosed quotes, likely keyword typos
- Simple GUI to open files, view source, and list errors

Files
- `checker.py` - core analysis logic
- `main.py` - Tkinter GUI
- `tests_test_checker.py` - small unit tests

Run
- To launch the GUI: python main.py
- To run the tests: install pytest and run pytest in the project folder

Notes
This is intentionally lightweight — not a full C parser. It implements the checks shown in the user's notes: invalid variable names, missing semicolons, incorrect keywords, unclosed quotes, and basic error reporting with line numbers.
