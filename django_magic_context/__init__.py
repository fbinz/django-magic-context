import inspect
from typing import Any


def get(d: dict[str, Any], key: str, lazy=True):
    value = d[key]

    if callable(value):
        args = inspect.getargs(value.__code__)

        if lazy:

            def evaluate():
                val = d[key]
                if callable(val):
                    evaluated = val(
                        **{name: get(d, name, lazy=False) for name in args.args}
                    )
                    d[key] = evaluated
                    return evaluated
                else:
                    return val

            return evaluate

        else:
            evaluated = value(**{name: get(d, name, lazy=False) for name in args.args})
            d[key] = evaluated
            return evaluated
    else:
        return value


def resolve(**kwargs):
    return {k: get(kwargs, k) if callable(v) else v for k, v in kwargs.items()}
