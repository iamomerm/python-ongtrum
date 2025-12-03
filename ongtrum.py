import argparse
import atexit
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from time import time
from typing import Optional, Any

import yaml
from ast_parser import parse  # noqa
from fs_scanner import scan  # noqa


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


def parse_ongtrum_config(project_root: str) -> Optional[ConfigSpec]:
    """ Reads 'ongtrum_config.yaml' at the project root and returns list of prep files """
    config_path = os.path.join(project_root, 'ongtrum_config.yaml')
    if not os.path.exists(config_path):
        return None

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}  # noqa

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

    # Run the test method itself
    if not method:
        results.append(TestSpec(file_name, cls_name, method_name, False, 'MethodNotFound'))
        return results

    params_list = getattr(method, '__params__', [None])
    for params in params_list:
        try:
            if params is None:
                method()
            elif isinstance(params, dict):
                method(**params)
            elif isinstance(params, (list, tuple)):
                method(*params)
            results.append(TestSpec(file_name, cls_name, method_name, True, params=params))
        except Exception as e:
            results.append(TestSpec(
                file_name,
                cls_name,
                method_name,
                False,
                f'{type(e).__name__} - {str(e) or "Undefined"}',
                params
            ))

    return results


def worker_run_files(batch: list, test_filter: Any = None) -> list[TestSpec]:
    results = []

    for file_name, content, test_methods in batch:
        # Apply file filter
        if test_filter and test_filter.file_name and test_filter.file_name != '*' and file_name != test_filter.file_name:
            continue

        # Apply class and method filters
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

        test_namespace = {}
        try:
            exec(compile(content, file_name, 'exec'), test_namespace)
        except Exception as e:
            for cls_name, methods in filtered_test_methods.items():
                for m in methods:
                    results.append(TestSpec(file_name, cls_name, m, False, f'ExecError: {e}'))
            continue

        for cls_name, method_names in filtered_test_methods.items():
            cls = test_namespace.get(cls_name)
            if not cls:
                for m in method_names:
                    results.append(TestSpec(file_name, cls_name, m, False, 'ClassNotFound'))
                continue

            instance = cls()
            for method_name in method_names:
                method = getattr(instance, method_name, None)
                if not method:
                    results.append(TestSpec(file_name, cls_name, method_name, False, 'MethodNotFound'))
                    continue

                params_list = getattr(method, '__params__', [None])
                for params in params_list:
                    try:
                        if params is None:
                            method()
                        elif isinstance(params, dict):
                            method(**params)
                        elif isinstance(params, (list, tuple)):
                            method(*params)
                        results.append(TestSpec(file_name, cls_name, method_name, True, params=params))
                    except Exception as e:
                        results.append(
                            TestSpec(
                                file_name,
                                cls_name,
                                method_name,
                                False,
                                f'{type(e).__name__} - {str(e) or "Undefined"}',
                                params
                            )
                        )

    return results


def run(
        root_dir: str,
        max_workers: Optional[int] = None,
        quiet: bool = False,
        batch_size: int = 64,
        suite: Optional[str] = None,
        test_filter: Optional[str] = None
):
    start_time = time()
    collected_tests = 0

    if not quiet:
        print(f'Project: {root_dir}')
        print(f'Max Workers: {max_workers or 1}')
        print(f'Batch Size: {batch_size}')
        print(f'Suite: {suite}')
        print(f'Filter: {test_filter}')

    # Prepare test filter
    test_spec = TestSpec()
    if test_filter:
        parts = [p.strip() for p in test_filter.split('.')]
        if not 1 <= len(parts) <= 3:
            raise ValueError('Invalid test filter format: use file, file.class, or file.class.method')
        parts += [None] * (3 - len(parts))
        test_spec.file_name, test_spec.cls_name, test_spec.method_name = parts

    all_tasks = []

    # Temporarily add the project root to sys.path so test modules can be imported
    # Automatically remove it on program exit to avoid polluting sys.path
    sys.path.insert(0, root_dir)
    atexit.register(lambda: sys.path.pop(0) if sys.path and sys.path[0] == root_dir else None)

    for file_name, content in scan(root_dir):
        test_classes, test_methods, _imports = parse(content)
        if not test_classes:
            continue
        collected_tests += sum(len(m) for m in test_methods.values())
        all_tasks.append((file_name.removesuffix('.py'), content, test_methods))

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

    # Single Worker
    if not max_workers or max_workers == 1:
        for task in all_tasks:
            results = worker_run_files([task], test_spec)
            for r in results:
                reprs.append(repr_result(r))

    # Multi-Worker
    else:
        print(
            '\033[93m[Warning]\033[0m Multiprocessing should be used for heavy or long-running tests'
            'For simple tests, it may slow down execution due to process startup overhead'
        )

        batches = [all_tasks[i:i + batch_size] for i in range(0, len(all_tasks), batch_size)]
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker_run_files, batch, test_spec) for batch in batches]
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ongtrum — Fast Python Test Runner')
    parser.add_argument('-p', '--project', type=str, required=True, help='Root directory of the test project')
    parser.add_argument('-w', '--workers', type=int, default=None, help='Number of parallel test processes')
    parser.add_argument('-bs', '--batch-size', type=int, default=64, help='Number of test files each worker processes at once (default: 64)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Run in quiet mode (minimal output)')
    parser.add_argument('-s', '--suite', type=str, required=False, help='Test suite to run')
    parser.add_argument('-f', '--filter', type=str, help='Run only a specific test: file, file.class, or file.class.method')

    args = parser.parse_args()

    if not os.path.exists(args.project):
        raise ValueError(f'Project {args.project} does not exist!')

    # Load Config
    config = parse_ongtrum_config(args.project)

    if config:
        pass  # Handle Config

    run(
        args.project,
        max_workers=args.workers,
        quiet=args.quiet,
        batch_size=args.batch_size,
        suite=args.suite,
        test_filter=args.filter
    )
