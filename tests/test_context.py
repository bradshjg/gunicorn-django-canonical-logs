from gunicorn_django_wide_events.context import Context


def test_context_str():
    context = Context({"foo": "bar", "baz": "qux"})
    assert str(context) == "foo=bar baz=qux"


def test_context_reset():
    context = Context({"foo": "bar", "baz": "qux"})
    assert str(context) == "foo=bar baz=qux"
    context.reset()
    assert str(context) == ""
