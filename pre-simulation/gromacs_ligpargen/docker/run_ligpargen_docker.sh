#!/usr/bin/env bash
# Run LigParGen + BOSS inside Linux (works on macOS via Docker).
# Prerequisites: Docker Desktop, image built (./docker/build.sh), boss/ unpacked next to docker/
#
# Example (from Simulations/ as Docker /work):
#   ./gromacs_ligpargen/docker/run_ligpargen_docker.sh \\
#     -i Packmol_initial_system_generation/single_molecules_pdb/hexane.pdb \\
#     -n hexane -p gromacs_ligpargen/ligpargen_runs/hex -r HEX -c 0 -o 0 -cgen CM1A-LBCC
#
# Paths are relative to **Simulations/** (parent of this ``gromacs_ligpargen/`` folder), bind-mounted as /work.

set -euo pipefail
GR="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$GR/.." && pwd)"
IMG="${LIGPARGEN_IMAGE:-ligpargen-boss:local}"

if ! docker image inspect "$IMG" &>/dev/null; then
  echo "Image $IMG not found. Build first:"
  echo "  $GR/docker/build.sh"
  exit 1
fi
if [[ ! -x "$GR/boss/BOSS" ]]; then
  echo "Missing $GR/boss/BOSS — unpack boss0824.tar.gz into gromacs_ligpargen/boss/"
  exit 1
fi

exec docker run --rm \
  --platform linux/amd64 \
  -v "$GR/boss:/boss:ro" \
  -v "$ROOT:/work" \
  -w /work \
  "$IMG" \
  "$@"
