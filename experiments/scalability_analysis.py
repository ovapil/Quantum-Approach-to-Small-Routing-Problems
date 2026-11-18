
import csv
import json
from pathlib import Path


# =====================================================
# WEEK 6 - GĐ12: SCALABILITY ANALYSIS
# =====================================================

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULT_DIR = ROOT / "experiments" / "results"

SIZES = [4, 6, 8, 10]
BYTES_PER_COMPLEX128 = 16

RESULT_DIR.mkdir(parents=True, exist_ok=True)


def read_topology(size):
    path = DATA_DIR / f"topology_{size}.json"

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["directed"] is True
    assert len(data["nodes"]) == size
    assert len(set(data["nodes"])) == size

    node_set = set(data["nodes"])
    assert data["source"] in node_set
    assert data["destination"] in node_set

    for edge in data["edges"]:
        assert edge["source"] in node_set
        assert edge["target"] in node_set
        assert edge["weight"] >= 0

    return data


def save_csv(rows, filename):
    assert rows, "No results to save"

    output = RESULT_DIR / filename

    with output.open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"[PASS] CSV created: {output}")


def analyze_topology():
    results = []

    print("=" * 65)
    print("GĐ12 - TOPOLOGY SCALABILITY")
    print("=" * 65)

    for size in SIZES:
        data = read_topology(size)

        nodes = len(data["nodes"])
        edges = len(data["edges"])

        variables = edges
        qubits = variables
        states = 2 ** qubits

        memory_bytes = states * BYTES_PER_COMPLEX128
        memory_mib = memory_bytes / (1024 ** 2)
        memory_gib = memory_bytes / (1024 ** 3)

        # Directed graph without self-loops
        density = edges / (nodes * (nodes - 1))

        row = {
            "topology": data["name"],
            "nodes": nodes,
            "edges": edges,
            "variables": variables,
            "qubits": qubits,
            "state_space_size": states,
            "statevector_memory_bytes": memory_bytes,
            "statevector_memory_mib": memory_mib,
            "statevector_memory_gib": memory_gib,
            "directed_density": density,
        }

        assert qubits == edges
        assert states == 2 ** qubits
        assert memory_bytes == states * 16

        results.append(row)

        print(f"\n[PASS] {data['name']}")
        print(f"Nodes: {nodes}")
        print(f"Edges: {edges}")
        print(f"Variables: {variables}")
        print(f"Qubits: {qubits}")
        print(f"State-space size: {states}")
        print(f"Memory: {memory_mib:.6f} MiB")
        print(f"Directed density: {density:.4f}")

    save_csv(results, "scalability_analysis.csv")
    return results


def analyze_density():
    input_file = RESULT_DIR / "graph_density.csv"

    if not input_file.is_file():
        raise FileNotFoundError(
            "Run experiments/exp_graph_density.py first"
        )

    with input_file.open(
        "r", newline="", encoding="utf-8"
    ) as f:
        source_rows = list(csv.DictReader(f))

    assert source_rows, "Graph density CSV is empty"

    results = []

    print()
    print("=" * 65)
    print("GĐ12 - GRAPH DENSITY SCALABILITY")
    print("=" * 65)

    for item in source_rows:
        nodes = int(item["nodes"])
        edges = int(item["edges"])

        variables = edges
        qubits = edges
        states = 2 ** qubits

        # Density relative to forward-only DAG
        max_dag_edges = nodes * (nodes - 1) // 2
        density = edges / max_dag_edges

        memory_mib = (
            states * BYTES_PER_COMPLEX128
            / (1024 ** 2)
        )

        row = {
            "topology": item["topology"],
            "nodes": nodes,
            "edges": edges,
            "variables": variables,
            "qubits": qubits,
            "state_space_size": states,
            "statevector_memory_mib": memory_mib,
            "dag_density": density,
        }

        assert int(item["qubits"]) == qubits
        assert int(item["state_space_size"]) == states

        results.append(row)

        print(
            f"[PASS] {item['topology']} | "
            f"edges={edges} | "
            f"qubits={qubits} | "
            f"states={states} | "
            f"memory={memory_mib:.6f} MiB"
        )

    save_csv(results, "density_scalability.csv")
    return results


def main():
    topology = analyze_topology()
    density = analyze_density()

    assert len(topology) == 4
    assert len(density) == 4

    print()
    print("=" * 65)
    print("ALL SCALABILITY VALIDATIONS PASSED!")
    print("=" * 65)


if __name__ == "__main__":
    main()
