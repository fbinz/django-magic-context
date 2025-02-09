from django_magic_context import Context


def test__simple():
    call_count = 0

    context = Context()

    @context.register("a")
    def get_a():
        nonlocal call_count
        call_count += 1
        return 1

    c = context.resolve()

    assert c["a"]() == 1
    assert c["a"]() == 1

    assert call_count == 1


def test__injection():
    call_count_a = 0
    call_count_b = 0

    context = Context()

    @context.register("a")
    def get_a():
        nonlocal call_count_a
        call_count_a += 1
        return 1

    @context.register("b")
    def get_b(a):
        nonlocal call_count_b
        call_count_b += 1
        return a + 1

    c = context.resolve()

    assert c["a"]() == 1
    assert c["a"]() == 1
    assert c["b"]() == 2
    assert c["b"]() == 2

    assert call_count_a == 1
    assert call_count_b == 1


def test_extra():
    call_count_a = 0

    context = Context()

    @context.register("a")
    def get_a(x):
        nonlocal call_count_a
        call_count_a += 1
        return x + 1

    c = context.resolve(x=1)

    assert c["x"]() == 1
    assert c["a"]() == 2
    assert c["a"]() == 2

    assert call_count_a == 1


def test_nested():
    parent_context = Context()
    child_context = Context()

    @parent_context.register("a")
    def get_a():
        return 1

    @child_context.register("b")
    def get_b(a):
        return a + 1

    parent_context.register("child", context=child_context)
    c = parent_context.resolve()

    assert c["a"]() == 1
    assert c["child"]()["b"]() == 2


def test_nested_extra():
    parent_context = Context()
    child_context = Context()

    @parent_context.register("a")
    def get_a():
        return 1

    @child_context.register("b")
    def get_b(a):
        return a + 1

    parent_context.register("child", context=child_context, a=2)
    ctx = parent_context.resolve()

    assert ctx["a"]() == 1
    assert ctx["child"]()["a"]() == 2
    assert ctx["child"]()["b"]() == 3


def test_nested_precedence():
    parent_context = Context()
    child_context = Context()

    @parent_context.register("a")
    def get_a():
        return 1

    @child_context.register("a")
    def get_a_child():
        return 5

    @child_context.register("b")
    def get_b(a):
        return a + 1

    parent_context.register("child", context=child_context)
    c = parent_context.resolve()

    assert c["a"]() == 1
    assert c["child"]()["b"]() == 6


def test_nested_mixed_injection():
    parent_context = Context()
    child_context = Context()

    @parent_context.register("parent_a")
    def get_parent_a():
        return "parent_a"

    @parent_context.register("parent_b")
    def get_parent_b():
        return "parent_b"

    @child_context.register("child_a")
    def get_child_a(parent_a, child_b):
        return [parent_a, child_b]

    @child_context.register("child_b")
    def get_child_b(parent_b):
        return "child_b"

    parent_context.register("child", context=child_context)
    c = parent_context.resolve()

    assert c["parent_a"]() == "parent_a"
    assert c["child"]()["child_a"]() == ["parent_a", "child_b"]


def test_component():
    # A component, that expects a key from the parent context
    component_context = Context()

    @component_context.register("data")
    def get_data(items, a):
        return len(items) + a

    context = Context()

    @context.register("items_new")
    def get_items_new():
        return [1, 2, 3]

    @context.register("items_old")
    def get_items_old():
        return []

    call_count_a = 0

    @context.register("a")
    def get_a():
        nonlocal call_count_a
        call_count_a += 1
        return 1

    context.register("component_new", context=component_context, items=get_items_new)
    context.register("component_old", context=component_context, items=get_items_old)

    c = context.resolve()

    assert c["component_new"]()["data"]() == 3 + 1
    assert c["component_old"]()["data"]() == 0 + 1
    assert call_count_a == 1
