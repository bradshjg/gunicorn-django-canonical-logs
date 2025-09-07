# Gunicorn Django canonical logs

[![PyPI - Version](https://img.shields.io/pypi/v/gunicorn-django-canonical-logs.svg)](https://pypi.org/project/gunicorn-django-canonical-logs)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gunicorn-django-canonical-logs.svg)](https://pypi.org/project/gunicorn-django-canonical-logs)

-----

`gunicorn-django-canonical-logs` provides extensible [canonical log lines](https://brandur.org/canonical-log-lines) for Gunicorn/Django applications.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Overview](#overview)
  * [Monitoring](#monitoring)
  * [Timeouts](#timeouts)
- [License](#license)

## Installation

```console
pip install gunicorn-django-canonical-logs
```

## Usage

Add the following to your gunicorn configuration file:

```python
from gunicorn_django_wide_events.glogging import Logger  #
from gunicorn_django_wide_events.gunicorn_hooks import *  # register gunicorn hooks and instrumenters

accesslog = "-"
logger_class = Logger
```

## Overview

The goal is to enhance obersvability by providing reasonable defaults and extensibility to answer two questions:

* If my request succeeded, what did it do?
* If my request timed out, what was it trying to do?

To help answer those questions, two base types of events are used. A request will generate exactly one of these two `event_type`s:

* `request` - when the worker process was able to successfully process the request and return a response.
* `timeout` - when the worker process timed out before returning a response

## Example logs

TODO: add examples

## Adding instrumenters

TODO: add docs on adding instrumenters

## License

`gunicorn-django-canonical-logs` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
