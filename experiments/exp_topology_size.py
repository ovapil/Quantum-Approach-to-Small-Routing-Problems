
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from metrics import (
    shortest_path_dijkstra,
    measure_dijkstra,
    scaling_info,
    save_results_csv,
)


DATA_DIR = ROOT / "data"
OUTPUT_FILE = (
    ROOT / "experiments" / "results"
    / "topology_size.csv"
)

SIZES = [6, 8, 10]
REPEATS = 1000


def load_topology(size):
    file_path = DATA_DIR / f"topology_{size}.json"

    with file_path.open(
        "r", encoding="utf-8"
    ) as file:
        data = json.load(file)

    assert data["directed"] is True
    assert len(data["nodes"]) == size

    edges = [
        (e["source"], e["target"], e["weight"])
        for e in data["edges"]
    ]

    return data, edges


def run_experiment():
    results = []

    print("=" * 65)
    print("WEEK 5 - EXPERIMENT A: TOPOLOGY SIZE")
    print("=" * 65)

    for size in SIZES:
        data, edges = load_topology(size)

        nodes = data["nodes"]
        source = data["source"]
        target = data["destination"]

        path, cost = shortest_path_dijkstra(
            nodes, edges, source, target
        )

        assert path is not None

        if "expected_shortest_cost" in data:
            assert cost == data["expected_shortest_cost"]

        if "expected_shortest_path" in data:
            assert path == data["expected_shortest_path"]

        _, _, runtime = measure_dijkstra(
            nodes, edges, source, target,
            repeats=REPEATS,
        )

        info = scaling_info(nodes, edges)

        row = {
            "experiment": "A_topology_size",
            "topology": data["name"],
            "method": "dijkstra_reference",
            "seed": None,
            "density": len(edges) / (len(nodes) * (len(nodes) - 1)),
            **info,
            "optimal_cost": cost,
            "best_feasible_cost": cost,
            "optimality_gap": 0.0,
            "runtime_seconds": runtime,
            "runtime_repeats": REPEATS,
        }

        results.append(row)

        print(f"\n[PASS] {data['name']}")
        print(f"Nodes: {info['nodes']}")
        print(f"Edges: {info['edges']}")
        print(f"Variables: {info['variables']}")
        print(f"Qubits: {info['qubits']}")
        print(f"State-space size: {info['state_space_size']}")
        print(f"Shortest path: {' -> '.join(path)}")
        print(f"Shortest cost: {cost}")
        print(f"Avg runtime: {runtime:.9f} seconds")

    output = save_results_csv(
        results, OUTPUT_FILE
    )

    assert len(results) == 3
    assert output.is_file()

    print()
    print("[PASS] CSV created:", output)
    print("ALL TOPOLOGY SIZE EXPERIMENTS PASSED!")


if __name__ == "__main__":
    run_experiment()
