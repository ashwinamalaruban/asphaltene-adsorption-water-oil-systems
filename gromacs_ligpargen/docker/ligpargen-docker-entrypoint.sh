#!/usr/bin/env bash
set -e
export BOSSdir="${BOSSdir:-/boss}"
if [[ ! -x "${BOSSdir}/BOSS" ]]; then
  echo "ERROR: Mount BOSS at ${BOSSdir} (expected executable ${BOSSdir}/BOSS)."
  exit 1
fi
if ! command -v obabel &>/dev/null; then
  echo "ERROR: obabel not found in container."
  exit 1
fi
exec ligpargen "$@"
