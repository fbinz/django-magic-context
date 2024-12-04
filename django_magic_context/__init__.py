import inspect
from typing import Any

NOT_EVALUATED = object()


def get(d: dict[str, Any], key: str, lazy=True):
    value = d[key]

    if callable(value):
        args = inspect.getargs(value.__code__)

        if lazy:
            evaluated = NOT_EVALUATED

            def evaluate():
                nonlocal evaluated

                if evaluated is NOT_EVALUATED:
                    evaluated = value(
                        **{name: get(d, name, lazy=False) for name in args.args}
                    )
                    d[key] = evaluated
                return evaluated

            return evaluate

        else:
            evaluated = value(**{name: get(d, name, lazy=False) for name in args.args})
            d[key] = evaluated
            return evaluated
    else:
        return value


def resolve(**kwargs):
    return {k: get(kwargs, k) if callable(v) else v for k, v in kwargs.items()}
