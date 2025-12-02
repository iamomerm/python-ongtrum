### <ins> Ongtrum </ins>

Ongtrum is a Python test runner designed for speed <br>

## <ins> Why Ongtrum is Fast ? </ins>

<ins> Scan </ins> <br>

Recursively scans for test files in the project directory with a Cython-optimized filesystem scanner <br>

<ins> Parse </ins> <br>

Each file is parsed with a Cython-optimized AST parser <br>

<ins> Execute </ins> <br>

For each file, all its test classes and methods are executed in one go using Python’s exec <br>
To reduce overhead, files are processed in batches, keeping worker processes alive throughout the run <br>

<ins> Optional Parallelism </ins> <br>

Tests can be run across multiple processes with `--workers` <br>

## <ins> Benchmark </ins>

Execution Commands: <br>

- Unittests: `python -m unittest discover <Project Dir>` <br>
- PyTest: `python -m pytest <Project Dir> -s -q` <br>
- Ongtrum: `python -m ongtrum.py' -q -p <Project Dir>` <br>

Test Files: 5440 <br>
Test Class: 10880 <br>

- Unittests: 12.462s <br>
- PyTest: 27.217S <br>
- Ongtrum: 5.950s (vs Unittests 2 × Faster, vs PyTest 4.5 × Faster) <br>
