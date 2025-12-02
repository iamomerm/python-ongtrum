
import ast
from cpython.dict cimport PyDict_New
from cpython.list cimport PyList_New, PyList_Append

def parse(str content):
    cdef list test_classes = []
    cdef dict test_methods = dict()
    cdef list imports = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return test_classes, test_methods, imports

    cdef object node, n, methods, module

    for node in tree.body:
        # IMPORTS
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for n in node.names:
                imports.append(f"{module}.{n.name}")

        # TEST CLASSES
        elif isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
            test_classes.append(node.name)

            methods = []
            for n in node.body:
                if isinstance(n, ast.FunctionDef) and n.name.startswith('test'):
                    methods.append(n.name)

            test_methods[node.name] = methods

    return test_classes, test_methods, imports
