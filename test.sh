#!/usr/bin/env bash
set -euo pipefail

hatch env remove hatch-test
hatch test "$@"
