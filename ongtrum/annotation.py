from functools import wraps
from typing import Callable, Any

from ongtrum.session import Session


def suites(suites: str or list[str]):  # noqa
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


def parameters(params: dict or list[dict]):
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


def prep(*, scope: str = "method"):
    allowed_scopes = {'session', 'class', 'method'}
    if scope not in allowed_scopes:
        raise ValueError(f'Invalid Scope: {scope!r}, Allowed Scopes: {allowed_scopes}')

    def decorator(fn: Callable[..., Any]):
        prep_name = fn.__name__
        Session().preps.setdefault(scope, {})
        Session().preps[scope][prep_name] = fn
        return fn

    return decorator


def preps(prep_names: str or list[str]):
    """ Mark a test class or method to use specific preps """

    if isinstance(prep_names, str):
        prep_names = [prep_names]

    def decorator(obj):
        if not hasattr(obj, '__preps__'):
            obj.__preps__ = []
        obj.__preps__.extend(prep_names)
        return obj

    return decorator
