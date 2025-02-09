from .scope_dict import ScopeDict
from copy import deepcopy
from dataclasses import dataclass, field
import inspect
from typing import Any, Callable, Iterable, overload


@dataclass(eq=True)
class NotEvaluated:
    def __repr__(self):
        return "NotEvaluated"


@dataclass(eq=True)
class NoDefault:
    def __repr__(self):
        return "NoDefault"


NOT_EVALUATED = NotEvaluated()

NO_DEFAULT = NoDefault()

DOES_NOT_EXIST = object()


@dataclass
class Context:
    registry: ScopeDict = field(default_factory=ScopeDict)
    fn_cache: ScopeDict = field(default_factory=ScopeDict)
    extra: dict = field(default_factory=dict)

    @overload
    def register(self, key, *, context, **extra) -> None: ...

    @overload
    def register(self, key) -> Callable[..., Any]: ...

    def register(self, key, *, context=None, **extra):
        if context is not None:
            if not isinstance(context, Context):
                raise ValueError(
                    "Can only register other contexts using the non-decorator form of Context.register"
                )

            context = deepcopy(context)
            context.extra = extra
            self.registry[key] = context
            return

        if extra:
            raise ValueError(
                "Can only pass extra when using the non-decorator form of Context.register"
            )

        def decorator(fn):
            self.fn_cache[fn] = NOT_EVALUATED
            self.registry[key] = fn
            return fn

        return decorator

    def resolve(
        self,
        *,
        parent_registry: ScopeDict | None = None,
        parent_fn_cache: ScopeDict | None = None,
        **extra,
    ):
        context = deepcopy(self)
        registry = ScopeDict(extra or None, context.registry, parent_registry)
        fn_cache = ScopeDict(context.fn_cache, parent_fn_cache)
        return {key: lazy_lookup(registry, fn_cache, key) for key in registry.keys()}


def lazy_lookup(
    registry: ScopeDict,
    fn_cache: ScopeDict,
    key: str,
):
    def do_lookup():
        value = registry[key]

        # Resolve child contexts directly
        if isinstance(value, Context):
            return value.resolve(
                parent_fn_cache=fn_cache,
                parent_registry=registry,
                **value.extra,
            )

        if not callable(value):
            return value

        fn = value

        evaluated = fn_cache.get(fn, default=DOES_NOT_EXIST)
        if evaluated is DOES_NOT_EXIST:
            return fn

        if evaluated == NOT_EVALUATED:
            evaluated = eager_lookup(registry, fn_cache, key)

        return evaluated

    return do_lookup


def eager_lookup(
    registry: ScopeDict,
    fn_cache: ScopeDict,
    key: str,
    default=NO_DEFAULT,
):
    try:
        fn = registry[key]

        if not callable(fn):
            return fn

        value = fn_cache.get(fn, default=DOES_NOT_EXIST)
        if value is DOES_NOT_EXIST:
            return fn

        value = fn_cache[fn]

        # handle already evaluated values
        if value != NOT_EVALUATED:
            return value

        parameters = inspect.signature(fn).parameters.values()
        evaluated = fn(**evaluate_parameters(registry, fn_cache, parameters))

        fn_cache[fn] = evaluated
        registry[key] = evaluated

        return evaluated

    except KeyError:
        if default is NO_DEFAULT:
            raise
        return default


def evaluate_parameters(
    registry: ScopeDict,
    fn_cache: ScopeDict,
    parameters: Iterable[inspect.Parameter],
):
    return {
        parameter.name: eager_lookup(
            registry,
            fn_cache,
            key=parameter.name,
            default=NO_DEFAULT
            if parameter.default is inspect.Parameter.empty
            else parameter.default,
        )
        for parameter in parameters
    }
