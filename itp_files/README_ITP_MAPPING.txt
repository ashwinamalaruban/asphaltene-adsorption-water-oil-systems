ITP files collected and renamed for clarity
=========================================

Naming style
- packed systems (PDB): packed_<oil>_htbhbc<count>_<oilcount>_water<totalwater>.pdb
- system ITP copies:    system_<oil>_htbhbc<count>_<oilcount>_water<totalwater>__<RES>.itp
- molecule ITPs:        mol_<RES>__<name>_ligpargen.gmx.itp

Prefix meaning
- mol_*      : molecule-level LigParGen outputs (DEC/HEX/HEP/HTB)
- water_*    : TIP3P include files
- ff_*       : force-field defaults include
- system_*   : system-specific HEX/HTB copies aligned with packed PDB naming

Examples
- packed_hexane_htbhbc10_hex3000_water8000*.pdb
  use system_hexane_htbhbc10_hex3000_water8000__HEX.itp
      system_hexane_htbhbc10_hex3000_water8000__HTB.itp

- packed_hexane_htbhbc20_hex3000_water8000*.pdb
  use system_hexane_htbhbc20_hex3000_water8000__HEX.itp
      system_hexane_htbhbc20_hex3000_water8000__HTB.itp

- packed_decane_htbhbc20_dec3000_water8000.pdb
- packed_decane_htbhbc40_dec3000_water8000.pdb
  use mol_DEC__decane_ligpargen.gmx.itp + mol_HTB__HTBHBC_ligpargen.gmx.itp

Note
- These are copies. Originals are kept in their source directories.
