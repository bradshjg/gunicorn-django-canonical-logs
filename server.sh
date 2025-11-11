#!/usr/bin/env bash
set -euo pipefail

cd tests/server
hatch run server:start
