#!/usr/bin/env bash
set -euo pipefail

hatch env remove server
cd tests/server
hatch run server:start
