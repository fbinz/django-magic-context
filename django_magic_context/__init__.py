import inspect
from typing import Any


def get_lazy(d: dict[str, Any], key: str):
    value = d[key]
    if callable(value):
        args = inspect.getargs(value.__code__)

        value = value(**{name: get_lazy(d, name) for name in args.args})
        d[key] = value
        return value
    else:
        return value


def resolve(**kwargs):
    return {k: get_lazy(kwargs, k) if callable(v) else v for k, v in kwargs.items()}
