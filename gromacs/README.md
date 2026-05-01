# GROMACS workflow (Bridges-2): `asph_in_decane_20`

This folder contains the `.mdp` files and command sequence to run a full MD workflow on Bridges-2 for the decane-20 bundle case.

`asph_in_decane_20` means: **20 HTBHBC (asphaltene) molecules in a decane slab system** with Packmol block order
`4000 SOL | 20 HTB | 3000 DEC | 4000 SOL`.

## Folder contents

- `topol_decane20_bundle.top`
- `mdp_files/em_decane20_bundle.mdp`
- `mdp_files/nvt_decane20_bundle.mdp`
- `mdp_files/npt_decane20_bundle.mdp`
- `mdp_files/md_decane20_bundle_prod_50ns.mdp`

## ITP includes used by `topol_decane20_bundle.top`

These are referenced from:
`../pre-simulation/itp_files/`

- `ff_OPLSAA__defaults.itp`
- `water_TIP3P__tip3p_atomtypes.itp`
- `water_TIP3P__tip3p.itp`
- `mol_HTB__HTBHBC_ligpargen.gmx.itp`
- `mol_DEC__decane_atomtypes_for_topol.itp`
- `mol_DEC__decane_molecule_for_topol.itp`

## Required external file (prepare/upload separately)

- Coordinates already prepared for GROMACS naming (example: `decane20_for_gmx.pdb`)

## Environment

```bash
module purge
module load cuda/10.2.0
module load gromacs/2020.4-gpu
export LD_LIBRARY_PATH=/jet/packages/intel/compilers_and_libraries_2020.4.304/linux/mpi/intel64/libfabric/lib:${LD_LIBRARY_PATH}
export OMP_NUM_THREADS=8
```

## 1) Build periodic box

```bash
mpirun -np 1 gmx_mpi editconf \
  -f decane20_for_gmx.pdb \
  -o decane20_boxed.gro \
  -c -d 1.0 -bt cubic
```

## 2) Energy minimization (EM)

```bash
mpirun -np 1 gmx_mpi grompp \
  -f gromacs/mdp_files/em_decane20_bundle.mdp \
  -c decane20_boxed.gro \
  -p gromacs/topol_decane20_bundle.top \
  -o decane20_em.tpr \
  -maxwarn 5

mpirun -np 1 gmx_mpi mdrun \
  -v -deffnm decane20_em \
  -ntomp ${OMP_NUM_THREADS}
```

## 3) NVT equilibration

```bash
mpirun -np 1 gmx_mpi grompp \
  -f gromacs/mdp_files/nvt_decane20_bundle.mdp \
  -c decane20_em.gro \
  -p gromacs/topol_decane20_bundle.top \
  -o decane20_nvt.tpr \
  -maxwarn 5

mpirun -np 1 gmx_mpi mdrun \
  -v -deffnm decane20_nvt \
  -ntomp ${OMP_NUM_THREADS} \
  -nb gpu -pme gpu -bonded gpu
```

## 4) NPT equilibration

```bash
mpirun -np 1 gmx_mpi grompp \
  -f gromacs/mdp_files/npt_decane20_bundle.mdp \
  -c decane20_nvt.gro \
  -r decane20_nvt.gro \
  -t decane20_nvt.cpt \
  -p gromacs/topol_decane20_bundle.top \
  -o decane20_npt.tpr \
  -maxwarn 5

mpirun -np 1 gmx_mpi mdrun \
  -v -deffnm decane20_npt \
  -ntomp ${OMP_NUM_THREADS} \
  -nb gpu -pme gpu -bonded gpu
```

## 5) 50 ns production

```bash
mpirun -np 1 gmx_mpi grompp \
  -f gromacs/mdp_files/md_decane20_bundle_prod_50ns.mdp \
  -c decane20_npt.gro \
  -t decane20_npt.cpt \
  -p gromacs/topol_decane20_bundle.top \
  -o decane20_md50ns.tpr \
  -maxwarn 5

mpirun -np 1 gmx_mpi mdrun \
  -v -deffnm decane20_md50ns \
  -ntomp ${OMP_NUM_THREADS} \
  -nb gpu -pme gpu -bonded gpu -update gpu
```

## Notes

- If GPU flags fail on your node, retry with:
  `-nb gpu -pme gpu` only.
- Ensure all `#include` paths in `gromacs/topol_decane20_bundle.top` remain valid on Bridges-2.
