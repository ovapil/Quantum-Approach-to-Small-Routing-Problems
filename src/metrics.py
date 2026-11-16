
import csv
import heapq
from collections import defaultdict
from math import isclose
from pathlib import Path
from time import perf_counter


# =====================================================
# WEEK 5 - METRICS AND COMMON EXPERIMENT UTILITIES
# =====================================================

CSV_FIELDS = [
    "experiment",
    "topology",
    "method",
    "seed",
    "nodes",
    "edges",
    "density",
    "variables",
    "qubits",
    "state_space_size",
    "total_shots",
    "feasible_shots",
    "optimal_shots",
    "feasibility_rate",
    "optimal_solution_probability",
    "best_feasible_cost",
    "mean_feasible_cost",
    "optimal_cost",
    "optimality_gap",
    "runtime_seconds",
    "runtime_repeats",
]


def to_project_bits(bitstring, bit_order="qiskit"):
    bits = bitstring.replace(" ", "")

    if bit_order not in ("qiskit", "project"):
        raise ValueError("Unsupported bit order")

    if not bits or set(bits) - {"0", "1"}:
        raise ValueError("Invalid bitstring")

    return bits[::-1] if bit_order == "qiskit" else bits


def decode_selected_path(bits, edges, source, target):
    if len(bits) != len(edges):
        raise ValueError("Bitstring length mismatch")

    if not bits or set(bits) - {"0", "1"}:
        raise ValueError("Invalid bits")

    selected = [
        (u, v, w)
        for bit, (u, v, w) in zip(bits, edges)
        if bit == "1"
    ]

    cost = sum(w for _, _, w in selected)

    if source == target:
        return False, None, cost

    outgoing = defaultdict(list)
    incoming = defaultdict(list)

    for u, v, _ in selected:
        outgoing[u].append(v)
        incoming[v].append(u)

    vertices = {source, target}
    for u, v, _ in edges:
        vertices.update((u, v))

    for node in vertices:
        indeg = len(incoming[node])
        outdeg = len(outgoing[node])

        if node == source:
            expected = (0, 1)
        elif node == target:
            expected = (1, 0)
        else:
            if (indeg, outdeg) not in ((0, 0), (1, 1)):
                return False, None, cost
            continue

        if (indeg, outdeg) != expected:
            return False, None, cost

    path = [source]
    visited = {source}
    current = source

    while current != target:
        if len(outgoing[current]) != 1:
            return False, None, cost

        next_node = outgoing[current][0]

        if next_node in visited:
            return False, None, cost

        visited.add(next_node)
        path.append(next_node)
        current = next_node

    if len(path) - 1 != len(selected):
        return False, None, cost

    return True, path, cost


def shortest_path_dijkstra(nodes, edges, source, target):
    graph = {node: [] for node in nodes}

    for u, v, weight in edges:
        if weight < 0:
            raise ValueError("Dijkstra requires nonnegative weights")
        graph[u].append((v, weight))

    distances = {source: 0}
    previous = {}
    queue = [(0, source)]

    while queue:
        distance, current = heapq.heappop(queue)

        if distance != distances[current]:
            continue

        if current == target:
            break

        for neighbor, weight in graph[current]:
            new_distance = distance + weight

            if new_distance < distances.get(
                neighbor, float("inf")
            ):
                distances[neighbor] = new_distance
                previous[neighbor] = current
                heapq.heappush(
                    queue, (new_distance, neighbor)
                )

    if target not in distances:
        return None, None

    path = [target]

    while path[-1] != source:
        path.append(previous[path[-1]])

    path.reverse()
    return path, distances[target]


def measure_dijkstra(
    nodes, edges, source, target, repeats=1000
):
    if repeats <= 0:
        raise ValueError("repeats must be positive")

    # Warm-up; not included in timing
    shortest_path_dijkstra(nodes, edges, source, target)

    start = perf_counter()

    for _ in range(repeats):
        result = shortest_path_dijkstra(
            nodes, edges, source, target
        )

    runtime = (perf_counter() - start) / repeats

    path, cost = result
    return path, cost, runtime


def scaling_info(nodes, edges):
    n = len(nodes)
    m = len(edges)

    return {
        "nodes": n,
        "edges": m,
        "variables": m,
        "qubits": m,
        "state_space_size": 2 ** m,
    }


def calculate_metrics(
    counts,
    edges,
    source,
    target,
    optimal_cost,
    bit_order="qiskit",
    runtime_seconds=None,
):
    if not edges:
        raise ValueError("Edges cannot be empty")

    if optimal_cost <= 0:
        raise ValueError("optimal_cost must be positive")

    if runtime_seconds is not None and runtime_seconds < 0:
        raise ValueError("Invalid runtime")

    total_shots = 0
    feasible_shots = 0
    optimal_shots = 0
    weighted_cost = 0.0
    best_cost = None

    for bitstring, shots in counts.items():
        if type(shots) is not int or shots < 0:
            raise ValueError("Invalid shot count")

        bits = to_project_bits(bitstring, bit_order)

        valid, _, cost = decode_selected_path(
            bits, edges, source, target
        )

        total_shots += shots

        if valid and shots > 0:
            feasible_shots += shots
            weighted_cost += cost * shots

            best_cost = (
                cost if best_cost is None
                else min(best_cost, cost)
            )

            if isclose(
                cost, optimal_cost,
                rel_tol=1e-9,
                abs_tol=1e-9,
            ):
                optimal_shots += shots

    if total_shots == 0:
        raise ValueError("Total shots must be positive")

    mean_cost = (
        weighted_cost / feasible_shots
        if feasible_shots else None
    )

    gap = (
        (best_cost - optimal_cost) / optimal_cost
        if best_cost is not None else None
    )

    vertices = {source, target}
    for u, v, _ in edges:
        vertices.update((u, v))

    result = scaling_info(vertices, edges)

    result.update({
        "total_shots": total_shots,
        "feasible_shots": feasible_shots,
        "optimal_shots": optimal_shots,
        "feasibility_rate":
            feasible_shots / total_shots,
        "optimal_solution_probability":
            optimal_shots / total_shots,
        "best_feasible_cost": best_cost,
        "mean_feasible_cost": mean_cost,
        "optimal_cost": optimal_cost,
        "optimality_gap": gap,
        "runtime_seconds": runtime_seconds,
    })

    return result


def save_results_csv(rows, output_path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(rows, dict):
        rows = [rows]

    with path.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CSV_FIELDS,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)

    return path
