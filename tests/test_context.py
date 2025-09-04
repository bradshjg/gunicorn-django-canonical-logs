from gunicorn_django_wide_events.event_context import EventContext


def test_context_log_str_simple():
    context = EventContext({"foo": "bar", "baz": "qux"})
    assert str(context) == "foo=bar baz=qux"


def test_context_log_str_prefixed():
    context = EventContext({"prefix": {"foo": "bar", "baz": "qux"}})
    assert str(context) == "prefix_foo=bar prefix_baz=qux"


def test_context_log_str_mixed():
    context = EventContext({"foo": "bar", "prefix": {"foo": "bar", "baz": "qux"}})
    assert str(context) == "foo=bar prefix_foo=bar prefix_baz=qux"


def test_context_log_str_ignore_none_value():
    context = EventContext({"foo": "bar", "baz": None})
    assert str(context) == "foo=bar"


def test_context_log_str_quoting():
    context = EventContext({"with spaces": "baz", "dec": "1.234", "int": 5})
    assert str(context) == '"with spaces"=baz dec="1.234" int=5'


def test_context_dict_value():
    context = EventContext({"prefix": {"foo": "bar", "baz": "qux"}})
    assert str(context) == "prefix_foo=bar prefix_baz=qux"


def test_context_reset():
    context = EventContext({"foo": "bar", "baz": "qux"})
    assert str(context) == "foo=bar baz=qux"
    context.reset()
    assert str(context) == ""

# TODO when we move this into it's own formatter, use https://github.com/josheppinette/python-logfmter/blob/main/tests/test_formatter.py
# for inspirationn for tests
