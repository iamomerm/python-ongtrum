import argparse
import atexit
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from time import time

from ast_parser import parse  # noqa
from fs_scanner import scan  # noqa


def worker_run_files(batch: list, suite: str = None):
    """ Execute multiple files in one worker to reduce process overhead """
    results = []

    for content, test_methods in batch:
        namespace = dict()
        try:
            code_obj = compile(content, '<string>', 'exec')
            exec(code_obj, namespace)
        except Exception as e:
            for cls_name, methods in test_methods.items():
                for m in methods:
                    results.append((cls_name, m, False, f'ExecError: {e}'))
            continue

        for cls_name, method_names in test_methods.items():
            cls = namespace.get(cls_name)
            if not cls:
                for m in method_names:
                    results.append((cls_name, m, False, 'ClassNotFound'))  # noqa
                continue

            instance = cls()
            for method_name in method_names:
                method = getattr(instance, method_name, None)
                if not method:
                    results.append((cls_name, method_name, False, 'MethodNotFound'))  # noqa
                    continue

                # Suite
                if suite:
                    test_suites = getattr(method, '__suites__', [])
                    if suite not in test_suites:
                        continue

                # Parameterization
                params_list = getattr(method, '__params__', [None])
                for params in params_list:
                    try:
                        if params is None:
                            method()
                        else:
                            method(**params)

                        results.append((cls_name, method_name, True, None, params))
                    except Exception as e:
                        results.append((cls_name, method_name, False, f'{type(e)} - {str(e) or "Unspecified"}', params))

    return results


def run(
        root_dir: str,
        max_workers: int = None,
        quiet: bool = False,
        batch_size: int = 64,
        suite: str = None
):
    print(
        '\n'.join([
            f'Project: {root_dir}',
            f'Max Workers: {max_workers or "1"}',
            f'Batch Size: {batch_size}',
            f'Quiet: {quiet}',
            f'Suite: "{suite}"'
        ]) + '\n'
    )

    collected_tests = 0
    executed_tests = 0
    total_failures = 0
    start_time = time()

    sys.path.insert(0, root_dir)
    atexit.register(lambda: sys.path.pop(0) if sys.path and sys.path[0] == root_dir else None)

    all_tasks = []

    for content in scan(root_dir):
        test_classes, test_methods, _imports = parse(content)
        if not test_classes:
            continue
        collected_tests += sum(len(m) for m in test_methods.values())
        all_tasks.append((content, test_methods))

    # Single-Worker
    if max_workers is None or max_workers == 1:
        for task in all_tasks:
            results = worker_run_files([task], suite)
            for cls_name, method_name, passed, error, params in results:
                params_exp = f'[{params}]' if params else ''
                executed_tests += 1
                if passed:
                    if not quiet:

                        print(f'\033[92m[PASS]\033[0m {cls_name}.{method_name}{params_exp}')
                else:
                    total_failures += 1
                    if not quiet:
                        print(f'\033[91m[FAIL]\033[0m {cls_name}.{method_name}{params_exp} → {error}')

    # Multi-Workers
    else:
        print(
            '\033[93m[Warning]\033[0m Multiprocessing should be used for heavy or long-running tests. '
            'For simple tests, it may slow down execution due to process startup overhead.'
        )

        batches = [all_tasks[i:i + batch_size] for i in range(0, len(all_tasks), batch_size)]
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker_run_files, batch, suite) for batch in batches]

            for future in as_completed(futures):
                for cls_name, method_name, passed, error, params in future.result():
                    params_exp = f'[{params}]' if params else ''
                    executed_tests += 1
                    if passed:
                        if not quiet:
                            print(f'\033[92m[PASS]\033[0m {cls_name}.{method_name}{params_exp}')
                    else:
                        total_failures += 1
                        if not quiet:
                            print(f'\033[91m[FAIL]\033[0m {cls_name}.{method_name}{params_exp} → {error}')

    # Summary
    print('\n- - - Summary - - -\n')
    print(f'Collected: {collected_tests}')
    print(f'Executed: {executed_tests} / {collected_tests}')
    print(f'Failed: {total_failures}')
    print(f'Passed: {executed_tests - total_failures}')
    print(f'Total Time: {time() - start_time:.2f} Seconds')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ongtrum — Fast Python Test Runner')
    parser.add_argument('-p', '--project', type=str, required=True, help='Root directory of the test project')
    parser.add_argument('-w', '--workers', type=int, default=None, help='Number of parallel test processes')
    parser.add_argument('-bs', '--batch-size', type=int, default=64, help='Number of test files each worker processes at once (default: 64)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Run in quiet mode (minimal output)')
    parser.add_argument('-s', '--suite', type=str, required=False, help='Test suite to run')
    args = parser.parse_args()

    if not os.path.exists(args.project):
        raise ValueError(f'Project {args.project} does not exist!')

    run(args.project, max_workers=args.workers, quiet=args.quiet, batch_size=args.batch_size, suite=args.suite)
