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


def test_hello(server: tuple[IO[str], IO[str]]) -> None:
    stdout, _ = server
    requests.get("http://localhost:8080/hello/")
    log = stdout.readline()
    assert "GET /hello/" in log


def test_howdy(server: tuple[IO[str], IO[str]]) -> None:
    stdout, _ = server
    requests.get("http://localhost:8080/howdy/")
    log = stdout.readline()
    assert "GET /howdy/" in log
