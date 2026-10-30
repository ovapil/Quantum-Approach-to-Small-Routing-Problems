
import json
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def validate_topology(n):
    file_path = DATA_DIR / f"topology_{n}.json"

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["directed"] is True
    assert len(data["nodes"]) == n
    assert len(set(data["nodes"])) == n

    graph = nx.DiGraph()
    graph.add_nodes_from(data["nodes"])

    for edge in data["edges"]:
        u = edge["source"]
        v = edge["target"]
        weight = edge["weight"]

        assert u in graph and v in graph
        assert isinstance(weight, (int, float))
        assert weight > 0
        assert not graph.has_edge(u, v)

        graph.add_edge(u, v, weight=weight)

    source = data["source"]
    target = data["destination"]

    assert source in graph and target in graph
    assert source != target

    expected_path = data["expected_shortest_path"]
    expected_cost = data["expected_shortest_cost"]

    assert expected_path[0] == source
    assert expected_path[-1] == target
    assert len(expected_path) == len(set(expected_path))

    manual_cost = 0

    for u, v in zip(expected_path, expected_path[1:]):
        assert graph.has_edge(u, v)
        manual_cost += graph[u][v]["weight"]

    actual_path = nx.dijkstra_path(
        graph, source, target, weight="weight"
    )

    actual_cost = nx.dijkstra_path_length(
        graph, source, target, weight="weight"
    )

    assert manual_cost == expected_cost
    assert actual_cost == expected_cost

    print(f"[PASS] Topology {n} nodes")
    print(f"Expected: {' -> '.join(expected_path)}")
    print(f"Dijkstra: {' -> '.join(actual_path)}")
    print(f"Cost: {actual_cost}")
    print()


if __name__ == "__main__":
    for n in (4, 6, 8, 10):
        validate_topology(n)

    print("All topology validations passed!")
