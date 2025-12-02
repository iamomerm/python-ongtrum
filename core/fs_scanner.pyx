# cython: boundscheck=False, wraparound=False
from libc.string cimport memcmp
import os

def scan(str root_dir):
    """
    Recursively scan for test_*.py files.
    Yield only the file content (str) per file.
    Optimized for many files < 1 MB.
    """
    cdef str dirpath, fname
    cdef bytes bfname
    cdef const char* c_bfname
    cdef int fname_len
    cdef object f_content

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for fname in filenames:
            fname_len = len(fname)
            if fname_len < 9:
                continue
            bfname = fname.encode('utf-8')
            c_bfname = bfname
            # Check prefix "test_" and suffix ".py"
            if memcmp(c_bfname, b"test_", 5) == 0 and memcmp(c_bfname + fname_len - 3, b".py", 3) == 0:
                with open(os.path.join(dirpath, fname), 'r', encoding='utf-8') as f:
                    f_content = f.read()
                yield f_content


