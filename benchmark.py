import subprocess
import time

project_dir = r'C:\Temp\test_project'

# Unittest
start = time.time()
subprocess.run(['python', '-m', 'unittest', 'discover', project_dir])
unittest_time = time.time() - start

# Ongtrum
start = time.time()
subprocess.run(['python', 'ongtrum.py', '-q', '--project', project_dir])
ongtrum_time = time.time() - start

# PyTest
start = time.time()
subprocess.run(['pytest', project_dir, '-s', '-q'])
pytest_time = time.time() - start

print(f'Unittest: {unittest_time:.3f}s')
print(f'Ongtrum : {ongtrum_time:.3f}s')
print(f'PyTest  : {pytest_time:.3f}s')
