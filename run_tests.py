import importlib.util
import inspect
import sys


def run_tests_module(path: str) -> int:
    spec = importlib.util.spec_from_file_location('tests_module', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    tests = [getattr(mod, name) for name in dir(mod) if name.startswith('test_') and inspect.isfunction(getattr(mod, name))]
    failed = 0
    for t in tests:
        try:
            t()
            print(f'PASS: {t.__name__}')
        except AssertionError as e:
            failed += 1
            print(f'FAIL: {t.__name__}: {e}')
        except Exception as e:
            failed += 1
            print(f'ERROR: {t.__name__}: {e}')
    return failed


if __name__ == '__main__':
    path = 'tests_test_checker.py'
    print('Running tests in', path)
    failed = run_tests_module(path)
    if failed:
        print(f"{failed} tests failed")
        sys.exit(1)
    print('All tests passed')
    sys.exit(0)
