from __future__ import annotations

import socket
import struct
import sys
import threading
import time
from dataclasses import dataclass, fields
from multiprocessing.shared_memory import SharedMemory
from typing import TYPE_CHECKING

from gunicorn_django_wide_events.hooks import register_hook

if TYPE_CHECKING:
    from gunicorn.arbiter import Arbiter
    from gunicorn.http.message import Request
    from gunicorn.workers.base import Worker


@dataclass
class SaturationStats:
    workers_total: int = 0
    workers_active: int = 0
    backlog: int = 0

class SaturationStatsShared:
    STRUCT_FMT = 3*"H"  # 3*uint16 (workers_total, workers_active, backlog)
    STRUCT_SIZE = struct.calcsize(STRUCT_FMT)

    def __init__(self, shm):
        self.shm: SharedMemory = shm

    @staticmethod
    def create():
        shm = SharedMemory(create=True, size=SaturationStatsShared.STRUCT_SIZE, track=False)
        inst = SaturationStatsShared(shm)
        inst.set(stats=SaturationStats())
        return inst

    @staticmethod
    def from_name(name):
        shm = SharedMemory(name, track=False)
        return SaturationStatsShared(shm)

    @property
    def name(self) -> str:
        return self.shm.name

    def set(self, *, stats: SaturationStats) -> None:
        values = [getattr(stats, field.name) for field in fields(stats)]
        struct.pack_into(self.STRUCT_FMT, self.shm.buf, 0, *values)

    @property
    def value(self) -> SaturationStats:
        unpacked = struct.unpack_from(self.STRUCT_FMT, self.shm.buf, 0)
        return SaturationStats(*unpacked)

    def close(self) -> None:
        self.shm.close()

    def unlink(self) -> None:
        self.shm.unlink()

class WorkerActiveShared:
    STRUCT_FMT = "?"  # boolean
    STRUCT_SIZE = struct.calcsize(STRUCT_FMT)

    def __init__(self, shm):
        self.shm: SharedMemory = shm

    @staticmethod
    def create():
        shm = SharedMemory(create=True, size=WorkerActiveShared.STRUCT_SIZE, track=False)
        inst = WorkerActiveShared(shm)
        inst.set(active=False)
        return inst

    @staticmethod
    def from_name(name):
        shm = SharedMemory(name, track=False)
        return WorkerActiveShared(shm)

    @property
    def name(self) -> str:
        return self.shm.name

    def set(self, *, active: bool) -> None:
        struct.pack_into(self.STRUCT_FMT, self.shm.buf, 0, active)

    @property
    def value(self) -> bool:
        unpacked = struct.unpack_from(self.STRUCT_FMT, self.shm.buf, 0)
        return unpacked[0]

    def close(self) -> None:
        self.shm.close()

    def unlink(self) -> None:
        self.shm.unlink()

def get_backlog(arbiter) -> int:
    """Get the number of connections waiting to be accepted by a server"""
    if sys.platform != "linux":
        return 0
    total = 0
    for listener in arbiter.LISTENERS:
        if not listener.sock:
            continue

        tcp_info_fmt = "B" * 8 + "I" * 5  # tcp_info struct from /usr/include/linux/tcp.h
        tcp_info_size = 28
        tcpi_unacked_index = 12
        tcp_info_struct = listener.sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, tcp_info_size)
        total += struct.unpack(tcp_info_fmt, tcp_info_struct)[tcpi_unacked_index]

    return total

def get_workers_active(arbiter: Arbiter, workers: list[Worker]) -> int:
    workers_active = 0
    for worker in workers:
        if not hasattr(worker, "saturation_stats_active_shm_name"):
            arbiter.log.debug("no activeness shm path available for worker with pid %s", worker.pid)
            continue

        try:
            active = WorkerActiveShared.from_name(worker.saturation_stats_active_shm_name).value
        except FileNotFoundError:
            arbiter.log.debug("no activeness shm file found for worker with pid %s", worker.pid)
            continue
        else:
            workers_active += int(active)
    return workers_active


def monitor_saturation(arbiter: Arbiter):
    """Monitor thread target to share stats with requests

    This thread updates saturation stats combining data from the arbiter and workers.

    * Saturation stats are made available on `requests` via pre-request hooks.
    * Workers activeness is maintained via pre/post-request hooks.
    """
    update_interval_seconds = 1

    while True:
        if arbiter.saturation_stats_should_exit:
            arbiter.log.info("Stopping saturation monitor")
            break

        workers: list[Worker] = arbiter.WORKERS.values()
        workers_total = len(workers)
        workers_active = get_workers_active(arbiter, workers)

        backlog = get_backlog(arbiter)

        arbiter.saturation_stats.set(stats=SaturationStats(workers_total, workers_active, backlog))

        time.sleep(update_interval_seconds)


@register_hook
def when_ready(arbiter: Arbiter):
    arbiter.log.info("Starting saturation monitor")
    arbiter.saturation_stats = SaturationStatsShared.create()
    arbiter.saturation_stats_should_exit = False
    arbiter.saturation_stats_thread = threading.Thread(target=monitor_saturation, args=(arbiter,))
    arbiter.saturation_stats_thread.start()


@register_hook
def pre_fork(arbiter: Arbiter, worker: Worker):
    worker.saturation_stats_shm_name = arbiter.saturation_stats.name
    worker.saturation_stats_active = WorkerActiveShared.create()
    worker.saturation_stats_active_shm_name = worker.saturation_stats_active.name


@register_hook
def pre_request(worker: Worker, request: Request):
    worker.saturation_stats_active.set(active=True)
    request.saturation_stats = SaturationStatsShared.from_name(worker.saturation_stats_shm_name).value


@register_hook
def post_request(worker: Worker, *_):
    worker.saturation_stats_active.set(active=False)


@register_hook
def worker_exit(_, worker: Worker):
    worker.saturation_stats_active.close()
    worker.saturation_stats_active.unlink()

@register_hook
def on_exit(arbiter: Arbiter):
    arbiter.saturation_stats_should_exit = True
    arbiter.saturation_stats_thread.join()
    arbiter.saturation_stats.close()
    arbiter.saturation_stats.unlink()
