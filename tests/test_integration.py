from __future__ import annotations

import subprocess
import time
from typing import IO, Generator

import pytest
import requests

from tests.server.gunicorn_config import workers


@pytest.fixture(scope="session")
def server() -> Generator[tuple[IO[str], IO[str]], None, None]:
    s_proc = subprocess.Popen(
        ["gunicorn", "-c", "./tests/server/gunicorn_config.py", "tests.server.app"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,  # line buffered
        text=True,
    )

    time.sleep(5)  # HACK wait for server boot and saturation monitor to start emitting data

    try:
        yield s_proc.stdout, s_proc.stderr
    finally:
        s_proc.terminate()
        s_proc.wait()


def test_access_event(server) -> None:
    stdout, _ = server
    requests.get("http://localhost:8080/ok/")
    log = stdout.readline()
    assert 'req_path="/ok/"' in log
    assert "resp_status=200" in log


def test_saturation_event(server) -> None:
    stdout, _ = server

    requests.get("http://localhost:8080/ok/")
    log = stdout.readline()
    assert f"w_num={workers}" in log


def test_exception_event(server) -> None:
    stdout, _ = server

    requests.get("http://localhost:8080/view_exception/")
    log = stdout.readline()
    assert "resp_status=500" in log
    assert 'exc_type=MyError exc_msg="Oh noes!"' in log


def test_custom_event(server) -> None:
    stdout, _ = server

    requests.get("http://localhost:8080/custom_event/")
    log = stdout.readline()
    assert "custom_event=1" in log


def test_context_reset_between_requests(server) -> None:
    stdout, _ = server

    requests.get("http://localhost:8080/custom_event/")
    log = stdout.readline()
    assert "custom_event=1" in log

    # context reset between requests
    requests.get("http://localhost:8080/ok/")
    log = stdout.readline()
    assert "custom_event=1" not in log
