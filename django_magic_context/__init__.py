import inspect
from typing import Any, Callable

NOT_EVALUATED = object()


def evaluate(context: dict[str, Any], key: str, value: Callable, args: list[str]):
    evaluated = value(**{name: get(context, name, lazy=False) for name in args})
    context[key] = evaluated
    return evaluated


def get(context: dict[str, Any], key: str, lazy=True):
    value = context[key]

    # handle plain values
    if not callable(value):
        return value

    args = inspect.getargs(value.__code__).args

    # handle non-lazy calls
    if not lazy:
        return evaluate(context, key, value, args)

    # handle lazy calls
    evaluated = NOT_EVALUATED

    def lazy_evaluate():
        nonlocal evaluated
        if evaluated is NOT_EVALUATED:
            evaluated = evaluate(context, key, value, args)
        return evaluated

    return lazy_evaluate


def resolve(**kwargs):
    return {k: get(kwargs, k) if callable(v) else v for k, v in kwargs.items()}


NO_DEFAULT = object()


def cget(context, *keys, default=NO_DEFAULT):
    """Helper function to get one or multiple keys from a context.

    If one key is requested, one a single value is returned.
    If multiple keys are requested, a list of values is returned.

    If no default is given and the key does not exist, a KeyError is raised.

    If the requested value is callable, it will be called.
    """
    result = []
    for key in keys:
        if default is NO_DEFAULT:
            value = context[key]
        else:
            value = context.get(key, default)
        if callable(value):
            result.append(value())
        else:
            result.append(value)

    if len(result) == 1:
        return result[0]

    return result
