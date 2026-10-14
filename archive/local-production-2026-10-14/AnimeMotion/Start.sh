#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
echo 'Open http://127.0.0.1:8765 in your browser once the server starts.'
exec python3 studio.py "$@"
