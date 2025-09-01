# SPDX-FileCopyrightText: 2025-present James Bradshaw <james.g.bradshaw@gmail.com>
#
# SPDX-License-Identifier: MIT
from gunicorn_django_wide_events import (
    instrumenters,  # noqa: F401 registers hooks
    monitors,  # noqa: F401 registers hooks
)
