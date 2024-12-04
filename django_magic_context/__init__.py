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

    # handle non-lazy calls
    args = inspect.getargs(value.__code__).args
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
