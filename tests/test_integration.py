from __future__ import annotations

import re
import subprocess
import tempfile
import time
from typing import IO, TYPE_CHECKING

import pytest
import requests

from server.gunicorn_config import workers

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(scope="module")
def server() -> Generator[tuple[IO[str], IO[str]], None, None]:
    fp_stdout = tempfile.TemporaryFile(mode="w+")
    fp_stderr = tempfile.TemporaryFile(mode="w+")

    s_proc = subprocess.Popen(
        ["gunicorn", "-c", "./tests/server/gunicorn_config.py", "tests.server.app"],
        stdout=fp_stdout,
        stderr=fp_stderr,
        bufsize=1,  # line buffered
        text=True,
    )

    time.sleep(5)  # HACK wait for server boot and saturation monitor to start emitting data

    try:
        yield fp_stdout, fp_stderr
    finally:
        s_proc.terminate()
        s_proc.wait()


def clear_output(fp: IO[str]) -> None:
    fp.seek(0)
    fp.truncate()


def read_first_line(fp: IO[str]) -> str:
    time.sleep(1)
    fp.flush()
    fp.seek(0)
    return fp.readline()


def test_context_reset_between_requests(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/custom_event/")

    log = read_first_line(stdout)
    assert 'custom_event="1"' in log

    # context reset between requests
    clear_output(stdout)
    requests.get("http://localhost:8080/ok/")

    log = read_first_line(stdout)
    assert 'custom_event="1"' not in log


def test_access_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/ok/")

    log = read_first_line(stdout)
    assert log.startswith('event_type="request"')
    assert 'req_path="/ok/"' in log
    assert 'resp_status="200"' in log


def test_saturation_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/ok/")

    log = read_first_line(stdout)
    assert f'w_count="{workers}"' in log


def test_exception_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/view_exception/")

    log = read_first_line(stdout)
    assert 'resp_status="500"' in log
    assert 'exc_type="MyError"' in log
    assert 'exc_msg="Oh noes!"' in log
    assert re.search(r'exc_loc="app.py:\d+:view_exception"', log)
    assert re.search(r'exc_cause_loc="app.py:\d+:func_that_throws"', log)


def test_template_exception_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/template_callable_exception/")

    log = read_first_line(stdout)
    assert 'resp_status="500"' in log
    assert 'exc_type="MyError"' in log
    assert 'exc_msg="Oh noes!"' in log
    assert re.search(r'exc_template="callable_exception.html:\d+"', log)
    assert re.search(r'exc_loc="app.py:\d+:template_callable_exception"', log)
    assert re.search(r'exc_cause_loc="app.py:\d+:func_that_throws"', log)


@pytest.mark.django_db
def test_db_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/db_queries/")

    log = read_first_line(stdout)
    assert 'resp_status="200"' in log
    assert 'db_queries="3"' in log


def test_custom_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/custom_event/")

    log = read_first_line(stdout)
    assert 'custom_event="1"' in log


def test_app_instrumenter(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/custom_event/")

    log = read_first_line(stdout)
    assert 'app_key="val"' in log


def test_timeout_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/sleep/?duration=10")

    log = read_first_line(stdout)
    assert log.startswith('event_type="timeout"')
    assert re.search(r'timeout_loc="app\.py:\d+:sleep"', log)
    assert re.search(r'timeout_cause_loc="app\.py:\d+:simulate_blocking"', log)


def test_sigkill_timeout_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    with pytest.raises(requests.ConnectionError):  # worker SIGKILL will abort connection
        requests.get("http://localhost:8080/rude_sleep/?duration=10")

    log = read_first_line(stdout)
    assert log.startswith('event_type="timeout"')
    assert re.search(r'timeout_loc="app\.py:\d+:rude_sleep"', log)
    assert re.search(r'timeout_cause_loc="app\.py:\d+:simulate_blocking_and_ignoring_signals"', log)
