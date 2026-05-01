#!/usr/bin/env python3
"""
Step 3 — LigParGen + BOSS in Docker (one entry point per molecule).

Docker mounts this repo root (the directory that contains ``gromacs_ligpargen/``) as ``/work``.

Paths:
  ``-i single_molecules_pdb/...`` — resolved under ``packmol_initial_system_generation/`` first,
  then under the repo root (same layout as ``step4_ligpargen.py`` on the full Simulations tree).

  ``-p gromacs_ligpargen/ligpargen_runs/...`` — relative to this repo root.

Override the Packmol tree with env ``PACKMOL_PROJECT_ROOT`` if needed.

Examples (from ``github_push/``):

  python3 step3_ligpargen.py \\
    -i single_molecules_pdb/decane.pdb -n decane \\
    -p gromacs_ligpargen/ligpargen_runs/decane -r DEC

  python3 step3_ligpargen.py \\
    -i single_molecules_pdb/hexane.pdb -n hexane \\
    -p gromacs_ligpargen/ligpargen_runs/hexane -r HEX

Prerequisites: Docker, image ``ligpargen-boss:local`` (``./gromacs_ligpargen/docker/build.sh``),
and ``gromacs_ligpargen/boss/BOSS`` present.

Copy-paste examples: see ``LIGPARGEN_EXAMPLES.txt`` in this repo root.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    """Directory that contains ``gromacs_ligpargen/``."""
    return Path(__file__).resolve().parent


def packmol_project_root() -> Path:
    override = os.environ.get("PACKMOL_PROJECT_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    root = repo_root()
    for name in ("packmol_initial_system_generation", "Packmol_initial_system_generation"):
        p = root / name
        if p.is_dir():
            return p.resolve()
    return (root / "packmol_initial_system_generation").resolve()


def docker_relpath(path: Path, mount: Path) -> str:
    return path.resolve().relative_to(mount.resolve()).as_posix()


def resolve_input_for_docker(rel: str, mount: Path, packmol: Path) -> str:
    rel = rel.replace("\\", "/").lstrip("/")
    cand_packmol = (packmol / rel).resolve()
    if cand_packmol.is_file():
        return docker_relpath(cand_packmol, mount)
    cand_mount = (mount / rel).resolve()
    if cand_mount.is_file():
        return docker_relpath(cand_mount, mount)
    print(f"ERROR: PDB not found as:\n  {cand_packmol}\n  {cand_mount}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    root = repo_root()
    packmol = packmol_project_root()
    docker_sh = root / "gromacs_ligpargen" / "docker" / "run_ligpargen_docker.sh"

    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "-i",
        "--input-pdb",
        metavar="REL_PATH",
        help="Monomer PDB path (e.g. single_molecules_pdb/decane.pdb).",
    )
    src.add_argument(
        "-s",
        "--smiles",
        metavar="SMILES",
        help="SMILES; LigParGen builds geometry in the container.",
    )
    p.add_argument("-n", "--name", required=True, help="Output basename (e.g. decane).")
    p.add_argument(
        "-p",
        "--out-dir",
        required=True,
        metavar="REL_PATH",
        help="Output dir under repo root (e.g. gromacs_ligpargen/ligpargen_runs/decane).",
    )
    p.add_argument("-r", "--residue", required=True, help="Residue name in .itp (DEC, HEX, HTB, …).")
    p.add_argument("-c", type=int, default=0, help="Formal charge (default 0).")
    p.add_argument("-o", type=int, default=0, help="LigParGen -o (default 0).")
    p.add_argument("-cgen", default="CM1A-LBCC", help="Charge model (default CM1A-LBCC).")
    p.add_argument("--dry-run", action="store_true", help="Print command only.")
    args = p.parse_args()

    if not docker_sh.is_file():
        print(f"ERROR: Missing {docker_sh}", file=sys.stderr)
        sys.exit(1)

    out_rel = args.out_dir.replace("\\", "/").lstrip("/")
    out_path = root / out_rel
    if not out_rel.startswith("gromacs_ligpargen/"):
        print(
            "WARNING: -p is usually under gromacs_ligpargen/ligpargen_runs/... "
            f"(got {out_rel!r})",
            file=sys.stderr,
        )

    lig_args: list[str] = [
        "-n",
        args.name,
        "-p",
        out_rel,
        "-r",
        args.residue,
        "-c",
        str(args.c),
        "-o",
        str(args.o),
        "-cgen",
        args.cgen,
    ]
    if args.input_pdb:
        rel_i = args.input_pdb.replace("\\", "/").lstrip("/")
        docker_i = resolve_input_for_docker(rel_i, root, packmol)
        lig_args = ["-i", docker_i] + lig_args
    else:
        lig_args = ["-s", args.smiles] + lig_args

    cmd = ["bash", str(docker_sh), *lig_args]

    print("Step 3 — LigParGen (Docker)")
    print(f"  Repo root (/work): {root}")
    print(f"  Packmol tree:      {packmol}")
    print(f"  Command:           {' '.join(cmd)}")
    if args.dry_run:
        return

    rc = subprocess.call(cmd, cwd=str(root))
    if rc != 0:
        sys.exit(rc)
    print(f"Done. See {out_path} for *.gmx.itp and *.gmx.gro")


if __name__ == "__main__":
    main()
