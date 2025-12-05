import os

# Configuration
ROOT_DIR = 'C:/Temp/test_project'
DEPTH = 4
SUBDIRS_PER_LEVEL = 4
TEST_FILES_PER_DIR = 16

# Counters
test_file_count = 0

# Templates
TEST_CLASS_TEMPLATE = """
import unittest

class Test{classname}(unittest.TestCase):
    def test_example(self):
        {body}
"""

def create_test_file(module_dir, index):
    """
    fail_every_n: every n-th test will fail, rest pass
    """
    global test_file_count
    file_name = f'test_{index}.py'
    path = os.path.join(module_dir, file_name)
    with open(path, 'w') as f:
        for i in range(2):  # Classes per file
            class_index = f'{index}_{i}'
            # body = 'assert False, "Failure"' if (i % 2 == 2) else 'assert True'
            body = 'assert True'
            f.write(TEST_CLASS_TEMPLATE.format(classname=class_index, body=body))
    test_file_count += 1

def create_tree(current_dir, depth=0):
    if depth >= DEPTH:
        return

    # Create subdirectories
    for i in range(SUBDIRS_PER_LEVEL):
        subdir = os.path.join(current_dir, f'pkg_{depth}_{i}')
        os.makedirs(subdir, exist_ok=True)
        # Package init
        with open(os.path.join(subdir, '__init__.py'), 'w') as f:
            f.write("# package init\n")
        # Test files
        for k in range(TEST_FILES_PER_DIR):
            create_test_file(subdir, f'{depth}_{i}_{k}')
        # Recurse
        create_tree(subdir, depth + 1)

if __name__ == '__main__':
    os.makedirs(ROOT_DIR, exist_ok=True)
    create_tree(ROOT_DIR)
    print(f"Total test files created: {test_file_count}")
