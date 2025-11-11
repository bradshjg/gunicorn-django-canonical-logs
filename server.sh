#!/usr/bin/env bash
set -euo pipefail

gunicorn --bind 127.0.0.1:8888 -c tests/server/gunicorn_config.py tests.server.app
