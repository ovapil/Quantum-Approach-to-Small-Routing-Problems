
import json
from pathlib import Path

# Project root: parent of Tests/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_EDGE_COUNTS = {
    4: 4,
    6: 7,
    8: 11,
    10: 15,
}


def analyze_topology(node_count):
    file_path = (
        PROJECT_ROOT
        / "data"
        / f"topology_{node_count}.json"
    )

    with open(file_path, "r", encoding="utf-8") as f:
        topology = json.load(f)

    nodes = topology["nodes"]
    edges = topology["edges"]

    num_nodes = len(nodes)
    num_edges = len(edges)

    # One binary variable per directed edge
    num_variables = num_edges

    # Standard direct encoding: 1 qubit per variable
    num_qubits = num_variables

    # Number of computational basis states
    num_states = 2 ** num_qubits

    assert num_nodes == node_count
    assert num_edges == EXPECTED_EDGE_COUNTS[node_count]

    return num_nodes, num_edges, num_qubits, num_states


def main():
    print("=" * 65)
    print("QUBIT SCALING VALIDATION")
    print("=" * 65)

    print(
        f"{'Topology':<14}"
        f"{'Nodes':<10}"
        f"{'Edges':<10}"
        f"{'Qubits':<10}"
        f"{'States':<10}"
    )
    print("-" * 65)

    for node_count in [4, 6, 8, 10]:
        nodes, edges, qubits, states = (
            analyze_topology(node_count)
        )

        print(
            f"{'topology_' + str(node_count):<14}"
            f"{nodes:<10}"
            f"{edges:<10}"
            f"{qubits:<10}"
            f"{states:<10}"
        )

    print()
    print("[PASS] Qubit scaling verified for all topologies!")


if __name__ == "__main__":
    main()
