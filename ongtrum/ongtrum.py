import argparse
import atexit
import importlib.util
import inspect
import marshal
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from time import time
from typing import Optional, Any

import yaml
from ongtrum.core.ast_parser import parse  # noqa
from ongtrum.core.fs_scanner import scan  # noqa

from ongtrum.session import Session


@dataclass
class TestSpec:
    file_name: Optional[str] = None
    cls_name: Optional[str] = None
    method_name: Optional[str] = None
    status: Optional[bool] = None
    error: Optional[str] = None
    params: Optional[any] = None


@dataclass
class ResultSpec:
    status: bool
    file_name: str
    cls_name: str
    method_name: str
    params_exp: str
    error: Optional[Any] = None

    def __str__(self):
        if self.status:
            return f'\033[92m[PASS]\033[0m {self.file_name}.{self.cls_name}.{self.method_name}{self.params_exp}'
        else:
            return f'\033[91m[FAIL]\033[0m {self.file_name}.{self.cls_name}.{self.method_name}{self.params_exp} → {self.error}'


@dataclass
class ConfigSpec:
    prep_files: Optional[list[str]] = None


def parse_ongtrum_config(project: str, config_file: str = None) -> Optional[ConfigSpec]:
    """
    Reads an 'ongtrum.yaml' config file and returns a list of prep files.

    Args:
        project: Project root directory or a test file path.
        config_file: Config file path (absolute or relative to project root). Defaults to 'ongtrum.yaml'.

    Returns:
        ConfigSpec with absolute paths to prep files, or None if config does not exist.
    """
    config_file = config_file or 'ongtrum.yaml'
    project_root = project if os.path.isdir(project) else os.path.dirname(project)
    config_path = config_file if os.path.isabs(config_file) else os.path.join(project_root, config_file)

    if not os.path.exists(config_path):
        return None

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}

    prep_files = config.get('prep_files', [])
    if not isinstance(prep_files, list):
        raise ValueError('Invalid "prep_files" in config file, must be a list')

    return ConfigSpec(prep_files=[os.path.join(project_root, p) for p in prep_files])


def passes_filter(value: str, filter_value: Optional[str]) -> bool:
    """
    Determines whether a given value passes a filter

    Args:
        value (str): The value to test (file name, class name, method name)
        filter_value (Optional[str]): The filter to apply - Can be:
            - None or empty: always passes
            - '*': wildcard, always passes
            - specific string: passes only if `value == filter_value`

    Returns:
        bool: True if the value passes the filter, False otherwise
    """
    return not filter_value or filter_value == '*' or value == filter_value


def run_method(file_name: str, instance: Any, cls_name: str, method_name: str) -> list[TestSpec]:
    results = []
    method = getattr(instance, method_name, None)
    if not method:
        results.append(TestSpec(file_name, cls_name, method_name, False, 'MethodNotFound'))
        return results

    # Method Preps
    prep_names = getattr(method, '__preps__', [])
    prep_values = run_preps('method', prep_names) or {}

    # Parameter Sets
    param_sets = getattr(method, '__params__', [{}])

    for param_set in param_sets:
        args = []
        sig = inspect.signature(method)
        for name in sig.parameters.keys():
            if name in param_set:
                args.append(param_set[name])
            elif name in prep_values:
                args.append(prep_values[name])
            else:
                args.append(None)

        try:
            method(*args)
            results.append(TestSpec(file_name, cls_name, method_name, True, params=args))
        except Exception as e:
            results.append(TestSpec(file_name, cls_name, method_name, False, f'{type(e).__name__} - {str(e) or "Undefined"}', params=args))

    return results


def worker_run_files(batch: list, test_filter: Any = None, suite: str = None, session_prep_values: dict = None) -> list[TestSpec]:
    results = []

    # In multiprocessing, each worker gets its own memory space, so Session() is re-initialized
    # To solve this a shallow copy of the session prep results is injected
    if session_prep_values:
        Session().prep_cache['session'] = session_prep_values.copy()

    for file_name, test_methods, code_bytes in batch:
        # Apply File Filter
        if test_filter and test_filter.file_name and test_filter.file_name != '*' and file_name != test_filter.file_name:
            continue

        # Apply Class and Method Filters
        filtered_test_methods = {}
        for cls_name, method_names in test_methods.items():
            if test_filter and test_filter.cls_name and test_filter.cls_name != '*' and cls_name != test_filter.cls_name:
                continue

            filtered_methods = [
                m for m in method_names
                if not test_filter or not test_filter.method_name or test_filter.method_name == '*' or m == test_filter.method_name
            ]
            if filtered_methods:
                filtered_test_methods[cls_name] = filtered_methods

        if not filtered_test_methods:
            continue

        # Compile Test File Into a Namespace
        test_namespace = {'__builtins__': __builtins__}
        try:
            code_obj = marshal.loads(code_bytes)
            exec(code_obj, test_namespace)
        except Exception as e:
            for cls_name, methods in filtered_test_methods.items():
                for m in methods:
                    results.append(TestSpec(file_name, cls_name, m, False, f'ExecError: {e}'))
            continue

        # Run Tests
        for cls_name, method_names in filtered_test_methods.items():
            cls = test_namespace.get(cls_name)
            if not cls:
                for m in method_names:
                    results.append(TestSpec(file_name, cls_name, m, False, 'ClassNotFound'))
                continue

            instance = cls()  # noqa

            # Session Preps Injection to Class
            for name, val in Session().prep_cache['session'].items():
                setattr(instance, name, val)

            # Class Preps Injection to Class
            class_preps = getattr(cls, '__preps__', [])
            class_vals = run_preps('class', class_preps)
            for name, val in class_vals.items():
                setattr(instance, name, val)

            # Suites & Run Methods
            for method_name in method_names:
                method = getattr(instance, method_name)
                method_suites = getattr(method, '__suites__', [])
                if suite and suite not in method_suites:
                    continue
                results.extend(run_method(file_name, instance, cls_name, method_name))

    return results


def load_prep_file(file_path: str):
    """
    Import a prep file dynamically so that all @prep decorators run
    and register preps into Session()
    """
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def run_preps(scope: str, prep_names: list[str]):
    """
    Runs the prep functions for the given scope and returns their results

    Behavior:
    - Looks up prep functions by name in Session().preps[scope]
    - 'session' and 'class' scoped preps are cached in Session().prep_cache,
      so they are only executed once per session or per class
    - 'method' scoped preps are always re-run for each method invocation
    - Returns a dictionary mapping prep names to their computed values
    """
    session = Session()
    cache = session.prep_cache.get(scope, {})

    results = {}
    for name in prep_names:
        fn = session.preps[scope].get(name)
        if fn:
            if scope in ('session', 'class') and name in cache:
                results[name] = cache[name]
            else:
                results[name] = fn()
                if scope in ('session', 'class'):
                    cache[name] = results[name]
    return results


def run(
        project: str,
        config: str = None,
        max_workers: Optional[int] = None,
        quiet: bool = False,
        batch_size: int = None,
        suite: Optional[str] = None,
        test_filter: Optional[str] = None
) -> dict:
    start_time = time()
    collected_tests = 0

    # Load Config
    configuration = parse_ongtrum_config(project, config)

    if not configuration:
        print('WARNING: No Config Found !')

    if configuration and configuration.prep_files:
        for prep_file in configuration.prep_files:
            if os.path.exists(prep_file):
                load_prep_file(prep_file)
            else:
                print(f'WARNING: Prep File {prep_file} Not Found !')

    if not quiet:
        print(f'Project: {project}')
        print(f'Suite: {suite}')
        print(f'Filter: {test_filter}')
        print(f'Max Workers: {max_workers or 1}')
        if max_workers and max_workers > 1:
            print(f'Batch Size: {batch_size or "Dynamic"}')

    test_spec = TestSpec()

    # Prepare Test Filter
    if test_filter:
        parts = [p.strip() for p in test_filter.split('.')]
        if not 1 <= len(parts) <= 3:
            raise ValueError('Invalid test filter format: use file, file.class, or file.class.method')
        parts += [None] * (3 - len(parts))
        test_spec.file_name, test_spec.cls_name, test_spec.method_name = parts

    all_tasks = []

    # Temporarily add the project root to sys.path so test modules can be imported
    # Automatically remove it on program exit to avoid polluting sys.path
    sys.path.insert(0, project)
    atexit.register(lambda: sys.path.pop(0) if sys.path and sys.path[0] == project else None)

    # Determine Files to Process
    if os.path.isdir(project):
        files_to_process = scan(project)  # Returns list of (file_name, content)
    elif os.path.isfile(project) and project.endswith('.py'):
        with open(project, 'r', encoding='utf-8') as f:
            content = f.read()
        files_to_process = [(os.path.basename(project), content)]
    else:
        raise ValueError(f'Invalid project path: {project}')

    for file_name, content in files_to_process:
        test_classes, test_methods, _imports, code_obj = parse(content)
        if not test_classes:
            continue
        collected_tests += sum(len(m) for m in test_methods.values())

        # Marshal the compiled code object into bytes so it can be sent to worker processes
        # (Multiprocessing requires objects to be pickleable)
        code_bytes = marshal.dumps(code_obj)

        all_tasks.append((file_name.removesuffix('.py'), test_methods, code_bytes))

    if not quiet:
        print('\n- - - Results - - -\n')

    def repr_result(_result: TestSpec) -> ResultSpec:
        """ Returns a string representation of the test result """
        params_exp = f'[{_result.params}]' if _result.params else ''

        return ResultSpec(
            status=_result.status,
            file_name=_result.file_name,
            cls_name=_result.cls_name,
            method_name=_result.method_name,
            params_exp=params_exp,
            error=_result.error
        )

    reprs = []

    # Session Preps
    session = Session()
    run_preps('session', prep_names=list(session.preps['session'].keys()))
    session_prep_cache = session.prep_cache['session']

    # Single Worker
    if not max_workers or max_workers == 1:
        for task in all_tasks:
            results = worker_run_files([task], test_spec, suite, session_prep_cache)
            for r in results:
                reprs.append(repr_result(r))

    # Multi-Worker
    else:
        print(
            '\033[93m[Warning]\033[0m Multiprocessing should be used for heavy or long-running tests'
            'For simple tests, it may slow down execution due to process startup overhead'
        )

        # Split all test files into batches for multiprocessing
        # Each batch contains up to `batch_size` files - workers process all tests in their assigned files
        batch_size = batch_size or max(1, collected_tests // max_workers)
        batches = [all_tasks[i:i + batch_size] for i in range(0, len(all_tasks), batch_size)]

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker_run_files, batch, test_spec, suite, session_prep_cache) for batch in batches]
            for future in as_completed(futures):
                for r in future.result():
                    reprs.append(repr_result(r))

    if not quiet:
        print('\n'.join(str(r) for r in reprs))

    executed_tests = len(reprs)
    total_failures = sum(1 for r in reprs if not r.status)

    # Summary
    print('\n- - - Summary - - -\n')
    print(f'Collected: {collected_tests}')
    print(f'Executed: {executed_tests} / {collected_tests}')
    print(f'Failed: {total_failures}')
    print(f'Passed: {executed_tests - total_failures}')
    print(f'Total Time: {time() - start_time:.2f} seconds')

    return {
        'collected': collected_tests,
        'executed': executed_tests,
        'failed': total_failures,
        'passed': executed_tests - total_failures,
        'time': time() - start_time
    }


def main():
    parser = argparse.ArgumentParser(description='Ongtrum — Fast Python Test Runner')
    parser.add_argument('-p', '--project', type=str, required=True, help='Root directory of the test project')
    parser.add_argument('-w', '--workers', type=int, default=None, help='Number of parallel test processes')
    parser.add_argument('-bs', '--batch-size', type=int, default=None, help='Number of test files each worker processes at once (default: 64)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Run in quiet mode (minimal output)')
    parser.add_argument('-s', '--suite', type=str, required=False, help='Test suite to run')
    parser.add_argument('-f', '--filter', type=str, help='Run only a specific test: file, file.class, or file.class.method')
    parser.add_argument('-c', '--config', type=str, required=False, default='ongtrum.yaml', help='Path to Ongtrum config file ("ongtrum.yaml")')

    args = parser.parse_args()

    if not os.path.exists(args.project):
        raise ValueError(f'Project {args.project} does not exist!')

    run(
        args.project,
        config=args.config,
        max_workers=args.workers,
        quiet=args.quiet,
        batch_size=args.batch_size,
        suite=args.suite,
        test_filter=args.filter
    )


if __name__ == '__main__':
    main()
