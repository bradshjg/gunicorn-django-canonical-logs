import ctypes
import socket
import struct
import sys
import threading
import time
from multiprocessing import Value
from typing import ClassVar

from gunicorn.arbiter import Arbiter
from gunicorn.workers.base import Worker

from gunicorn_django_wide_events.hooks import register_hook


class STATS(ctypes.Structure):
    _fields_: ClassVar = [
        ("num_workers", ctypes.c_uint16),
        ("num_active", ctypes.c_uint16),
        ("backlog", ctypes.c_uint16),
    ]


class SaturationMonitor(threading.Thread):
    def __init__(self, arbiter):
        super().__init__()
        self.arbiter: Arbiter = arbiter
        self.daemon = True  # don't wait for this thread to complete during arbiter shutdown
        self.METRIC_INTERVAL_SECONDS = 1

    def run(self):
        self.arbiter._stats = Value(STATS)  # noqa: SLF001
        while True:
            workers = len(self.arbiter.WORKERS)
            active = sum(1 for worker in self.arbiter.WORKERS.values() if worker.active.value)
            backlog = self.get_backlog()
            self.arbiter._stats.value = STATS(workers, active, backlog)  # noqa: SLF001
            time.sleep(self.METRIC_INTERVAL_SECONDS)

    def get_backlog(self):
        """Get the number of connections waiting to be accepted by a server"""
        if sys.platform != "linux":
            return None
        total = 0
        for listener in self.arbiter.LISTENERS:
            if not listener.sock:
                continue

            # tcp_info struct from include/uapi/linux/tcp.h
            tcp_info_fmt = "B" * 7 + "I" * 24
            tcp_info_bytes = 103
            tcp_info_struct = listener.sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, tcp_info_bytes)
            # 12 is tcpi_unacked
            total += struct.unpack(tcp_info_fmt, tcp_info_struct)[12]

        return total


def when_ready(arbiter: Arbiter):
    arbiter.log.info("Starting SaturationMonitor")
    sm = SaturationMonitor(arbiter)
    sm.start()
    arbiter.log.debug("busy workers = 0", extra={"metric": "gunicorn.busy_workers", "value": "0", "mtype": "gauge"})
    arbiter.log.debug(
        "total workers = 0",
        extra={"metric": "gunicorn.total_workers", "value": str(arbiter.num_workers), "mtype": "gauge"},
    )


@register_hook
def pre_fork(_, worker: Worker):
    worker._active = Value(ctypes.c_bool, False)  # noqa: SLF001


@register_hook
def pre_request(worker: Worker, _):
    worker._active.value = True  # noqa: SLF001


@register_hook
def post_request(worker: Worker, *_):
    worker._active.value = False  # noqa: SLF001
