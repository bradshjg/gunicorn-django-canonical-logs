from collections import defaultdict
from collections.abc import Callable
from enum import Enum
from functools import wraps


class InvalidHookError(Exception):
    def __init__(self, hook_name):
        super().__init__(f"{hook_name} is not a valid hook")


class Hook(Enum):
    ON_STARTING = "on_starting"
    ON_RELOAD = "on_reload"
    WHEN_READY = "when_ready"
    PRE_FORK = "pre_fork"
    POST_FORK = "post_fork"
    POST_WORKER_INIT = "post_worker_init"
    WORKER_INT = "worker_int"
    WOKER_ABORT = "worker_abort"
    PRE_EXEC = "pre_exec"
    PRE_REQUEST = "pre_request"
    POST_REQUEST = "post_request"
    CHILD_EXIT = "child_exit"
    WORKER_EXIT = "worker_exit"
    NWORKERS_CHANGED = "nworkers_changed"
    ON_EXIT = "on_exit"
    SSL_CONTEXT = "ssl_context"

    @classmethod
    def values(cls) -> set[str]:
        return {member.value for member in cls}


class HookRegistry:
    def __init__(self):
        self._registered_hooks: dict[Hook, Callable] = defaultdict(set)

    def __getitem__(self, key: Hook):
        return self._registered_hooks[key]

    def register(self, *, hook: Hook, callback: Callable) -> None:
        self._registered_hooks[hook].add(callback)

    def reset(self):
        self._registered_hooks.clear()


hook_registry = HookRegistry()


def register_hook(func=None, *, registry=hook_registry):
    def decorator(f):
        hook_name = f.__name__
        if hook_name not in Hook.values():
            raise InvalidHookError(hook_name)
        registry.register(hook=hook_name, callback=f)

        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper

    if func:
        return decorator(func)
    return decorator
