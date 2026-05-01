# GROMACS workflow (Bridges-2): `asph_in_decane_20`

This folder contains the `.mdp` files and command sequence to run a full MD workflow on Bridges-2 for the decane-20 bundle case.

Relabeling is intentionally excluded here because that step is done on your local computer before upload.

## Folder contents

- `mdp_files/em_decane20_bundle.mdp`
- `mdp_files/nvt_decane20_bundle.mdp`
- `mdp_files/npt_decane20_bundle.mdp`
- `mdp_files/md_decane20_bundle_prod_50ns.mdp`

## Required external files (prepare/upload separately)

- Coordinates already prepared for GROMACS naming (example: `decane20_for_gmx.pdb`)
- Topology: `topol_decane20_bundle.top`
- Any included `.itp` files referenced by your topology

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
  -p topol_decane20_bundle.top \
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
  -p topol_decane20_bundle.top \
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
  -p topol_decane20_bundle.top \
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
  -p topol_decane20_bundle.top \
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
- Ensure all paths in `topol_decane20_bundle.top` are valid on Bridges-2.
