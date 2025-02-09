from django_magic_context.scope_dict import ScopeDict


def test_scope_dict_00():
    d = ScopeDict()
    d["a"] = 1
    assert d["a"] == 1


def test_scope_dict_01():
    parent_scope = ScopeDict()
    parent_scope["a"] = 1
    parent_scope["b"] = 1

    child_scope = parent_scope.new_child()
    child_scope["a"] = 2

    assert child_scope["a"] == 2
    assert child_scope["b"] == 1


def test_scope_dict_02():
    parent_scope = ScopeDict()
    parent_scope["a"] = 1

    child_scope = parent_scope.new_child()
    # this updates the parent_scope, too
    child_scope["a"] = 2

    assert child_scope["a"] == 2
    assert parent_scope["a"] == 2


def test_scope_dict_03():
    parent_scope = ScopeDict()
    parent_scope["a"] = 1

    child_scope = parent_scope.new_child(a=1)
    # this only updates the child_scope, since the key "a" exists there
    child_scope["a"] = 2

    assert parent_scope["a"] == 1
    assert child_scope["a"] == 2


def test_scope_dict_04():
    parent_scope = ScopeDict()
    parent_scope["a"] = 1

    child_scope = parent_scope.new_child(a=2)
    # delete from child_scope, but not from parent
    del child_scope["a"]

    assert parent_scope["a"] == 1
    assert child_scope["a"] == 1
