from django_magic_context import resolve


def test_resolve_simple():
    context = resolve(a=1, b=2)

    assert context["a"] == 1
    assert context["b"] == 2


def test_resolve_function_is_lazy():
    call_count = 0

    def get_y():
        nonlocal call_count
        call_count += 1

        return 3

    context = resolve(y=get_y)
    assert call_count == 0

    assert context["y"]() == 3
    assert context["y"]() == 3
    assert call_count == 1


def test_resolve_injects_dependencies():
    x_call_count = 0

    def get_x(request):
        nonlocal x_call_count
        x_call_count += 1

        return request

    y_call_count = 0

    def get_y(x):
        nonlocal y_call_count
        y_call_count += 1

        return x + x

    context = resolve(
        request=1,
        x=get_x,
        y=get_y,
    )

    assert context["x"]() == 1
    assert context["y"]() == 2

    assert x_call_count == 1
    assert y_call_count == 1


def test_unused_function_is_not_called():
    def get_not_used():
        raise NotImplementedError

    context = resolve(not_used=get_not_used)
