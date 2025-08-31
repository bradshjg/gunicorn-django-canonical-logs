import socket
import struct
import sys
import threading
import time
from multiprocessing.shared_memory import SharedMemory

from gunicorn.arbiter import Arbiter
from gunicorn.http.message import Request
from gunicorn.workers.base import Worker

from gunicorn_django_wide_events.hooks import register_hook

stats_struct = struct.Struct(3*"H")


class SaturationMonitor(threading.Thread):
    def __init__(self, arbiter):
        super().__init__()
        self.arbiter: Arbiter = arbiter
        self.daemon = True  # don't wait for this thread to complete during arbiter shutdown
        self.METRIC_INTERVAL_SECONDS = 1

    def run(self):
        while True:
            workers = len(self.arbiter.WORKERS)
            backlog = self.get_backlog()
            self.arbiter._stats.buf[0:stats_struct.size] = stats_struct.pack(workers, backlog, 0)
            time.sleep(self.METRIC_INTERVAL_SECONDS)

    def get_backlog(self) -> int:
        """Get the number of connections waiting to be accepted by a server"""
        if sys.platform != "linux":
            return None
        total = 0
        for listener in self.arbiter.LISTENERS:
            if not listener.sock:
                continue

            # tcp_info struct from include/uapi/linux/tcp.h
            tcp_info_fmt = "B" * 8 + "I" * 24
            tcp_info_bytes = 104
            tcp_info_struct = listener.sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, tcp_info_bytes)
            # 12 is tcpi_unacked
            total += struct.unpack(tcp_info_fmt, tcp_info_struct)[12]

        return total

@register_hook
def on_starting(arbiter: Arbiter):
    arbiter._stats = SharedMemory(create=True, size=stats_struct.size)

@register_hook
def when_ready(arbiter: Arbiter):
    arbiter.log.info("Starting SaturationMonitor")
    sm = SaturationMonitor(arbiter)
    sm.start()


@register_hook
def pre_fork(arbiter: Arbiter, worker: Worker):
    worker._arbiter_stats_name = arbiter._stats.name


@register_hook
def pre_request(worker: Worker, request: Request):
    request._arbiter_stats_name = worker._arbiter_stats_name


@register_hook
def post_request(worker: Worker, *_):
    pass

@register_hook
def on_exit(arbiter: Arbiter):
    arbiter._stats.unlink()
