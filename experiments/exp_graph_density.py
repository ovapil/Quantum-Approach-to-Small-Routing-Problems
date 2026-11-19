
import json
import random
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


DATA_FILE = ROOT / "data" / "topology_6.json"

OUTPUT_FILE = (
    ROOT / "experiments" / "results"
    / "graph_density.csv"
)

SEED = 42
REPEATS = 1000

# Number of edges in the DAG
EDGE_COUNTS = [7, 10, 13, 15]


def load_base_graph():
    with DATA_FILE.open(
        "r", encoding="utf-8"
    ) as file:
        data = json.load(file)

    assert data["directed"] is True

    edges = [
        (e["source"], e["target"], e["weight"])
        for e in data["edges"]
    ]

    return data, edges


def create_density_variants(data, base_edges):
    nodes = data["nodes"]
    n = len(nodes)

    # Maximum edges in a forward-only DAG
    max_edges = n * (n - 1) // 2

    assert all(
        len(base_edges) <= m <= max_edges
        for m in EDGE_COUNTS
    )

    all_pairs = [
        (nodes[i], nodes[j])
        for i in range(n)
        for j in range(i + 1, n)
    ]

    base_pairs = {
        (u, v) for u, v, _ in base_edges
    }

    # The base graph must already follow DAG order
    assert base_pairs <= set(all_pairs)

    missing_pairs = [
        pair for pair in all_pairs
        if pair not in base_pairs
    ]

    rng = random.Random(SEED)
    rng.shuffle(missing_pairs)

    added_edges = [
        (u, v, rng.randint(1, 9))
        for u, v in missing_pairs
    ]

    variants = []

    for target_edges in EDGE_COUNTS:
        extra_count = target_edges - len(base_edges)

        edges = (
            list(base_edges)
            + added_edges[:extra_count]
        )

        assert len(edges) == target_edges

        variants.append(edges)

    return variants, max_edges


def run_experiment():
    data, base_edges = load_base_graph()

    nodes = data["nodes"]
    source = data["source"]
    target = data["destination"]

    variants, max_edges = create_density_variants(
        data, base_edges
    )

    results = []

    print("=" * 65)
    print("WEEK 5 - EXPERIMENT E: GRAPH DENSITY")
    print("=" * 65)

    for index, edges in enumerate(variants, start=1):
        path, cost = shortest_path_dijkstra(
            nodes, edges, source, target
        )

        assert path is not None

        _, _, runtime = measure_dijkstra(
            nodes, edges, source, target,
            repeats=REPEATS,
        )

        info = scaling_info(nodes, edges)

        # Density relative to maximum forward-only DAG
        density = len(edges) / max_edges

        row = {
            "experiment": "E_graph_density",
            "topology": f"density_level_{index}",
            "method": "dijkstra_reference",
            "seed": SEED,
            "density": density,
            **info,
            "best_feasible_cost": cost,
            "optimal_cost": cost,
            "optimality_gap": 0.0,
            "runtime_seconds": runtime,
            "runtime_repeats": REPEATS,
        }

        results.append(row)

        print(f"\n[PASS] Density level {index}")
        print(f"Nodes: {info['nodes']}")
        print(f"Edges: {info['edges']}")
        print(f"Density (DAG): {density:.4f}")
        print(f"Qubits: {info['qubits']}")
        print(f"State-space size: {info['state_space_size']}")
        print(f"Shortest path: {' -> '.join(path)}")
        print(f"Shortest cost: {cost}")
        print(f"Avg runtime: {runtime:.9f} seconds")

    output = save_results_csv(
        results, OUTPUT_FILE
    )

    assert len(results) == len(EDGE_COUNTS)
    assert output.is_file()

    print()
    print("[PASS] CSV created:", output)
    print("ALL GRAPH DENSITY EXPERIMENTS PASSED!")


if __name__ == "__main__":
    run_experiment()
