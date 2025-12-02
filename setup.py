from setuptools import setup
from Cython.Build import cythonize

setup(
    name='ongtrum_extensions',
    ext_modules=cythonize(
        ['core/fs_scanner.pyx', 'core/ast_parser.pyx'],
        compiler_directives={'language_level': '3'},
    )
)
