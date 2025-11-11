#!/usr/bin/env bash
set -euo pipefail

hatch fmt
hatch run types:check
