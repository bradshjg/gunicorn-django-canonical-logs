"""Provides gunicorn server hook definitions that run all registered callbacks

Usage: Add `from gunicorn_django_canonical_logs.registered_hook import *` to your gunicorn config file.

N.B.: You might _want_ to metaprogram these...but gunciorn does arity-checking, so no *args, **kwargs shenanigans!
"""

from gunicorn_django_canonical_logs.gunicorn_hooks.registry import Hook, hook_registry


def on_starting(server):
    for callback in hook_registry[Hook.ON_STARTING.value]:
        callback(server)


def on_reload(server):
    (callback(server) for callback in hook_registry[Hook.ON_RELOAD.value])


def when_ready(server):
    for callback in hook_registry[Hook.WHEN_READY.value]:
        callback(server)


def pre_fork(server, worker):
    for callback in hook_registry[Hook.PRE_FORK.value]:
        callback(server, worker)


def post_fork(server, worker):
    for callback in hook_registry[Hook.POST_FORK.value]:
        callback(server, worker)


def post_worker_init(worker):
    for callback in hook_registry[Hook.POST_WORKER_INIT.value]:
        callback(worker)


def worker_int(worker):
    for callback in hook_registry[Hook.WORKER_INT.value]:
        callback(worker)


def worker_abort(worker):
    for callback in hook_registry[Hook.WOKER_ABORT.value]:
        callback(worker)


def pre_exec(server):
    for callback in hook_registry[Hook.PRE_EXEC.value]:
        callback(server)


def pre_request(worker, req):
    for callback in hook_registry[Hook.PRE_REQUEST.value]:
        callback(worker, req)


def post_request(worker, req, environ, resp):
    for callback in hook_registry[Hook.POST_REQUEST.value]:
        callback(worker, req, environ, resp)


def child_exit(server, worker):
    for callback in hook_registry[Hook.CHILD_EXIT.value]:
        callback(server, worker)


def worker_exit(server, worker):
    for callback in hook_registry[Hook.WORKER_EXIT.value]:
        callback(server, worker)


def nworkers_changed(server, new_value, old_value):
    for callback in hook_registry[Hook.NWORKERS_CHANGED.value]:
        callback(server, new_value, old_value)


def on_exit(server):
    for callback in hook_registry[Hook.ON_EXIT.value]:
        callback(server)


def ssl_context(config, default_ssl_context_factory):
    for callback in hook_registry[Hook.SSL_CONTEXT.value]:
        callback(config, default_ssl_context_factory)
