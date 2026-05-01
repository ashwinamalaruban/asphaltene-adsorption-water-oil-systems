# LigParGen + BOSS (Docker)

BOSS is **Linux 32-bit**. The image is **linux/amd64** with **i386** libs. On **Apple Silicon**, enable **Rosetta for x86/amd64** in Docker Desktop → Settings → General.

## `/work` root

`run_ligpargen_docker.sh` mounts the **parent of `gromacs_ligpargen/`** as `/work` (your **repo root**: the folder that contains `gromacs_ligpargen/` and `step3_ligpargen.py`).

Paths `-i` and `-p` are **relative to that root**.

**Easiest:** from repo root, use **`python3 step3_ligpargen.py`** (see **`../LIGPARGEN_EXAMPLES.txt`**).

## BOSS

You need **`gromacs_ligpargen/boss/BOSS`** on the host (already in this bundle). If you ever start from scratch, unpack Yale’s `boss0824.tar.gz` here so `./boss/BOSS` exists.

## Build

From **repo root** (parent of `gromacs_ligpargen/`):

```bash
./gromacs_ligpargen/docker/build.sh
```

Re-run after edits under `gromacs_ligpargen/ligpargen_src/`.

## Run (raw docker)

From repo root:

```bash
./gromacs_ligpargen/docker/run_ligpargen_docker.sh \
  -i packmol_initial_system_generation/single_molecules_pdb/hexane.pdb \
  -n hexane -p gromacs_ligpargen/ligpargen_runs/hexane -r HEX -c 0 -o 0 -cgen CM1A-LBCC
```

## No Docker?

Use the [LigParGen web server](https://zarbi.chem.yale.edu/ligpargen/) with your PDBs.
