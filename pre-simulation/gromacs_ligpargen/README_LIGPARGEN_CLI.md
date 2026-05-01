# LigParGen in this bundle

Upstream: [github.com/Isra3l/ligpargen](https://github.com/Isra3l/ligpargen). Vendored code: **`ligpargen_src/`**.

## Recommended: Docker + `step3_ligpargen.py`

From the **repo root** (directory containing `step3_ligpargen.py`):

1. **`./gromacs_ligpargen/docker/build.sh`** once  
2. **`python3 step3_ligpargen.py ...`** — copy-paste examples in **`../LIGPARGEN_EXAMPLES.txt`**  
3. Details: **`docker/README_DOCKER.md`**

Outputs: **`*.gmx.itp`** and **`*.gmx.gro`** under the `-p` output directory.

## PDB inputs

All hydrogens present; residue names in PDBs should match what you pass as **`-r`** (e.g. `DEC`, `HEX`, `HTB`) and your planned `topol`.

## Native macOS LigParGen (no Docker)

Not supported here: the Yale **BOSS** binary is **Linux i386**. Use **Docker** (above), a **Linux machine**, or the [web server](https://zarbi.chem.yale.edu/ligpargen/).
