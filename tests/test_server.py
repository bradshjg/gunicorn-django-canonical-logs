from __future__ import annotations

import subprocess
from typing import IO, Generator

import pytest
import requests


@pytest.fixture(scope="session")
def server() -> Generator[IO[str], None, None]:
    s_proc = subprocess.Popen(
        ["gunicorn", "-c", "./tests/server/gunicorn_config.py", "tests.server.app"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,  # line buffered
        text=True,
    )
    for line in s_proc.stderr.readline():
        if "Booting worker" in line:
            break
    try:
        yield s_proc.stdout, s_proc.stderr
    finally:
        s_proc.terminate()
        s_proc.wait()


def test_hello(server) -> None:
    stdout, _ = server
    requests.get("http://localhost:8080/hello/")
    log = stdout.readline()
    assert 'req_path="/hello/"' in log


def test_howdy(server) -> None:
    stdout, _ = server
    requests.get("http://localhost:8080/howdy/")
    log = stdout.readline()
    assert 'req_path="/howdy/"' in log


def test_worker_count(server) -> None:
    stdout, _ = server
    import time

    time.sleep(2)  # HACK: find a way to ensure the saturation monitor is emitting data
    requests.get("http://localhost:8080/howdy/")
    log = stdout.readline()
    assert "w_num=5" in log
