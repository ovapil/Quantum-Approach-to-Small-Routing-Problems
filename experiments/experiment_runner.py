import json
import sys
import time
import csv
import networkx as nx
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

def load_topology_graph(topology_name):
    """
    Load topology từ data/topology_X.json
    và chuyển thành NetworkX graph.
    """

    file_path = (
        PROJECT_ROOT
        / "data"
        / f"{topology_name}.json"
    )

    with file_path.open(
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(file)

    directed = data.get(
        "directed",
        True
    )

    graph = (
        nx.DiGraph()
        if directed
        else nx.Graph()
    )

    nodes = data["nodes"]

    for node in nodes:
        if isinstance(node, dict):
            node_id = (
                node.get("id")
                or node.get("name")
            )
            graph.add_node(node_id)
        else:
            graph.add_node(node)

    for edge in data["edges"]:

        if isinstance(edge, dict):

            source = (
                edge.get("source")
                or edge.get("from")
                or edge.get("u")
            )

            target = (
                edge.get("target")
                or edge.get("to")
                or edge.get("v")
            )

            weight = edge["weight"]

        else:

            source = edge[0]
            target = edge[1]
            weight = edge[2]

        graph.add_edge(
            source,
            target,
            weight=weight
        )

    source_node = (
        data.get("source")
        or data.get("start")
    )

    target_node = (
        data.get("target")
        or data.get("destination")
        or data.get("end")
    )

    if source_node is None:
        raise ValueError(
            f"No source found in {file_path}"
        )

    if target_node is None:
        raise ValueError(
            f"No target found in {file_path}"
        )

    return (
        graph,
        source_node,
        target_node
    )

def path_upper_bound(graph, source, target):
    """Chi phí 1 path bất kỳ (BFS theo số hop, KHÔNG dùng trọng số) -> c_UB >= c*."""
    hop_path = nx.shortest_path(graph, source, target)
    return sum(
        graph[u][v]["weight"] for u, v in zip(hop_path, hop_path[1:])
    )


def bounded_penalty(graph, source, target, k=1.5):
    """
    Nghiệm không khả thi lệch luồng ở >= 2 node => penalty >= 2A.
    Ground state khả thi khi 2A > c*, tức A > c*/2.
    Dùng A = k * c_UB / 2 (k > 1 để có biên an toàn).
    """
    return k * path_upper_bound(graph, source, target) / 2

SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(
    0,
    str(SRC_DIR)
)


from topology import create_test_topology
from binary_encoding import create_edge_mapping
from dijkstra_solver import solve_dijkstra
from qubo_builder import build_qubo

from qaoa_solver import (
    qubo_to_cost_operator,
    run_qaoa,
)

from metrics import calculate_metrics


def graph_to_metric_edges(graph):
    """
    metrics.py của Pien cần edges dạng:

        (source, destination, weight)
    """

    return [
        (
            source,
            destination,
            data["weight"],
        )
        for source, destination, data
        in graph.edges(data=True)
    ]


def run_single_experiment(
    topology_name="topology_6",
    p=1,
    penalty=None,
    penalty_k=1.5,
    shots=2048,
    seed=42,
    maxiter=None,
    restarts=3,
):
    """
    Chạy một QAOA experiment trên topology được chọn.

    Pipeline:

        topology
        -> Dijkstra
        -> QUBO
        -> Ising Hamiltonian
        -> QAOA
        -> counts
        -> metrics

    Parameters
    ----------
    topology_name : str
        Tên topology, ví dụ:
        topology_4, topology_6,
        topology_8, topology_10.

    penalty : float or None
        Nếu penalty=None, sử dụng
        conservative_penalty(graph).
    """

    # ========================================================
    # 1. TOPOLOGY
    # ========================================================

    graph, source, target = (
        load_topology_graph(
            topology_name
        )
    )

    # Nếu không truyền penalty,
    # tự chọn penalty bảo thủ
    # theo topology hiện tại.
    if penalty is None:
        penalty = bounded_penalty(graph, source, target, k=penalty_k)
    else:
        penalty_k = None

    mapping = create_edge_mapping(
        graph
    )

    metric_edges = [
        (*mapping[i]["edge"], mapping[i]["weight"])
        for i in range(len(mapping))
    ]

    # ========================================================
    # 2. DIJKSTRA REFERENCE
    # ========================================================

    (
        dijkstra_path,
        dijkstra_cost,
    ) = solve_dijkstra(
        graph,
        source,
        target,
    )

    # ========================================================
    # 3. BUILD QUBO
    # ========================================================

    qubo = build_qubo(
        graph,
        mapping,
        source=source,
        destination=target,
        penalty=penalty,
    )

    # ========================================================
    # 4. QUBO -> COST HAMILTONIAN
    # ========================================================

    (
        cost_operator,
        offset,
        h,
        J,
    ) = qubo_to_cost_operator(
        qubo,
        num_qubits=len(mapping),
    )

    # ========================================================
    # 5. RUN QAOA
    # ========================================================

    start_time = time.perf_counter()

    qaoa_result = run_qaoa(
        cost_operator,
        offset=offset,
        reps=p,
        shots=shots,
        seed=seed,
        maxiter=maxiter,
    )

    end_time = time.perf_counter()

    runtime_seconds = (
        end_time
        - start_time
    )

    # ========================================================
    # 6. CALCULATE METRICS
    # ========================================================

    metric_result = calculate_metrics(
        counts=qaoa_result["counts"],
        edges=metric_edges,
        source=source,
        target=target,
        optimal_cost=dijkstra_cost,
        bit_order="qiskit",
        runtime_seconds=runtime_seconds,
    )

    # ========================================================
    # 7. MATCH WITH DIJKSTRA
    # ========================================================

    best_cost = metric_result[
        "best_feasible_cost"
    ]

    found_in_samples = (
        best_cost is not None
        and abs(best_cost - dijkstra_cost) < 1e-9
    )
    match_optimal = metric_result["top1_match"]

    # ========================================================
    # 8. SCALABILITY INFORMATION
    # ========================================================

    num_qubits = (
        cost_operator.num_qubits
    )

    state_space_size = (
        2 ** num_qubits
    )

    # Một complex128 amplitude
    # được ước lượng khoảng 16 bytes.
    statevector_memory_mib = (
        state_space_size
        * 16
        / (1024 ** 2)
    )

    # ========================================================
    # 9. STANDARDIZED RESULT ROW
    # ========================================================

    row = {
        "experiment":
            "single_run",

        "topology":
            topology_name,

        "nodes":
            graph.number_of_nodes(),

        "edges":
            graph.number_of_edges(),

        "variables":
            len(mapping),

        "qubits":
            num_qubits,

        "state_space_size":
            state_space_size,

        "statevector_memory_mib":
            statevector_memory_mib,

        "penalty_A":
            penalty,

        "p":
            p,

        "shots":
            shots,

        "seed":
            seed,

        "dijkstra_path":
            "->".join(
                dijkstra_path
            ),

        "dijkstra_cost":
            dijkstra_cost,

        "feasibility_rate":
            metric_result[
                "feasibility_rate"
            ],

        "optimal_solution_probability":
            metric_result[
                "optimal_solution_probability"
            ],

        "best_feasible_cost":
            metric_result[
                "best_feasible_cost"
            ],

        "mean_feasible_cost":
            metric_result[
                "mean_feasible_cost"
            ],

        "optimality_gap":
            metric_result[
                "optimality_gap"
            ],

        "match_optimal":
            match_optimal,
        "optimal_found_in_samples": found_in_samples,
        "top1_cost": metric_result["top1_cost"],
        "random_feasible_prob": metric_result["random_feasible_prob"],
        "random_optimal_prob": metric_result["random_optimal_prob"],
        "optimal_prob_gain": metric_result["optimal_prob_gain"],
        "approximation_ratio": metric_result["approximation_ratio"],
        "penalty_k": penalty_k,
        "restarts": restarts,
        "expectation_value":
            qaoa_result[
                "expectation_value"
            ],

        "optimizer_evaluations":
            len(
                qaoa_result[
                    "history"
                ]
            ),

        "runtime_seconds":
            runtime_seconds,

        "optimization_success":
            qaoa_result[
                "success"
            ],

        "optimization_message":
            qaoa_result.get(
                "message",
                ""
            ),

        "counts":
            json.dumps(
                qaoa_result[
                    "counts"
                ],
                sort_keys=True,
            ),
    }

    return row


if __name__ == "__main__":

    result = run_single_experiment(
        p=1,
        shots=2048,
        seed=42,
    )

    print(
        "=" * 70
    )

    print(
        "WEEK 5 - QAOA EXPERIMENT RUNNER"
    )

    print(
        "=" * 70
    )

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )

    print(
        "\n[PASS] QAOA experiment "
        "and metrics completed"
    )

def save_experiment_csv(
    rows,
    output_path
):
    """
    Lưu toàn bộ field của QAOA experiment.

    Không dùng schema cố định của metrics.py,
    vì experiment cần thêm p, penalty_A,
    shots, expectation value, v.v.
    """

    if not rows:
        raise ValueError(
            "No experiment rows to save"
        )

    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if isinstance(rows, dict):
        rows = [rows]

    fieldnames = list(
        rows[0].keys()
    )

    with path.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    return path