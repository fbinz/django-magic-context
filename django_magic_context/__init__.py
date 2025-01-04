import inspect
from typing import Any, Callable

NOT_EVALUATED = object()
NO_DEFAULT = object()


def evaluate(
    context: dict[str, Any],
    key: str,
    value: Callable,
    parameters: list[inspect.Parameter],
):
    evaluated = value(
        **{
            parameter.name: get(
                context,
                parameter.name,
                lazy=False,
                default=NO_DEFAULT
                if parameter.default is inspect.Parameter.empty
                else parameter.default,
            )
            for parameter in parameters
        }
    )
    context[key] = evaluated
    return evaluated


def get(context: dict[str, Any], key: str, lazy=True, default=NO_DEFAULT):
    try:
        value = context[key]
    except KeyError:
        if default is NO_DEFAULT:
            raise
        value = default

    # handle plain values
    if not callable(value):
        return value

    parameters = inspect.signature(value).parameters.values()

    # handle non-lazy calls
    if not lazy:
        return evaluate(context, key, value, parameters)

    # handle lazy calls
    evaluated = NOT_EVALUATED

    def lazy_evaluate():
        nonlocal evaluated
        if evaluated is NOT_EVALUATED:
            evaluated = evaluate(context, key, value, parameters)
        return evaluated

    return lazy_evaluate


def resolve(**kwargs):
    return {k: get(kwargs, k) if callable(v) else v for k, v in kwargs.items()}


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
