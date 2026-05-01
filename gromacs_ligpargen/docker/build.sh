#!/usr/bin/env bash
# Build image: ligpargen-boss:local
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CTX="$(cd "$HERE/.." && pwd)"
cd "$CTX"
docker build --platform linux/amd64 -f docker/Dockerfile -t ligpargen-boss:local "$CTX"
