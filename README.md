### <ins> Ongtrum </ins>

Ongtrum is a Python test runner designed for speed <br>

Installation: `pip install python-ongtrum` <br>

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

## <ins> Features </ins>

<ins> Test Suites </ins> <br>

Organize tests into named suites using the @suites decorator <br>

```python
from annotation import suites


class TestSuite:
    @suites(['suite_one', 'suite_two'])
    def test_dummy_1(self):
        assert 1 == 1
```

<ins> Test Parameters </ins> <br>

Organize tests into named suites using the @suites decorator <br>

```python
from annotation import parameters


class TestParameter:
    @parameters([{'a': 1, 'b': 2}, {'a': 10, 'b': 20}])
    def test_add(self, a, b):
        assert a in [1, 10]
        assert b in [2, 20]
```

<ins> Test Preps </ins> <br>

Ongtrum allows you to define reusable preparation functions (“preps”) in dedicated prep files, <br>
which are automatically loaded for your tests <>

Scopes: <br>

- Session - Run once per test session - Useful for expensive setup shared by all tests - Cached for the session <br>
- class - Run once per test class - Shared among all methods in that class - Cached for the class <br>
- method - Run for each test method individually - Re-run for every method call <br>

**_Configuration File_** <br>

By default, Ongtrum looks for an `ongtrum.yaml` file: <br>

- At the project root when running a directory <br>
- In the parent directory when running a single test file <br>

Alternatively, you can specify a config file explicitly using `ongtrum -c path/to/ongtrum.yaml` <br>

**_Configuration Example_** <br>

```yaml
prep_files:
  - preps/session_preps.py
  - preps/class_preps.py
  - preps/method_preps.py
```

**_Declaring a Prep_** <br>

```python
from annotation import prep


@prep(scope='session')
def session_prep():
    return 'Session Prep'


@prep(scope='class')
def class_prep():
    return 'Class Prep'


@prep(scope='method')
def method_prep():
    return 'Method Prep'
```

**_Applying a Prep_**

```python
from annotation import preps


@preps('class_prep')
class TestExample:

    @preps('method_prep')
    def test_something(self, method_prep):
        assert self.class_prep == 'Class Prep'
        assert method_prep == 'Method Prep'
```

<ins> Test Filter </ins> <br>

You can run a subset of tests using the `-f / --filter` option <br>
Filter format: `<File>.<Class>.<Method>` <Br>
You can also use wildcards (*) for flexible matching <br>

**_Examples:_** <br>

```
ongtrum -p tests/test_example.py -f test_example
ongtrum -p tests/test_example.py -f test_example.TestClass
ongtrum -p tests/test_example.py -f test_example.TestClass.test_method

ongtrum -p tests/test_example.py -f *.TestClass
ongtrum -p tests/test_example.py -f *.*.test_method
```
