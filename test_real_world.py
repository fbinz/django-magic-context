from dataclasses import dataclass

import django_magic_context as magic


context = magic.Context()


@dataclass
class HttpRequest:
    method: str
    path: str
    GET: dict[str, str]


@dataclass
class Employee:
    id: str
    name: str


@context.register("search")
def get_search(request) -> str | None:
    return request.GET.get("search")


@context.register("page")
def get_page(request) -> int | None:
    page = request.GET.get("page")
    if page is not None:
        return int(page)

    return None


@context.register("employee_list")
def get_employee_list(search: str | None, page: int | None) -> list[Employee]:
    employees = [
        Employee("1", "Mary"),
        Employee("1", "Sue"),
        Employee("1", "Martin"),
    ]

    if search:
        employees = [e for e in employees if e.name.startswith(search)]

    if page:
        employees = employees[page : page + 1]

    return employees


def make_context(request):
    return context.resolve(request=request)


def test_real_world_no_search():
    request = HttpRequest(method="GET", path="employees/", GET={})

    context = make_context(request)
    assert len(context["employee_list"]()) == 3


def test_real_world_query_params_1():
    request = HttpRequest(method="GET", path="employees/", GET={"search": "M"})

    context = make_context(request)
    assert len(context["employee_list"]()) == 2


def test_real_world_query_params_2():
    request = HttpRequest(
        method="GET", path="employees/", GET={"search": "M", "page": "1"}
    )

    context = make_context(request)
    assert len(context["employee_list"]()) == 1
