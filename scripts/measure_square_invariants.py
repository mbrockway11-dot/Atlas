"""Static structural fingerprint of the seven planetary Kameas.

The Structural Plane, computed: each square as a graph, measured. No history, no
interpretation -- measurements licensed by mathematics only. Grid-topology
columns are size-driven (every n x n grid is the same shape); the value and
sigil columns are specific to how each square is arranged.

    .venv/Scripts/python.exe scripts/measure_square_invariants.py
"""

from __future__ import annotations

from atlas.kamea.square_invariants import all_square_invariants

ORDER = ["saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon"]


def main() -> None:
    inv = all_square_invariants()

    print("=== GRID TOPOLOGY (canonical, but size-driven) ===")
    print(f"{'planet':9} {'n':>2} {'nodes':>5} {'edges':>5} {'diam':>4} "
          f"{'avgpath':>7} {'spec_rad':>8} {'alg_conn':>8} {'autos':>5}")
    for key in ORDER:
        s = inv[key]
        print(f"{s.planet:9} {s.size:>2} {s.grid_nodes:>5} {s.grid_edges:>5} "
              f"{s.grid_diameter:>4} {s.grid_average_shortest_path:>7.3f} "
              f"{s.grid_spectral_radius:>8.3f} {s.grid_algebraic_connectivity:>8.3f} "
              f"{s.grid_automorphisms:>5}")

    print("\n=== VALUE ARRANGEMENT (specific to each square) ===")
    print(f"{'planet':9} {'mean|d|':>7} {'var|d|':>8} {'max|d|':>6} "
          f"{'assort':>7} {'consec':>7} {'semimagic':>9} {'fullmagic':>9}")
    for key in ORDER:
        s = inv[key]
        print(f"{s.planet:9} {s.value_mean_abs_neighbor_delta:>7.2f} "
              f"{s.value_var_abs_neighbor_delta:>8.2f} {s.value_max_neighbor_delta:>6} "
              f"{s.value_neighbor_assortativity:>7.3f} "
              f"{s.value_consecutive_edge_fraction:>7.3f} "
              f"{str(s.semimagic):>9} {str(s.fully_magic):>9}")

    print("\n=== SIGIL GEOMETRY (the seal 1..n^2, specific to each square) ===")
    print(f"{'planet':9} {'length':>9} {'mean_step':>9} {'crossings':>9} "
          f"{'turn_entropy':>12}")
    for key in ORDER:
        s = inv[key]
        print(f"{s.planet:9} {s.sigil_length:>9.2f} {s.sigil_mean_step:>9.3f} "
              f"{s.sigil_self_intersections:>9} {s.sigil_turning_entropy:>12.3f}")

    print("\nNote: grid automorphisms are 8 (the board's dihedral group) for every"
          "\nsquare -- graph symmetry does not distinguish them. Their arrangement"
          "\ndoes: see the value and sigil columns. Mercury is the only square that"
          "\nis semimagic but not fully magic (broken anti-diagonal).")


if __name__ == "__main__":
    main()
