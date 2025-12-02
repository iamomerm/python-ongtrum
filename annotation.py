from functools import wraps
from typing import Union, List


def suites(suites: Union[str, List[str]]):  # noqa
    """
    Decorator to associate a test function with one or more test suites
    Accepts a single suite name (string) or a list of suite names
    Stores the suite information on the function for runtime access
    """
    if isinstance(suites, str):
        suites = [suites]  # noqa

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__suites__ = suites
        return wrapper

    return decorator


def parameters(params: list[dict]):
    """
    Decorator to associate test parameters with a test method
    Accepts a single dict or a list of dicts
    Each dict represents one set of parameters
    """
    if isinstance(params, dict):
        params = [params]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__params__ = params
        return wrapper

    return decorator
