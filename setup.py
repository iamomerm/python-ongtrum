from setuptools import setup
from Cython.Build import cythonize

setup(
    name='python-ongtrum',
    packages=['ongtrum', 'ongtrum.core'],
    ext_modules=cythonize(
        ['ongtrum/core/fs_scanner.pyx', 'ongtrum/core/ast_parser.pyx'],
        compiler_directives={'language_level': '3'},
    ),
)