# Gunicorn Django wide events

[![PyPI - Version](https://img.shields.io/pypi/v/gunicorn-django-wide-events.svg)](https://pypi.org/project/gunicorn-django-wide-events)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gunicorn-django-wide-events.svg)](https://pypi.org/project/gunicorn-django-wide-events)

-----

`gunicorn-django-wide-events` provides TODO

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Overview](#overview)
  * [Monitoring](#monitoring)
  * [Timeouts](#timeouts)
- [License](#license)

## Installation

```console
pip install gunicorn-django-wide-events
```

## Usage

TODO

## Overview

The goal is to enhance obersability by providing reasonable defaults and extensibility to answer two questions:

* If my request succeeded, what did it do?
* If my request timed out, what was it trying to do?

To help answer those questions, two base types of events are used. A request will generate exactly one of these two types:

* `request` - when the worker process was able to successfully process the request and return a response.
* `timeout` - when the worker process timed out before returning a response

## Monitoring

To provide insight into server state, process manager runs a monitoring thread that collects data about worker processes. Shared memory is used so that worker processes can enhance their events with server data that would otherwise not be available to them (data about their siblings).

## Timeouts

To support timeout events with application-level data, each request spawns a timeout thread with a shorter timeout than the master process'. When that timeout is reached, the worker will emit a timeout event before aborting itself. The worker-internal timeout thread provides the ability to log application-level data that might escape the view of the `worker_abort` hook, since it relies on Python context switching instead of OS context switching. A C extension that doesn't checkpoint often enough could otherwise result in the master gunicorn process ungracefully killing the worker without `worker_abort` ever firing.

## License

`gunicorn-django-wide-events` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
