# Magic contexts

TLDR: Build contexts using dependency injection.

- [Motivation](#motivation)
- [Usage](#usage)
- [How It Works](#how-it-works)

### Motivation

The context is a core part of the Djangos rendering process and can often grow quite large.
As your views become more complex, so does your context.
Soon, you might split up creating the context into separate functions:

```python
def view(request):
    context = {}
    context.update(get_list_context(request))
    context.update(get_header_context(request))
    context.update(get_footer_context(request))
    ...
```

Now, things get more complex, you find that you need some value in both - `get_list_context` and `get_header_context`.
Since this value is expensive to compute (i.e. it might involve a DB query), you don't want to compute it twice.
So you extract the value and pass it to both functions.

```python
def view(request):
    context = {}
    expensive = get_expensive_value(request)
    context.update(get_list_context(request, expensive))
    context.update(get_header_context(request, expensive))
    context.update(get_footer_context(request))
    ...
```

Now a new shiny technology like HTMX comes along and you now want to render only a part of your view (i.e. the footer) into response to an HTMX request.
This part only needs part of the context.
In particular, it *doesn't* need the expensive value to be computed.
So off you go:


```python
def view(request):
    context = {}

    if not request.htmx:
        expensive = get_expensive_value(request)
        context.update(get_list_context(request, expensive))
        context.update(get_header_context(request, expensive))

    context.update(get_footer_context(request))
    ...
```

As you can imagine, this only get's more complex over time.

### Solution

This "library" (actually it's little more than a code snippet) implements a pattern called dependency injection inspired pytest's fixtures.

Let's see how the above example would look instead:


```python
import django_magic_context as magic

def view(request):
    context = magic.resolve(
        request=request,
        expensive=get_expensive_value,
        list_context=get_list_context,
        header_context=get_header_context,
    )
    ...
```

Note, that the implementation of the functions didn't really change. 
It only takes care of the wiring of the correct arguments (based on name) to the respective functions.
On top of that, it ensures that functions are evaluated lazily and only once, meaning that you can safely pass the entire context even if you only require a small part to render a partial for example


### Usage

The API only exposes a single function named `resolve`.
At the moment, I like importing it like so
```python
import django_magic_context as magic

def get_value_2(value_1):
    return value_1 + 1

context = magic.resolve(
    value_1=123,
    value_2=get_x,
)
```

The `resolve` function takes any number of keyword arguments, which will then be available in the template.
Non-callable values will just be passed as-is.
Callable values will take part in the dependency resolution and will be wrapped such that they are only every evaluated once.



### How it works

This package is primarily useful in the context (pun not intended) of the Django Template Language (DTL).
The DTL always expects plain dictionaries as context objects, which means that we cannot resort to more traditional ways of implementing laziness (say in a decorator for a method).
Fortunately, if the DTL encounters a callable where a non-callable value is expected, it will first call
the callable with no arguments and just use the result.

So, to implement laziness, we use the fact that we are dealing with plain dictionaries:
On the first use of a callable variable in a template, the callable is evaluated.
The evaluated value then overwrites the callable value in the dictionary, so that on further uses, the 
plain, evaluated value can be returned directly.
