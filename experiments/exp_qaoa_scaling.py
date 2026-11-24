import sys

from pathlib import Path
from itertools import product

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
)

SRC_DIR = (
    PROJECT_ROOT
    / "src"
)

EXPERIMENT_DIR = (
    PROJECT_ROOT
    / "experiments"
)


sys.path.insert(
    0,
    str(SRC_DIR)
)

sys.path.insert(
    0,
    str(EXPERIMENT_DIR)
)


# ============================================================
# IMPORT PROJECT MODULES
# ============================================================

from experiment_runner import (
    run_single_experiment,
    save_experiment_csv,
)


# ============================================================
# EXPERIMENT CONFIGURATION
# ============================================================

TOPOLOGIES = [
    "topology_4",
    "topology_6",
    "topology_8",
    "topology_10",
]


QAOA_DEPTH = 1

SHOTS = 2048

SEEDS = list(range(10))
MAXITER = None
PENALTY_K = 0.8                        # 1.5 = cấu hình gốc
OUTPUT_NAME = "qaoa_scaling_k08.csv"


# ============================================================
# MAIN EXPERIMENT
# ============================================================

def main():

    print(
        "=" * 75
    )

    print(
        "WEEK 6 - QAOA SCALABILITY EXPERIMENT"
    )

    print(
        "=" * 75
    )

    print(
        f"Fixed depth p: {QAOA_DEPTH}"
    )

    print(
        f"Fixed shots: {SHOTS}"
    )

    print(
        f"Seeds: {SEEDS}"
    )

    print(
        "Maxiter: 300 * p (x restarts)"
    )

    print(
        f"Penalty strategy: A = {PENALTY_K} * c_UB / 2 "
        "(topology_4 giữ k = 1.5)"
    )

    print(
        "=" * 75
    )

    results = []

    # ========================================================
    # RUN EACH TOPOLOGY
    # ========================================================

    for topology_name, seed in product(TOPOLOGIES, SEEDS):

        print()

        print(
            "=" * 75
        )

        print(
            f"RUNNING {topology_name}"
        )

        print(
            "=" * 75
        )

        try:

            # ------------------------------------------------
            # Run one QAOA experiment
            # ------------------------------------------------

            result = (
                run_single_experiment(
                    topology_name=topology_name,
                    p=QAOA_DEPTH,
                    penalty=None,
                    penalty_k=(
                        1.5 if topology_name == "topology_4" else PENALTY_K
                    ),
                    shots=SHOTS,
                    seed=seed,
                    maxiter=MAXITER,
                )
            )

            # Đổi tên experiment để phân biệt
            # với các experiment của Week 5.
            result[
                "experiment"
            ] = "qaoa_scaling"

            results.append(
                result
            )

            # ------------------------------------------------
            # Print structural information
            # ------------------------------------------------

            print()

            print(
                "[STRUCTURE]"
            )

            print(
                "Topology:",
                result[
                    "topology"
                ]
            )

            print(
                "Nodes:",
                result[
                    "nodes"
                ]
            )

            print(
                "Edges:",
                result[
                    "edges"
                ]
            )

            print(
                "Variables:",
                result[
                    "variables"
                ]
            )

            print(
                "Qubits:",
                result[
                    "qubits"
                ]
            )

            print(
                "State-space size:",
                result[
                    "state_space_size"
                ]
            )

            print(
                "Estimated raw statevector memory:",
                (
                    f"{result['statevector_memory_mib']:.6f}"
                    " MiB"
                )
            )

            # ------------------------------------------------
            # Print reference solution
            # ------------------------------------------------

            print()

            print(
                "[DIJKSTRA REFERENCE]"
            )

            print(
                "Path:",
                result[
                    "dijkstra_path"
                ]
            )

            print(
                "Cost:",
                result[
                    "dijkstra_cost"
                ]
            )

            # ------------------------------------------------
            # Print QAOA configuration
            # ------------------------------------------------

            print()

            print(
                "[QAOA CONFIGURATION]"
            )

            print(
                "Penalty A:",
                result[
                    "penalty_A"
                ]
            )

            print(
                "Depth p:",
                result[
                    "p"
                ]
            )

            print(
                "Shots:",
                result[
                    "shots"
                ]
            )

            print(
                "Seed:",
                result[
                    "seed"
                ]
            )

            # ------------------------------------------------
            # Print QAOA quality metrics
            # ------------------------------------------------

            print()

            print(
                "[QAOA RESULT]"
            )

            print(
                "Feasibility rate:",
                (
                    f"{result['feasibility_rate']:.6f}"
                )
            )

            print(
                "Optimal solution probability:",
                (
                    f"{result['optimal_solution_probability']:.6f}"
                )
            )

            print(
                "Best feasible cost:",
                result[
                    "best_feasible_cost"
                ]
            )

            print(
                "Mean feasible cost:",
                result[
                    "mean_feasible_cost"
                ]
            )

            print(
                "Optimality gap:",
                result[
                    "optimality_gap"
                ]
            )

            print(
                "Match Dijkstra optimum:",
                result[
                    "match_optimal"
                ]
            )

            # ------------------------------------------------
            # Print optimizer information
            # ------------------------------------------------

            print()

            print(
                "[OPTIMIZER]"
            )

            print(
                "Optimization success:",
                result[
                    "optimization_success"
                ]
            )

            print(
                "Optimization message:",
                result.get(
                    "optimization_message",
                    ""
                )
            )

            print(
                "Optimizer evaluations:",
                result[
                    "optimizer_evaluations"
                ]
            )

            print(
                "Expectation value:",
                result[
                    "expectation_value"
                ]
            )

            # ------------------------------------------------
            # Print runtime
            # ------------------------------------------------

            print()

            print(
                "[RUNTIME]"
            )

            print(
                "QAOA runtime:",
                (
                    f"{result['runtime_seconds']:.6f}"
                    " seconds"
                )
            )

            print()

            print(
                f"[PASS] {topology_name} completed"
            )

        except Exception as error:

            print()

            print(
                f"[FAIL] {topology_name}"
            )

            print(
                "Error type:",
                type(
                    error
                ).__name__
            )

            print(
                "Message:",
                str(
                    error
                )
            )

            # Không dừng toàn bộ experiment.
            # Nếu topology lớn gặp lỗi,
            # vẫn giữ kết quả của topology nhỏ.
            continue

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    print()

    print(
        "=" * 75
    )

    print(
        "QAOA SCALABILITY SUMMARY"
    )

    print(
        "=" * 75
    )

    if not results:

        print(
            "[FAIL] No QAOA scaling runs completed."
        )

        return

    output_path = (
        PROJECT_ROOT
        / "experiments"
        / "results"
        / OUTPUT_NAME
    )

    save_experiment_csv(
        results,
        output_path
    )

    # ========================================================
    # PRINT COMPACT SUMMARY
    # ========================================================

    for result in results:

        print(
            f"{result['topology']}"
            f" | qubits={result['qubits']}"
            f" | states={result['state_space_size']}"
            f" | runtime={result['runtime_seconds']:.6f}s"
            f" | feasibility={result['feasibility_rate']:.4f}"
            f" | optimal_prob="
            f"{result['optimal_solution_probability']:.4f}"
            f" | seed={result['seed']}"
            f" | gain={result['optimal_prob_gain']:.2f}"
            f" | top1={result['match_optimal']}"
            f" | optimizer_success="
            f"{result['optimization_success']}"
        )

    print()

    print(
        f"[PASS] CSV created: "
        f"{output_path}"
    )

    print(
        f"Successful instances: "
         f"{len(results)}/{len(TOPOLOGIES) * len(SEEDS)}"
    )

    print(
        "=" * 75
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()