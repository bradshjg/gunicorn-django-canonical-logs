from gunicorn_django_wide_events.hooks import Hook, HookRegistry, register_hook


def test_valid_hook_registration():
    hook_registry = HookRegistry()

    @register_hook(registry=hook_registry)
    def when_ready():
        pass

    assert hook_registry[Hook.WHEN_READY] == {when_ready.__wrapped__}


def test_double_registration_is_deduplicated():
    hook_registry = HookRegistry()

    def when_ready():
        pass

    register_hook(registry=hook_registry)(when_ready)
    register_hook(registry=hook_registry)(when_ready)

    assert hook_registry[Hook.WHEN_READY] == {when_ready}
