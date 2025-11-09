# noqa: INP001 intentionally not a package, part of pytest tests
from __future__ import annotations

import re
import shlex
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


def read_log_lines(fp: IO[str]) -> list[str]:
    time.sleep(1)
    fp.flush()
    fp.seek(0)
    return fp.readlines()


def get_parsed_canonical_logs(fp: IO[str], event_type="request") -> list[dict[str, str]]:
    """Returns a list of dictionaries of the key-value pairs in canonical logs of the given event type.

    NB this is unable to parse lines a "real" logfmt parser would, e.g. it breaks on values with "=" in them.

    Example:

    ```
    event_type="request" req_method="GET" resp_time=0.001
    random other log line
    event_type="other" is="ignored"
    event_type="request" req_method="POST"
    ```

    -> [
      {"event_type": "request", "req_method": "GET", "resp_time": "0.001"},
      {"event_type": "request", "req_method": "POST"},
    ]
    """
    lines = read_log_lines(fp)
    canonical_lines = [line for line in lines if line.startswith(f'event_type="{event_type}"')]
    # HACK HACK HACK the idea behind this "parser" is to let shlex handle preserving spaces within quoted logfmt values
    parsed_lines = []
    for line in canonical_lines:
        word_split = shlex.split(" ".join(line.strip().split("=")))
        word_split_iter = iter(word_split)
        parsed_lines.append({pair[0]: pair[1] for pair in dict(zip(word_split_iter, word_split_iter)).items()})
    return parsed_lines


def test_context_reset_between_requests(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    custom_event_key = "app_custom_event"

    requests.get("http://localhost:8080/custom_event/")

    logs = get_parsed_canonical_logs(stdout)
    assert len(logs) == 1
    assert logs[0][custom_event_key] == "1"

    # context reset between requests
    clear_output(stdout)
    requests.get("http://localhost:8080/ok/")

    logs = get_parsed_canonical_logs(stdout)
    assert len(logs) == 1
    assert custom_event_key not in logs[0]


def test_access_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/ok/")

    logs = get_parsed_canonical_logs(stdout)
    assert len(logs) == 1
    assert logs[0]["req_path"] == "/ok/"
    assert logs[0]["resp_status"] == "200"


def test_saturation_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/ok/")

    logs = get_parsed_canonical_logs(stdout)
    assert len(logs) == 1
    assert logs[0]["g_w_count"] == str(workers)


def test_exception_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/view_exception/")

    logs = get_parsed_canonical_logs(stdout)
    assert len(logs) == 1
    assert logs[0]["resp_status"] == "500"
    assert logs[0]["exc_type"] == "MyError"
    assert logs[0]["exc_msg"] == "Oh noes!"
    assert re.search(r"app.py:\d+:view_exception", logs[0]["exc_loc"])
    assert re.search(r"app.py:\d+:func_that_throws", logs[0]["exc_cause_loc"])


def test_template_exception_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/template_callable_exception/")

    logs = get_parsed_canonical_logs(stdout)
    assert len(logs) == 1
    assert logs[0]["resp_status"] == "500"
    assert logs[0]["exc_type"] == "MyError"
    assert logs[0]["exc_msg"] == "Oh noes!"
    assert re.search(r"callable_exception.html:\d+", logs[0]["exc_template"])
    assert re.search(r"app.py:\d+:template_callable_exception", logs[0]["exc_loc"])
    assert re.search(r"app.py:\d+:func_that_throws", logs[0]["exc_cause_loc"])


@pytest.mark.django_db
def test_db_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/db_queries/")

    logs = get_parsed_canonical_logs(stdout)
    assert len(logs) == 1
    assert logs[0]["resp_status"] == "200"
    assert logs[0]["db_queries"] == "3"


def test_custom_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/custom_event/")

    logs = get_parsed_canonical_logs(stdout)
    assert len(logs) == 1
    assert logs[0]["app_custom_event"] == "1"


def test_custom_timing(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/custom_timing/")

    logs = get_parsed_canonical_logs(stdout)
    assert len(logs) == 1
    assert re.search(r"0.2\d{2}", logs[0]["app_custom_time"])


def test_app_instrumenter(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/custom_event/")

    logs = get_parsed_canonical_logs(stdout)
    assert len(logs) == 1
    assert logs[0]["app_key"] == "val"


def test_timeout_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    requests.get("http://localhost:8080/sleep/?duration=10")

    logs = get_parsed_canonical_logs(stdout, event_type="timeout")
    assert len(logs) == 1
    assert re.search(r"app\.py:\d+:sleep", logs[0]["timeout_loc"])
    assert re.search(r"app\.py:\d+:simulate_blocking", logs[0]["timeout_cause_loc"])


def test_sigkill_timeout_event(server) -> None:
    stdout, _ = server
    clear_output(stdout)

    with pytest.raises(requests.ConnectionError):  # worker SIGKILL will abort connection
        requests.get("http://localhost:8080/rude_sleep/?duration=10")

    logs = get_parsed_canonical_logs(stdout, event_type="timeout")
    assert len(logs) == 1
    assert re.search(r"app\.py:\d+:rude_sleep", logs[0]["timeout_loc"])
    assert re.search(r"app\.py:\d+:simulate_blocking_and_ignoring_signals", logs[0]["timeout_cause_loc"])
