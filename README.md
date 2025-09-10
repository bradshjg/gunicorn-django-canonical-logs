# Gunicorn Django Canonical Logs

[![PyPI - Version](https://img.shields.io/pypi/v/gunicorn-django-canonical-logs.svg)](https://pypi.org/project/gunicorn-django-canonical-logs)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gunicorn-django-canonical-logs.svg)](https://pypi.org/project/gunicorn-django-canonical-logs)

-----

`gunicorn-django-canonical-logs` provides extensible [canonical log lines](https://brandur.org/canonical-log-lines) for Gunicorn/Django applications.

## Table of Contents

- [Caveats](#caveats)
- [Installation](#installation)
- [Usage](#usage)
- [Overview](#overview)
  * [Example logs](#example-logs)
  * [Default intstrumenters](#default-instrumenters)
    - [Request intstrumenter](#request-instrumenter)
    - [Exception intstrumenter](#exception-instrumenter)
    - [database intstrument](#database-instrumenter)
    - [saturation intstrument](#saturation-instrumenter)
  * [Default monitors](#default-monitors)
    - [Saturation monitor](#saturation-monitor)
    - [Timeout monitor](#timeout-monitor)
  * [Extending gunicorn-django-canonical-logs](#extending-gunicorn-django-canonical-logs)
- [License](#license)


## Caveats

This is alpha software. It has not (yet!) been battle-tested and does several risky things worth highlighting:

* Overrides Django settings to include custom middleware to gather request/response context
* Modifies Django template rendering and database query execution to gather template exception/database query context
* Runs a separate timeout thread for every request to gather timeout context
* Leverages shared memory between the Gunicorn arbiter and workers to gather saturation context
  - There's currently no cleanup and processes that receive `SIGKILL` will leak memory

## Installation

```console
pip install gunicorn-django-canonical-logs
```

## Usage

Add the following to your Gunicorn configuration file:

```python
from gunicorn_django_canonical_logs.glogging import Logger
from gunicorn_django_canonical_logs.gunicorn_hooks import *  # register Gunicorn hooks and instrumenters

accesslog = "-"
logger_class = Logger
```

> NB Only `sync` Gunicorn worker types are supported

## Overview

The goal is to enhance obersvability by providing reasonable defaults and extensibility to answer two questions:

* If a request was processed, what did it do?
* If a request timed out, what had it done and what was it doing?

A request will generate exactly one of these two `event_type`s:

* `request` - the worker process was able to successfully process the request and return a response
* `timeout` - the worker process timed out before returning a response
  - timeout events include a `timeout_loc`/`timeout_cause_loc`

## Example logs

Examples can be generated from the app used for integration testing:

* `cd tests/server`
* `DJANGO_SETTINGS_MODULE=settings python app.py migrate`
* `DJANGO_SETTINGS_MODULE=settings gunicorn -c gunicorn_config.py app`

And then, from another shell:

* `curl http://localhost:8080/db_queries/`
* `curl http://localhost:8080/rude_sleep/?duration=10`

### Request log

`event_type=request req_method=GET req_path=/db_queries/ req_referrer= req_user_agent=curl/7.88.1 req_view=app.db_queries resp_time=0.026 resp_cpu_time=0.011 resp_status=200 db_queries=3 db_time=0.005 db_dup_queries=2 db_dup_time=0.001 g_w_count=1 g_w_active=0 g_backlog=0 app_key=val`

### Timeout log

`event_type=timeout req_method=GET req_path=/rude_sleep/ req_referrer= req_user_agent=curl/7.88.1 resp_time=0.8 timeout_loc=app.py:73:rude_sleep timeout_cause_loc=app.py:93:simulate_blocking_and_ignoring_signals db_queries=0 db_time=0.000 db_dup_queries=0 db_dup_time=0.000 g_w_count=1 g_w_active=0 g_backlog=0 app_key=val`

### Default instrumenters

#### Request instrumenter

* `req_method` (`string`) - HTTP method (e.g. `GET`/`POST`)
* `req_path` (`string`) - URL path
* `req_referer` (`string`) - `Referrer` HTTP header
* `req_user_agent` (`string`) - `User-Agent` HTTP header
* `resp_time` (`float`) - wall time spent processing the request (in seconds)
* `resp_view` (`string`) - Django view that generated the response
* `resp_cpu_time` (`float`) - CPU time (i.e. ignoring sleep/wait) spent processing the request (in seconds)
* `resp_status` (`int`) - HTTP status code of the response

#### Exception instrumenter

* `exc_type` (`string`) - `type` of the exception
* `exc_message` (`string`) - exception message
* `exc_loc` (`string`) - `{module}:{line_number}:{name}` of the top of the stack (i.e. the last place the
  exception could've been handled)
* `exc_cause_loc` (`string`) - `{module}:{line_number}:{name}` of the frame that threw the exception
* `exc_template` (`string`) - `{template_name}:{line_number}` (if raised during template rendering)

> NB There's some subtlety in how `loc`/`cause_loc` work; they attempt to provide application-relevant info by
> ignoring frames in library code if application frames are available.

#### Database instrumenter

* `db_queries` (`int`) - total number of queries executed
* `db_time` (`float`) - total time spent executing queries (in seconds)
* `db_dup_queries` (`int`) - total number of non-unique queries; could indicate N+1 issues
* `db_dup_time` (`float`) - total time spent executing non-unique queries (in seconds); could indicate N+1 issues

#### Saturation instrumenter

* `g_w_count` (`int`) - total number of Gunicorn workers
* `g_w_active` (`int`) - number of active Gunicorn workers
* `g_w_backlog` (`int`) - number of queued requests

> NB These values are sampled about once a second, and represent a snapshot. To derive useful data, average the values over time.

### Default monitors

#### Saturation monitor

The saturation monitor samples and aggregates Gunicorn data; it provides data on the current number of active/idle workers
as well as the number of queued requests that have not been assigned to a worker.

#### Timeout monitor

The timeout monitor wakes up slightly before the Gunicorn timeout in order to emit stack frame and instrumenter data before
Gunicorn recycles the worker.

## Extending gunicorn-django-canonical-logs

### Application-specific context

from anywhere in your application, use

```python
from gunicorn_django_canonical_logs import Context

Context.set("key", "val")
```

This will add `app_key=val` to the log for the current request, and context will be automatically cleared for the next request.

### Custom instrumenters

```python
from gunicorn_django_canonical_logs import Context, register_instrumenter

@register_instrumenter
class MyInstrumenter:
    def setup(self):
        pass  # called once after forking a Gunicorn worker

    def call(self):
        pass  # called every time an event is emitted
```

> NB The application must import the instrumenter for it to register itself.

## License

`gunicorn-django-canonical-logs` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
