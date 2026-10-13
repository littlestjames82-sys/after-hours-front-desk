#!/usr/bin/env bash
# Run the After-Hours Front Desk simulator in THIS sandbox.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$(dirname "$0")/env-sandbox.sh"
exec python3 "$ROOT/desk/server.py"
