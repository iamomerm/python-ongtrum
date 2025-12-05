import ast

def parse(content: str):
    test_classes = []
    test_methods = {}
    imports = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return test_classes, test_methods, imports, None

    # Extract metadata
    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for n in node.names:
                imports.append(f"{module}.{n.name}")
        elif isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
            test_classes.append(node.name)
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef) and n.name.startswith('test')]
            test_methods[node.name] = methods

    # Compile
    codeobj = compile(tree, "<test>", "exec")

    return test_classes, test_methods, imports, codeobj
