import csv
import json

from pathlib import Path
from statistics import mean, stdev

import matplotlib.pyplot as plt
import networkx as nx


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESULTS_DIR = (
    PROJECT_ROOT
    / "experiments"
    / "results"
)

FIGURES_DIR = (
    PROJECT_ROOT
    / "experiments"
    / "figures"
)

FIGURES_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# FILE PATHS
# ============================================================

DEPTH_FILE = (
    RESULTS_DIR
    / "qaoa_depth.csv"
)

PENALTY_FILE = (
    RESULTS_DIR
    / "qaoa_penalty.csv"
)

SCALING_FILE = (
    RESULTS_DIR
    / "qaoa_scaling.csv"
)


# ============================================================
# HELPERS
# ============================================================

def load_csv(path):
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def group_metric(
    rows,
    group_column,
    metric_column,
):
    """
    Group các run theo một parameter
    và tính mean + sample standard deviation.
    """

    grouped = {}

    for row in rows:

        key = float(
            row[group_column]
        )

        value = float(
            row[metric_column]
        )

        grouped.setdefault(
            key,
            [],
        ).append(value)

    result = []

    for key in sorted(grouped):

        values = grouped[key]

        avg = mean(values)

        std = (
            stdev(values)
            if len(values) > 1
            else 0.0
        )

        result.append(
            (
                key,
                avg,
                std,
            )
        )

    return result


def save_figure(
    output_name,
):
    output_path = (
        FIGURES_DIR
        / output_name
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"[PASS] Figure saved: "
        f"{output_path}"
    )


# ============================================================
# 1. DEPTH -> OPTIMAL PROBABILITY
# ============================================================

def plot_depth_optimal_probability(
    rows,
):
    data = group_metric(
        rows,
        "p",
        "optimal_solution_probability",
    )

    x = [
        int(item[0])
        for item in data
    ]

    means = [
        item[1] * 100
        for item in data
    ]

    errors = [
        item[2] * 100
        for item in data
    ]

    plt.figure(
        figsize=(7, 5)
    )

    plt.errorbar(
        x,
        means,
        yerr=errors,
        marker="o",
        capsize=5,
    )

    plt.xticks(x)

    plt.xlabel(
        "QAOA Depth p"
    )

    plt.ylabel(
        "Optimal Solution Probability (%)"
    )

    plt.title(
        "QAOA Depth vs Optimal Solution Probability"
    )

    plt.grid(
        alpha=0.3
    )

    plt.ylim(
        bottom=0
    )

    save_figure(
        "qaoa_depth_optimal_probability.png"
    )


# ============================================================
# 2. DEPTH -> FEASIBILITY RATE
# ============================================================

def plot_depth_feasibility(
    rows,
):
    data = group_metric(
        rows,
        "p",
        "feasibility_rate",
    )

    x = [
        int(item[0])
        for item in data
    ]

    means = [
        item[1] * 100
        for item in data
    ]

    errors = [
        item[2] * 100
        for item in data
    ]

    plt.figure(
        figsize=(7, 5)
    )

    plt.errorbar(
        x,
        means,
        yerr=errors,
        marker="o",
        capsize=5,
    )

    plt.xticks(x)

    plt.xlabel(
        "QAOA Depth p"
    )

    plt.ylabel(
        "Feasibility Rate (%)"
    )

    plt.title(
        "QAOA Depth vs Feasibility Rate"
    )

    plt.grid(
        alpha=0.3
    )

    plt.ylim(
        bottom=0
    )

    save_figure(
        "qaoa_depth_feasibility.png"
    )


# ============================================================
# 3. PENALTY -> OPTIMAL PROBABILITY
# ============================================================

def plot_penalty_optimal_probability(
    rows,
):
    data = group_metric(
        rows,
        "penalty_A",
        "optimal_solution_probability",
    )

    x = [
        item[0]
        for item in data
    ]

    means = [
        item[1] * 100
        for item in data
    ]

    errors = [
        item[2] * 100
        for item in data
    ]

    plt.figure(
        figsize=(7, 5)
    )

    plt.errorbar(
        x,
        means,
        yerr=errors,
        marker="o",
        capsize=5,
    )

    plt.xlabel(
        "Penalty A"
    )

    plt.ylabel(
        "Optimal Solution Probability (%)"
    )

    plt.title(
        "Penalty Strength vs Optimal Solution Probability"
    )

    plt.grid(
        alpha=0.3
    )

    plt.ylim(
        bottom=0
    )

    save_figure(
        "qaoa_penalty_optimal_probability.png"
    )


# ============================================================
# 4. PENALTY -> FEASIBILITY RATE
# ============================================================

def plot_penalty_feasibility(
    rows,
):
    data = group_metric(
        rows,
        "penalty_A",
        "feasibility_rate",
    )

    x = [
        item[0]
        for item in data
    ]

    means = [
        item[1] * 100
        for item in data
    ]

    errors = [
        item[2] * 100
        for item in data
    ]

    plt.figure(
        figsize=(7, 5)
    )

    plt.errorbar(
        x,
        means,
        yerr=errors,
        marker="o",
        capsize=5,
    )

    plt.xlabel(
        "Penalty A"
    )

    plt.ylabel(
        "Feasibility Rate (%)"
    )

    plt.title(
        "Penalty Strength vs Feasibility Rate"
    )

    plt.grid(
        alpha=0.3
    )

    plt.ylim(
        bottom=0
    )

    save_figure(
        "qaoa_penalty_feasibility.png"
    )


# ============================================================
# 5. QUBITS -> TOTAL QAOA RUNTIME
# ============================================================

def plot_scaling_runtime(
    rows,
):
    sorted_rows = sorted(
        rows,
        key=lambda row:
            int(row["qubits"]),
    )

    qubits = [
        int(row["qubits"])
        for row in sorted_rows
    ]

    runtimes = [
        float(
            row["runtime_seconds"]
        )
        for row in sorted_rows
    ]

    plt.figure(
        figsize=(7, 5)
    )

    plt.plot(
        qubits,
        runtimes,
        marker="o",
    )

    plt.xticks(
        qubits
    )

    plt.xlabel(
        "Number of Qubits"
    )

    plt.ylabel(
        "Total QAOA Runtime (seconds)"
    )

    plt.title(
        "QAOA Runtime vs Number of Qubits"
    )

    plt.grid(
        alpha=0.3
    )

    save_figure(
        "qaoa_scaling_runtime.png"
    )


# ============================================================
# 6. QUBITS -> RUNTIME PER OPTIMIZER EVALUATION
# ============================================================

def plot_runtime_per_evaluation(
    rows,
):
    sorted_rows = sorted(
        rows,
        key=lambda row:
            int(row["qubits"]),
    )

    qubits = []
    runtime_per_eval = []

    for row in sorted_rows:

        q = int(
            row["qubits"]
        )

        runtime = float(
            row["runtime_seconds"]
        )

        evaluations = int(
            row[
                "optimizer_evaluations"
            ]
        )

        per_eval = (
            runtime
            / evaluations
        )

        qubits.append(
            q
        )

        runtime_per_eval.append(
            per_eval * 1000
        )

    plt.figure(
        figsize=(7, 5)
    )

    plt.plot(
        qubits,
        runtime_per_eval,
        marker="o",
    )

    plt.xticks(
        qubits
    )

    plt.xlabel(
        "Number of Qubits"
    )

    plt.ylabel(
        "Runtime per Optimizer Evaluation (ms)"
    )

    plt.title(
        "Simulation Cost per Evaluation vs Number of Qubits"
    )

    plt.grid(
        alpha=0.3
    )

    save_figure(
        "qaoa_scaling_runtime_per_evaluation.png"
    )


# ============================================================
# 7. QUBITS -> SOLUTION QUALITY
# ============================================================

def plot_scaling_quality(
    rows,
):
    sorted_rows = sorted(
        rows,
        key=lambda row:
            int(row["qubits"]),
    )

    qubits = [
        int(row["qubits"])
        for row in sorted_rows
    ]

    feasibility = [
        float(
            row[
                "feasibility_rate"
            ]
        ) * 100
        for row in sorted_rows
    ]

    optimal_probability = [
        float(
            row[
                "optimal_solution_probability"
            ]
        ) * 100
        for row in sorted_rows
    ]

    plt.figure(
        figsize=(7, 5)
    )

    plt.plot(
        qubits,
        feasibility,
        marker="o",
        label="Feasibility rate",
    )

    plt.plot(
        qubits,
        optimal_probability,
        marker="s",
        label="Optimal solution probability",
    )

    plt.xticks(
        qubits
    )

    plt.xlabel(
        "Number of Qubits"
    )

    plt.ylabel(
        "Rate / Probability (%)"
    )

    plt.title(
        "QAOA Solution Quality vs Number of Qubits"
    )

    plt.legend()

    plt.grid(
        alpha=0.3
    )

    plt.ylim(
        bottom=0
    )

    save_figure(
        "qaoa_scaling_quality.png"
    )


# ============================================================
# 8. BITSTRING PROBABILITY DISTRIBUTION
# ============================================================

def plot_bitstring_distribution(
    rows,
):
    """
    Vẽ 10 Qiskit bitstring có xác suất cao nhất
    cho run topology_4, p=1, seed=0.

    Project optimal bitstring:
        1010

    Qiskit optimal bitstring:
        0101
    """

    selected = None

    for row in rows:

        if (
            row["topology"]
            == "topology_4"
            and int(row["p"])
            == 1
            and int(row["seed"])
            == 0
        ):
            selected = row
            break

    if selected is None:
        raise ValueError(
            "Cannot find "
            "topology_4, p=1, seed=0"
        )

    counts = json.loads(
        selected["counts"]
    )

    total = sum(
        counts.values()
    )

    probabilities = {
        bitstring:
            count / total

        for bitstring, count
        in counts.items()
    }

    # --------------------------------------------------------
    # Top 10 measured bitstrings
    # --------------------------------------------------------

    top_items = sorted(
        probabilities.items(),
        key=lambda item:
            item[1],
        reverse=True,
    )[:10]

    bitstrings = [
        item[0]
        for item in top_items
    ]

    probs = [
        item[1] * 100
        for item in top_items
    ]

    plt.figure(
        figsize=(9, 5)
    )

    bars = plt.bar(
        bitstrings,
        probs,
    )

    plt.xlabel(
        "Qiskit Bitstring"
    )

    plt.ylabel(
        "Probability (%)"
    )

    plt.title(
        "QAOA Bitstring Probability Distribution"
    )

    plt.grid(
        axis="y",
        alpha=0.3
    )

    plt.ylim(
        bottom=0
    )

    # --------------------------------------------------------
    # Optimal solution:
    #
    # Project bitstring = 1010
    # Qiskit bitstring  = 0101
    # Path              = A -> B -> D
    # Cost              = 5
    # --------------------------------------------------------

    optimal_qiskit_bitstring = (
        "0101"
    )

    # --------------------------------------------------------
    # Annotate bars
    # --------------------------------------------------------

    for bar, bitstring in zip(
        bars,
        bitstrings,
    ):
        height = (
            bar.get_height()
        )

        # Probability label
        plt.text(
            bar.get_x()
            + bar.get_width() / 2,
            height + 0.3,
            f"{height:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8,
        )

        # Highlight optimal bitstring
        if (
            bitstring
            == optimal_qiskit_bitstring
        ):
            bar.set_hatch(
                "//"
            )

            # Additional label so the hatch
            # cannot be misunderstood.
            plt.text(
                bar.get_x()
                + bar.get_width() / 2,
                height + 1.2,
                "Optimal",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
            )

    save_figure(
        "qaoa_bitstring_distribution.png"
    )


# ============================================================
# 9. QAOA SELECTED PATH
# ============================================================

def plot_qaoa_selected_path(
    rows,
):
    """
    Highlight feasible path có xác suất cao nhất
    của run topology_4, p=1, seed=0.

    Lưu ý:
    đây là highest-probability feasible path,
    không nhất thiết là optimal path.
    """

    selected = None

    for row in rows:

        if (
            row["topology"]
            == "topology_4"
            and int(row["p"])
            == 1
            and int(row["seed"])
            == 0
        ):
            selected = row
            break

    if selected is None:
        raise ValueError(
            "Cannot find "
            "topology_4, p=1, seed=0"
        )

    counts = json.loads(
        selected["counts"]
    )

    total = sum(
        counts.values()
    )

    # --------------------------------------------------------
    # topology_4 edge mapping
    #
    # Project:
    #
    # bit 0 -> A->B
    # bit 1 -> A->C
    # bit 2 -> B->D
    # bit 3 -> C->D
    #
    # Valid path 1:
    # Project 1010
    # Qiskit  0101
    # A -> B -> D
    # Cost = 5
    #
    # Valid path 2:
    # Project 0101
    # Qiskit  1010
    # A -> C -> D
    # Cost = 9
    # --------------------------------------------------------

    feasible_qiskit = {

        "0101": {
            "project":
                "1010",

            "path":
                [
                    "A",
                    "B",
                    "D",
                ],

            "cost":
                5,
        },

        "1010": {
            "project":
                "0101",

            "path":
                [
                    "A",
                    "C",
                    "D",
                ],

            "cost":
                9,
        },
    }

    candidates = []

    for bitstring, info in (
        feasible_qiskit.items()
    ):
        count = counts.get(
            bitstring,
            0,
        )

        probability = (
            count
            / total
        )

        candidates.append(
            (
                probability,
                bitstring,
                info,
            )
        )

    (
        best_probability,
        best_bitstring,
        best_info,
    ) = max(
        candidates,
        key=lambda item:
            item[0],
    )

    selected_path = (
        best_info[
            "path"
        ]
    )

    selected_edges = list(
        zip(
            selected_path[:-1],
            selected_path[1:],
        )
    )

    # ========================================================
    # BUILD TOPOLOGY
    # ========================================================

    graph = nx.DiGraph()

    graph.add_weighted_edges_from(
        [
            (
                "A",
                "B",
                2,
            ),

            (
                "A",
                "C",
                5,
            ),

            (
                "B",
                "D",
                3,
            ),

            (
                "C",
                "D",
                4,
            ),
        ]
    )

    positions = {

        "A": (
            0,
            0,
        ),

        "B": (
            1,
            1,
        ),

        "C": (
            1,
            -1,
        ),

        "D": (
            2,
            0,
        ),
    }

    plt.figure(
        figsize=(8, 5)
    )

    # ========================================================
    # DRAW NODES
    # ========================================================

    nx.draw_networkx_nodes(
        graph,
        positions,
        node_size=1800,
    )

    nx.draw_networkx_labels(
        graph,
        positions,
        font_size=12,
        font_weight="bold",
    )

    # ========================================================
    # DRAW ALL EDGES
    # ========================================================

    nx.draw_networkx_edges(
        graph,
        positions,
        edgelist=list(
            graph.edges()
        ),
        width=1.5,
        alpha=0.35,
        arrows=True,
        arrowsize=20,
    )

    # ========================================================
    # HIGHLIGHT HIGHEST-PROBABILITY FEASIBLE PATH
    # ========================================================

    nx.draw_networkx_edges(
        graph,
        positions,
        edgelist=selected_edges,
        width=4,
        arrows=True,
        arrowsize=22,
    )

    # ========================================================
    # EDGE WEIGHT LABELS
    # ========================================================

    edge_labels = {
        (
            u,
            v,
        ):
            data[
                "weight"
            ]

        for u, v, data
        in graph.edges(
            data=True
        )
    }

    nx.draw_networkx_edge_labels(
        graph,
        positions,
        edge_labels=edge_labels,
        font_size=10,
    )

    # ========================================================
    # TITLE
    # ========================================================

    route_text = (
        " -> ".join(
            selected_path
        )
    )

    plt.title(
        "Highest-Probability Feasible QAOA Path\n"
        f"{route_text}"
        f" | Cost = {best_info['cost']}"
        f" | Probability = "
        f"{best_probability * 100:.2f}%"
    )

    plt.axis(
        "off"
    )

    save_figure(
        "qaoa_selected_path.png"
    )

    # ========================================================
    # TERMINAL SUMMARY
    # ========================================================

    print()

    print(
        "[QAOA SELECTED PATH]"
    )

    print(
        "Qiskit bitstring:",
        best_bitstring
    )

    print(
        "Project bitstring:",
        best_info[
            "project"
        ]
    )

    print(
        "Path:",
        route_text
    )

    print(
        "Cost:",
        best_info[
            "cost"
        ]
    )

    print(
        "Probability:",
        f"{best_probability:.6f}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 70
    )

    print(
        "WEEK 6 - QAOA VISUALIZATION"
    )

    print(
        "=" * 70
    )

    depth_rows = load_csv(
        DEPTH_FILE
    )

    penalty_rows = load_csv(
        PENALTY_FILE
    )

    scaling_rows = load_csv(
        SCALING_FILE
    )

    # --------------------------------------------------------
    # Week 5 experimental results
    # --------------------------------------------------------

    plot_depth_optimal_probability(
        depth_rows
    )

    plot_depth_feasibility(
        depth_rows
    )

    plot_penalty_optimal_probability(
        penalty_rows
    )

    plot_penalty_feasibility(
        penalty_rows
    )

    # --------------------------------------------------------
    # Week 6 scaling results
    # --------------------------------------------------------

    plot_scaling_runtime(
        scaling_rows
    )

    plot_runtime_per_evaluation(
        scaling_rows
    )

    plot_scaling_quality(
        scaling_rows
    )

    # --------------------------------------------------------
    # Bitstring probability distribution
    # --------------------------------------------------------

    plot_bitstring_distribution(
        depth_rows
    )

    # --------------------------------------------------------
    # Highest-probability feasible QAOA path
    # --------------------------------------------------------

    plot_qaoa_selected_path(
        depth_rows
    )

    print()

    print(
        "=" * 70
    )

    print(
        "ALL QAOA VISUALIZATIONS GENERATED!"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()