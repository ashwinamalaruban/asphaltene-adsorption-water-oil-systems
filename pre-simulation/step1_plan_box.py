#!/usr/bin/env python3
"""
Step 1 — Compute simulation box dimensions directly from molecule counts (no xlsx needed).

Model:
  V_total = sum_i (N_i * m_i / rho_i)
  m_i = Mw_i / (1000 * N_A)   [kg per molecule]

Outputs:
  - exact cubic edge (A)
  - equivalent non-cubic boxes with same volume (A)

Examples
--------
# Explicit components: name:count:Mw(g/mol):rho(kg/m^3)
python3 step1_plan_box.py \
  --component water:8000:18.015:1000 \
  --component htb:20:750.0:1540 \
  --component hexane:3000:86.178:660

# Use built-in presets by name + count
python3 step1_plan_box.py \
  --use water:8000 \
  --use htb:20 \
  --use hexane:3000
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

AVOGADRO = 6.022e23


@dataclass
class Component:
    name: str
    count: int
    mw_g_mol: float
    rho_kg_m3: float

    @property
    def mass_per_molecule_kg(self) -> float:
        return self.mw_g_mol / (1000.0 * AVOGADRO)

    @property
    def total_mass_kg(self) -> float:
        return self.count * self.mass_per_molecule_kg

    @property
    def occupied_volume_m3(self) -> float:
        return self.total_mass_kg / self.rho_kg_m3


# Adjust/edit these presets as your chemistry model changes.
PRESETS = {
    "water": (18.015, 1000.0),
    "hexane": (84, 660.0),
    "decane": (142.286, 730.0),
    "htb": (859.0, 1540.0),  # asphaltene surrogate
}


def parse_component(s: str) -> Component:
    parts = s.split(":")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(
            f"--component expects name:count:mw:rho, got: {s!r}"
        )
    name = parts[0].strip()
    try:
        count = int(parts[1])
        mw = float(parts[2])
        rho = float(parts[3])
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Bad numeric value in: {s!r}") from exc
    if count <= 0 or mw <= 0 or rho <= 0:
        raise argparse.ArgumentTypeError(f"All values must be positive in: {s!r}")
    return Component(name=name, count=count, mw_g_mol=mw, rho_kg_m3=rho)


def parse_use(s: str) -> Component:
    parts = s.split(":")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"--use expects name:count, got: {s!r}")
    name = parts[0].strip().lower()
    if name not in PRESETS:
        raise argparse.ArgumentTypeError(
            f"Unknown preset {name!r}. Available: {', '.join(sorted(PRESETS))}"
        )
    try:
        count = int(parts[1])
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Bad count in: {s!r}") from exc
    if count <= 0:
        raise argparse.ArgumentTypeError(f"Count must be >0 in: {s!r}")
    mw, rho = PRESETS[name]
    return Component(name=name, count=count, mw_g_mol=mw, rho_kg_m3=rho)


def fmt_box(lx: float, ly: float, lz: float) -> str:
    return f"{lx:8.2f} x {ly:8.2f} x {lz:8.2f}  A"


def monomer_for_name(name: str) -> str:
    n = name.lower()
    if "water" in n:
        return "single_molecules_pdb/water.pdb"
    if "htb" in n or "asph" in n:
        return "single_molecules_pdb/HTBHBC.pdb"
    if "hex" in n or "oil" in n or "decane" in n:
        return "single_molecules_pdb/hexane.pdb"
    return f"<set monomer for {name}>"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--component",
        action="append",
        type=parse_component,
        default=[],
        help="Component as name:count:mw:rho (repeatable).",
    )
    p.add_argument(
        "--use",
        action="append",
        type=parse_use,
        default=[],
        help="Use preset as name:count (repeatable).",
    )
    p.add_argument(
        "--step",
        type=float,
        default=5.0,
        help="Dimension grid step (A) for near-cubic candidates (default 5).",
    )
    p.add_argument(
        "--max-aspect",
        type=float,
        default=4.0,
        help="Max allowed aspect ratio for suggested boxes (default 4).",
    )
    p.add_argument(
        "--round-to",
        type=float,
        default=1.0,
        help="Round suggested dimensions to this step (A), e.g. 1 or 5.",
    )
    p.add_argument("--lx", type=float, default=None, help="Fixed box Lx (A) for thickness mode.")
    p.add_argument("--ly", type=float, default=None, help="Fixed box Ly (A) for thickness mode.")
    p.add_argument("--lz", type=float, default=None, help="Fixed box Lz (A) for thickness mode.")
    p.add_argument(
        "--ask-box",
        action="store_true",
        help="If lx/ly/lz are omitted, interactively pick a suggested box.",
    )
    p.add_argument(
        "--split",
        action="append",
        default=[],
        help=(
            "Component names to split into symmetric left/right slabs "
            "(repeatable), e.g. --split water --split htb"
        ),
    )
    p.add_argument(
        "--print-packmol",
        action="store_true",
        help="In fixed box mode, also print PACKMOL structure blocks.",
    )
    p.add_argument(
        "--asph-margin-xy",
        type=float,
        default=5.0,
        help="Inset margin in x/y for asphaltene slabs in PACKMOL output.",
    )
    args = p.parse_args()

    comps = args.component + args.use
    if not comps:
        raise SystemExit("No inputs provided. Use --component or --use.")

    # Merge duplicate names by summing counts if user mixed repeated entries.
    merged: dict[tuple[str, float, float], int] = {}
    for c in comps:
        key = (c.name, c.mw_g_mol, c.rho_kg_m3)
        merged[key] = merged.get(key, 0) + c.count
    comps = [
        Component(name=k[0], count=n, mw_g_mol=k[1], rho_kg_m3=k[2])
        for k, n in merged.items()
    ]

    v_total_m3 = sum(c.occupied_volume_m3 for c in comps)
    mass_total_kg = sum(c.total_mass_kg for c in comps)
    rho_avg = mass_total_kg / v_total_m3

    # Convert to A^3 for friendly geometry values.
    v_total_A3 = v_total_m3 * 1e30
    l_cube = v_total_A3 ** (1.0 / 3.0)

    print("Box size from molecule counts")
    print("=============================")
    print()
    print("Inputs:")
    print("  name         count     Mw(g/mol)   rho(kg/m^3)    V_i(A^3)")
    for c in comps:
        print(
            f"  {c.name:<10s} {c.count:>8d}   {c.mw_g_mol:>10.3f}   {c.rho_kg_m3:>10.3f}   "
            f"{c.occupied_volume_m3*1e30:>12.2f}"
        )
    print()
    print(f"Total target volume: {v_total_A3:,.2f} A^3")
    print(f"Average density:     {rho_avg:,.3f} kg/m^3")
    print(f"Exact cube edge:     {l_cube:.3f} A")
    print(f"Exact cube box:      {fmt_box(l_cube, l_cube, l_cube)}")
    print()

    # Common aspect-ratio templates for interfacial systems.
    templates = [
        (1, 1, 1),
        (1, 1, 2),
        (1, 1, 3),
        (1, 1, 4),
        (1, 2, 2),
        (2, 2, 3),
    ]
    print("Same-volume template boxes:")
    template_dims = {}
    for a, b, c in templates:
        s = (v_total_A3 / (a * b * c)) ** (1.0 / 3.0)
        lx, ly, lz = a * s, b * s, c * s
        template_dims[(a, b, c)] = (lx, ly, lz)
        print(f"  ratio {a}:{b}:{c} -> {fmt_box(lx, ly, lz)}")
    print()

    # Rounded versions with density impact (very practical for PACKMOL inputs).
    round_to = max(args.round_to, 0.1)

    def rnd(x: float) -> float:
        return round(x / round_to) * round_to

    print(f"Rounded template boxes (rounded to {round_to:g} A) with density error:")
    rounded_templates = []
    for a, b, c in templates:
        lx, ly, lz = template_dims[(a, b, c)]
        lxr, lyr, lzr = rnd(lx), rnd(ly), rnd(lz)
        v_r = lxr * lyr * lzr  # A^3
        rho_r = mass_total_kg / (v_r * 1e-30)
        drho_pct = 100.0 * (rho_r - rho_avg) / rho_avg
        rounded_templates.append((a, b, c, lxr, lyr, lzr, rho_r, drho_pct))
        print(
            f"  ratio {a}:{b}:{c} -> {fmt_box(lxr, lyr, lzr)}   "
            f"rho={rho_r:.2f} kg/m^3  ({drho_pct:+.2f}% vs exact)"
        )
    print()

    # Near-cubic candidates on user grid.
    print("Near-cubic candidate boxes (same volume):")
    step = max(args.step, 0.5)
    low = max(step, l_cube * 0.75)
    high = l_cube * 1.35
    candidates = []
    n = int((high - low) / step) + 1
    for i in range(n):
        lx = low + i * step
        for j in range(n):
            ly = low + j * step
            lz = v_total_A3 / (lx * ly)
            dims = sorted([lx, ly, lz])
            aspect = dims[-1] / dims[0]
            if aspect <= args.max_aspect:
                candidates.append((abs(lz - l_cube), aspect, lx, ly, lz))
    candidates.sort(key=lambda t: (t[0], t[1]))
    for _, aspect, lx, ly, lz in candidates[:10]:
        print(f"  {fmt_box(lx, ly, lz)}   aspect={aspect:.3f}")
    print()
    print("Use one of these dimensions in PACKMOL inside box lines.")

    # Interactive box picker if user did not pass --lx/--ly/--lz.
    if args.lx is None and args.ly is None and args.lz is None and (args.ask_box or sys.stdin.isatty()):
        print()
        print("Choose box dimensions for thickness/PACKMOL mode:")
        options: list[tuple[str, tuple[float, float, float] | None]] = []

        for a, b, c, lxr, lyr, lzr, _, drho in rounded_templates:
            options.append(
                (
                    f"ratio {a}:{b}:{c} rounded -> {fmt_box(lxr, lyr, lzr)} "
                    f"(rho_err={drho:+.2f}%)",
                    (lxr, lyr, lzr),
                )
            )

        for _, _, lx, ly, lz in candidates[:5]:
            lxr, lyr, lzr = rnd(lx), rnd(ly), rnd(lz)
            v_r = lxr * lyr * lzr
            rho_r = mass_total_kg / (v_r * 1e-30)
            drho = 100.0 * (rho_r - rho_avg) / rho_avg
            options.append(
                (
                    f"near-cubic rounded -> {fmt_box(lxr, lyr, lzr)} "
                    f"(rho_err={drho:+.2f}%)",
                    (lxr, lyr, lzr),
                )
            )

        options.append(("custom: enter Lx Ly Lz", None))

        for i, (label, _) in enumerate(options, start=1):
            print(f"  [{i}] {label}")
        raw = input("Option number (Enter to skip thickness mode): ").strip()
        if raw:
            try:
                k = int(raw)
            except ValueError:
                raise SystemExit("Invalid option: must be an integer.")
            if not (1 <= k <= len(options)):
                raise SystemExit("Option out of range.")
            chosen = options[k - 1][1]
            if chosen is None:
                vals = input("Enter Lx Ly Lz in A (e.g. 70 70 200): ").strip().split()
                if len(vals) != 3:
                    raise SystemExit("Need exactly 3 values.")
                args.lx, args.ly, args.lz = map(float, vals)
            else:
                args.lx, args.ly, args.lz = chosen
            print(f"Selected box: {fmt_box(args.lx, args.ly, args.lz)}")

    # Optional: fixed box mode -> thickness from V/Area and slab placement.
    if args.lx is not None and args.ly is not None and args.lz is not None:
        lx, ly, lz = args.lx, args.ly, args.lz
        if lx <= 0 or ly <= 0 or lz <= 0:
            raise SystemExit("--lx/--ly/--lz must be positive.")
        area_A2 = lx * ly
        area_m2 = area_A2 * 1e-20

        split_names = {s.lower() for s in args.split}
        nonsplit = [c for c in comps if c.name.lower() not in split_names]
        split = [c for c in comps if c.name.lower() in split_names]

        # Build slab order: split-left, nonsplit, split-right(reverse) for symmetric interface.
        slabs = []
        for c in split:
            t_A = (c.occupied_volume_m3 / 2.0) / area_m2 * 1e10
            slabs.append((f"{c.name}_left", c, c.count // 2, t_A))
        for c in nonsplit:
            t_A = c.occupied_volume_m3 / area_m2 * 1e10
            slabs.append((c.name, c, c.count, t_A))
        for c in reversed(split):
            t_A = (c.occupied_volume_m3 / 2.0) / area_m2 * 1e10
            slabs.append((f"{c.name}_right", c, c.count - c.count // 2, t_A))

        z = 0.0
        slab_rows = []
        for label, c, ncount, thick in slabs:
            z0 = z
            z1 = z0 + thick
            slab_rows.append((label, c, ncount, thick, z0, z1))
            z = z1

        filled = z
        leftover = lz - filled
        print()
        print("Fixed-box thickness mode")
        print("========================")
        print(f"Input box: {fmt_box(lx, ly, lz)}")
        print(f"Area (Lx*Ly): {area_A2:.2f} A^2")
        print()
        print("Slab thickness from V_i/Area:")
        print("  slab label           molecules   thickness(A)   z_lo(A)   z_hi(A)")
        for label, c, ncount, thick, z0, z1 in slab_rows:
            print(f"  {label:<18s} {ncount:>8d}      {thick:>9.3f}   {z0:>7.3f}   {z1:>7.3f}")
        print()
        print(f"Total filled z: {filled:.3f} A")
        print(f"Remaining z in box: {leftover:.3f} A")
        if abs(leftover) > 1.0:
            print(
                "NOTE: Significant z mismatch. Adjust molecule counts/densities or choose a different box."
            )

        if args.print_packmol:
            print()
            print("Suggested PACKMOL blocks:")
            for label, c, ncount, _, z0, z1 in slab_rows:
                mono = monomer_for_name(c.name)
                is_asph = ("htb" in c.name.lower()) or ("asph" in c.name.lower())
                if is_asph:
                    x0, y0 = args.asph_margin_xy, args.asph_margin_xy
                    x1, y1 = lx - args.asph_margin_xy, ly - args.asph_margin_xy
                else:
                    x0, y0, x1, y1 = 0.0, 0.0, lx, ly
                print(f"\n# --- {label} ---")
                print(f"structure {mono}")
                print(f"  number {ncount}")
                print(f"  inside box {x0:.3f} {y0:.3f} {z0:.3f} {x1:.3f} {y1:.3f} {z1:.3f}")
                print("end structure")


if __name__ == "__main__":
    main()
