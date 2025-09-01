from __future__ import annotations

import subprocess
from typing import IO, Generator

import pytest
import requests

from tests.server.gunicorn_config import workers


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


def test_ok(server) -> None:
    stdout, _ = server
    requests.get("http://localhost:8080/ok/")
    log = stdout.readline()
    assert 'req_path="/ok/"' in log
    assert "resp_status=200" in log


def test_worker_count(server) -> None:
    stdout, _ = server
    import time

    time.sleep(2)  # HACK: find a way to ensure the saturation monitor is emitting data
    requests.get("http://localhost:8080/ok/")
    log = stdout.readline()
    assert f"w_num={workers}" in log
