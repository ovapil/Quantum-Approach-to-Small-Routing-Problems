import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from topology import create_test_topology

from binary_encoding import create_edge_mapping

from exact_solver import solve_qubo_exact

def run_penalty_experiment():
    graph = create_test_topology()

    source = "A"
    destination = "D"

    mapping = create_edge_mapping(graph)

    penalties = [
        0.5,
        1.0,
        2.0,
        2.5,
        3.0,
        5.0,
        10.0
    ]

    print("=" * 90)
    print("QUBO PENALTY SWEEP")
    print("=" * 90)

    print(
        f"{'A':>6} | "
        f"{'Best':>8} | "
        f"{'Energy':>8} | "
        f"{'Cost':>6} | "
        f"{'Feasible':>10} | "
        f"{'Edges'}"
    )

    print("-" * 90)

    for penalty in penalties:
        results = solve_qubo_exact(
            graph,
            mapping,
            source,
            destination,
            penalty
        )

        best = results[0]

        print(
            f"{penalty:6.2f} | "
            f"{best['bitstring']:>8} | "
            f"{best['energy']:8.2f} | "
            f"{best['route_cost']:6} | "
            f"{str(best['feasible']):>10} | "
            f"{best['selected_edges']}"
        )


if __name__ == "__main__":
    run_penalty_experiment()