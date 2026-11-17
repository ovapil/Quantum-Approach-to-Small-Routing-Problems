import json
import sys
import time
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
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
    p=1,
    penalty=3.0,
    shots=2048,
    seed=42,
    maxiter=150,
):
    """
    Chạy một QAOA experiment trên topology 4.

    Pipeline:

        topology
        -> Dijkstra
        -> QUBO
        -> Ising Hamiltonian
        -> QAOA
        -> counts
        -> metrics
    """

    # ========================================================
    # 1. TOPOLOGY
    # ========================================================

    graph = create_test_topology()

    source = "A"
    target = "D"

    mapping = create_edge_mapping(
        graph
    )

    metric_edges = (
        graph_to_metric_edges(
            graph
        )
    )

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

    match_optimal = (
        best_cost is not None
        and abs(
            best_cost
            - dijkstra_cost
        ) < 1e-9
    )

    # ========================================================
    # 8. STANDARDIZED RESULT ROW
    # ========================================================

    row = {
        "experiment":
            "single_run",

        "topology":
            "topology_4",

        "nodes":
            graph.number_of_nodes(),

        "edges":
            graph.number_of_edges(),

        "variables":
            len(mapping),

        "qubits":
            cost_operator.num_qubits,

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
        penalty=3.0,
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