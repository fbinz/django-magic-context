import _collections_abc
from collections import defaultdict
from reprlib import recursive_repr as _recursive_repr


class ScopeDict(_collections_abc.MutableMapping):
    """A ScopeDict groups multiple dicts (or other mappings) together
    to create a single, updateable view.

    The underlying mappings are stored in a list.  That list is public and can
    be accessed or updated using the *maps* attribute.  There is no other
    state.

    Lookups search the underlying mappings successively until a key is found.
    Writes, updates and deletions likewise will search the underlying mapping successively
    and update the topmost key when found.
    If no key is found, writes will update on the first mapping.
    """

    def __init__(self, *maps):
        """Initialize a ChainMap by setting *maps* to the given mappings.
        If no mappings are provided, a single empty dictionary is used.

        """
        # always at least one map
        self.maps = [m for m in maps if m is not None] or [{}]

    def __missing__(self, key):
        raise KeyError(key)

    def __getitem__(self, key):
        for mapping in self.maps:
            try:
                return mapping[key]  # can't use 'key in mapping' with defaultdict
            except KeyError:
                pass
        return self.__missing__(key)  # support subclasses that define __missing__

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __len__(self):
        return len(set().union(*self.maps))  # reuses stored hash values if possible

    def __iter__(self):
        d = {}
        for mapping in map(dict.fromkeys, reversed(self.maps)):
            d |= mapping  # reuses stored hash values if possible
        return iter(d)

    def __contains__(self, key):
        return any(key in m for m in self.maps)

    def __bool__(self):
        return any(self.maps)

    @_recursive_repr()
    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(repr, self.maps))})"

    @classmethod
    def fromkeys(cls, iterable, *args):
        "Create a ChainMap with a single dict created from the iterable."
        return cls(dict.fromkeys(iterable, *args))

    def copy(self):
        "New ChainMap or subclass with a new copy of maps[0] and refs to maps[1:]"
        return self.__class__(self.maps[0].copy(), *self.maps[1:])

    __copy__ = copy

    def new_child(self, m=None, **kwargs):  # like Django's Context.push()
        """New ScopeDict with a new map followed by all previous maps.
        If no map is provided, an empty dict is used.
        Keyword arguments update the map or new empty dict.
        """
        if m is None:
            m = kwargs
        elif kwargs:
            m.update(kwargs)

        if isinstance(m, defaultdict):
            raise ValueError("defaultdicts cannot be used with ScopeMap")

        return self.__class__(m, *self.maps)

    @property
    def parents(self):  # like Django's Context.pop()
        "New ChainMap from maps[1:]."
        return self.__class__(*self.maps[1:])

    def __setitem__(self, key, value):
        for mapping in self.maps:
            if key in mapping:
                mapping[key] = value
                break
        else:
            self.maps[0][key] = value

    def __delitem__(self, key):
        for mapping in self.maps:
            try:
                del mapping[key]
                break
            except KeyError:
                pass
        else:
            raise KeyError(f"Key not found any mapping: {key!r}")

    def popitem(self):
        "Remove and return an item pair from maps[0]. Raise KeyError is maps[0] is empty."
        try:
            return self.maps[0].popitem()
        except KeyError:
            raise KeyError("No keys found in the first mapping.")

    def pop(self, key, *args):
        "Remove *key* from maps[0] and return its value. Raise KeyError if *key* not in maps[0]."
        try:
            return self.maps[0].pop(key, *args)
        except KeyError:
            raise KeyError(f"Key not found in the first mapping: {key!r}")

    def clear(self):
        "Clear maps[0], leaving maps[1:] intact."
        self.maps[0].clear()

    def __ior__(self, other):
        self.maps[0].update(other)
        return self

    def __or__(self, other):
        if not isinstance(other, _collections_abc.Mapping):
            return NotImplemented
        m = self.copy()
        m.maps[0].update(other)
        return m

    def __ror__(self, other):
        if not isinstance(other, _collections_abc.Mapping):
            return NotImplemented
        m = dict(other)
        for child in reversed(self.maps):
            m.update(child)
        return self.__class__(m)
