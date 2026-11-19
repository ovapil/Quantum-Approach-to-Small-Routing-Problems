
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx


# =====================================================
# WEEK 6 - GĐ13: VISUALIZATION
# =====================================================

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULT_DIR = ROOT / "experiments" / "results"
FIGURE_DIR = ROOT / "experiments" / "figures"

FIGURE_DIR.mkdir(parents=True, exist_ok=True)

SIZES = [4, 6, 8, 10]


def load_csv(filename):
    path = RESULT_DIR / filename

    with path.open(
        "r", newline="", encoding="utf-8"
    ) as f:
        return list(csv.DictReader(f))


def save_figure(filename):
    path = FIGURE_DIR / filename

    plt.savefig(
        path,
        dpi=200,
        bbox_inches="tight"
    )
    plt.close()

    print(f"[PASS] Figure saved: {path}")


# =====================================================
# FIGURE 1: ORIGINAL TOPOLOGIES + DIJKSTRA PATH
# =====================================================

def draw_topologies():
    for size in SIZES:
        file_path = (
            DATA_DIR / f"topology_{size}.json"
        )

        with file_path.open(
            "r", encoding="utf-8"
        ) as f:
            data = json.load(f)

        graph = nx.DiGraph()

        graph.add_nodes_from(data["nodes"])

        for edge in data["edges"]:
            graph.add_edge(
                edge["source"],
                edge["target"],
                weight=edge["weight"]
            )

        source = data["source"]
        destination = data["destination"]

        path = nx.shortest_path(
            graph,
            source=source,
            target=destination,
            weight="weight"
        )

        path_cost = nx.path_weight(
            graph, path, weight="weight"
        )

        assert path_cost == data["expected_shortest_cost"]
        assert path == data["expected_shortest_path"]

        highlighted = list(zip(path[:-1], path[1:]))

        # Larger spacing for complex topologies
        positions = nx.spring_layout(
            graph,
            seed=42,
            k=2.5 if size >= 8 else 1.5,
            iterations=400,
            scale=2.5,
        )

        plt.figure(figsize=(15, 9) if size >= 8 else (10, 6))

        nx.draw_networkx_nodes(
            graph,
            positions,
            node_size=1100,
            node_color="#DBEAFE",
            edgecolors="#1E3A8A",
            linewidths=1.5
        )

        nx.draw_networkx_labels(
            graph,
            positions,
            font_size=12,
            font_weight="bold"
        )

        nx.draw_networkx_edges(
            graph,
            positions,
            edge_color="#A3A3A3",
            arrows=True,
            arrowsize=20,
            node_size=1100,
            width=1.6,
            connectionstyle="arc3,rad=0.04"
        )

        nx.draw_networkx_edges(
            graph,
            positions,
            edgelist=highlighted,
            edge_color="#DC2626",
            arrows=True,
            arrowsize=24,
            node_size=1100,
            width=3.5,
            connectionstyle="arc3,rad=0.04"
        )

        labels = nx.get_edge_attributes(
            graph, "weight"
        )

        nx.draw_networkx_edge_labels(
            graph,
            positions,
            edge_labels=labels,
            font_size=9 if size >= 8 else 10,
            font_color="black",
            rotate=False,
            label_pos=0.45,
            bbox={
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.95,
                "pad": 0.15,
            },
        )

        plt.title(
            f"Topology {size} nodes\n"
            f"Dijkstra: {' -> '.join(path)} | "
            f"Cost = {path_cost}",
            fontsize=14
        )

        plt.axis("off")

        save_figure(
            f"topology_{size}_dijkstra.png"
        )


# =====================================================
# FIGURE 2: QUBITS VS STATE-SPACE
# =====================================================

def draw_state_space():
    rows = load_csv("scalability_analysis.csv")

    qubits = [
        int(row["qubits"]) for row in rows
    ]

    states = [
        int(row["state_space_size"])
        for row in rows
    ]

    plt.figure(figsize=(9, 5))

    plt.plot(
        qubits,
        states,
        marker="o",
        linewidth=2
    )

    for q, s in zip(qubits, states):
        plt.annotate(
            f"{s:,}",
            (q, s),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center"
        )

    plt.xlabel("Number of qubits")
    plt.ylabel("State-space size (2^qubits)")
    plt.title("Qubit Count vs State-Space Size")
    plt.yscale("log", base=2)
    plt.grid(True, alpha=0.3)

    save_figure("qubits_vs_state_space.png")


# =====================================================
# FIGURE 3: GRAPH DENSITY VS QUBITS
# =====================================================

def draw_density_qubits():
    rows = load_csv("density_scalability.csv")

    density = [
        float(row["dag_density"])
        for row in rows
    ]

    qubits = [
        int(row["qubits"])
        for row in rows
    ]

    plt.figure(figsize=(9, 5))

    plt.plot(
        density,
        qubits,
        marker="o",
        linewidth=2
    )

    plt.xlabel("Graph density (DAG)")
    plt.ylabel("Number of qubits")
    plt.title("Graph Density vs Qubit Count")
    plt.grid(True, alpha=0.3)

    save_figure("density_vs_qubits.png")


# =====================================================
# FIGURE 4: GRAPH DENSITY VS STATE-SPACE
# =====================================================

def draw_density_states():
    rows = load_csv("density_scalability.csv")

    density = [
        float(row["dag_density"])
        for row in rows
    ]

    states = [
        int(row["state_space_size"])
        for row in rows
    ]

    plt.figure(figsize=(9, 5))

    plt.plot(
        density,
        states,
        marker="o",
        linewidth=2
    )

    plt.xlabel("Graph density (DAG)")
    plt.ylabel("State-space size")
    plt.title("Graph Density vs State-Space Size")
    plt.yscale("log", base=2)
    plt.grid(True, alpha=0.3)

    save_figure("density_vs_state_space.png")


def main():
    print("=" * 65)
    print("WEEK 6 - VISUALIZATION")
    print("=" * 65)

    draw_topologies()
    draw_state_space()
    draw_density_qubits()
    draw_density_states()

    print()
    print("ALL VISUALIZATIONS GENERATED!")


if __name__ == "__main__":
    main()
