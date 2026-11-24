"""
Vẽ các hình cho báo cáo từ kết quả QAOA mới.

Input:
    experiments/results/qaoa_scaling.csv
    experiments/results/qaoa_depth.csv
    experiments/results/qaoa_penalty.csv

Output (experiments/figures/):
    report_scaling_vs_random.png   P_opt và feasibility của QAOA so với random theo số qubit
    report_depth_gain.png          gain theo độ sâu p (boxplot, từng topology)
    report_penalty_gain.png        gain theo hệ số k, kèm ngưỡng lý thuyết A = c*/2
    report_path_comparison.png     path Dijkstra và path top-1 của QAOA trên topology 6/8/10

Chạy:   python experiments/plot_report_figures.py
"""

import csv
import json
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

from experiment_runner import PROJECT_ROOT, load_topology_graph

from binary_encoding import create_edge_mapping
from metrics import decode_selected_path, to_project_bits


RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"
FIGURES_DIR = PROJECT_ROOT / "experiments" / "figures"

PATH_TOPOLOGIES = ["topology_6", "topology_8", "topology_10"]


# ============================================================
# HELPERS
# ============================================================

def load_rows(name):
    with (RESULTS_DIR / name).open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def save(fig, name, rect=None):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURES_DIR / name
    fig.tight_layout(rect=rect or (0, 0, 1, 1))
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[PASS] {out}")


def by_topology(rows):
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["topology"]].append(r)
    return dict(sorted(grouped.items(), key=lambda kv: int(kv[1][0]["qubits"])))


# ============================================================
# 1. SCALING: QAOA vs RANDOM
# ============================================================

def plot_scaling(datasets):
    """datasets: list of (label, rows, color, marker)."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    panels = [
        ("optimal_solution_probability", "random_optimal_prob",
         "Xác suất ra nghiệm tối ưu (P_opt)"),
        ("feasibility_rate", "random_feasible_prob",
         "Tỉ lệ nghiệm khả thi"),
    ]

    for ax, (col, rand_col, title) in zip(axes, panels):
        rand_curve = None
        zero_marks = []
        for d, (label, rows, color, marker) in enumerate(datasets):
            groups = by_topology(rows)
            q, mean = [], []
            offset = (d - (len(datasets) - 1) / 2) * 0.18
            for topo, rs in groups.items():
                vals = np.array([num(r[col]) for r in rs])
                n = int(rs[0]["qubits"])
                q.append(n)
                mean.append(vals.mean())
                positive = vals[vals > 0]
                ax.scatter(np.full(len(positive), n + offset), positive,
                           color=color, alpha=0.3, s=16, marker=marker)
            if rand_curve is None:
                rand_curve = (q, [num(rs[0][rand_col])
                                  for rs in groups.values()])

            q, mean = np.array(q), np.array(mean)
            ok = mean > 0
            ax.plot(q[ok], mean[ok], marker=marker, linestyle="-",
                    color=color, label=f"{label} (trung bình)")
            for x in q[~ok]:
                zero_marks.append((x, label, color))

        ax.plot(*rand_curve, "s--", color="tab:red", label="Random đều")
        for i, (x, label, color) in enumerate(zero_marks):
            ax.annotate(f"{label.replace('QAOA ', '')}: trung bình = 0", xy=(x, 0.03 + 0.07 * i),
                        xycoords=("data", "axes fraction"), color=color,
                        ha="right", fontsize=8)
        ax.set_yscale("log")
        ax.set_xticks(rand_curve[0])
        ax.set_xlabel("Số qubit (= số cung)")
        ax.set_title(title)
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=8)

    fig.suptitle("QAOA (p = 1, 10 seed) so với chọn ngẫu nhiên theo quy mô topology"
                 "\nĐiểm mờ: từng seed (seed có giá trị 0 không hiển thị trên trục log)",
                 fontsize=11)
    save(fig, "report_scaling_vs_random.png")


# ============================================================
# 2. DEPTH: GAIN BOXPLOT
# ============================================================

def plot_depth(rows):
    groups = by_topology(rows)
    fig, axes = plt.subplots(1, len(groups), figsize=(5.5 * len(groups), 4.2),
                             squeeze=False)

    for ax, (topo, rs) in zip(axes[0], groups.items()):
        depths = sorted({int(r["p"]) for r in rs})
        data = [[num(r["optimal_prob_gain"]) for r in rs if int(r["p"]) == p]
                for p in depths]
        ax.boxplot(data, showfliers=False)
        ax.set_xticks(range(1, len(depths) + 1))
        ax.set_xticklabels([f"p={p}" for p in depths])
        for i, vals in enumerate(data, start=1):
            ax.scatter(np.full(len(vals), i), vals, alpha=0.5, s=18)
        ax.axhline(1, color="tab:red", linestyle="--", label="Random (gain = 1)")
        ax.set_title(f"{topo} ({rs[0]['qubits']} qubit)")
        ax.set_ylabel("Gain = P_opt / P_random")
        ax.grid(True, alpha=0.3)
        ax.legend()

    fig.suptitle("Ảnh hưởng của độ sâu p (k = 1.5, 5 seed)")
    save(fig, "report_depth_gain.png")


# ============================================================
# 3. PENALTY: GAIN vs k
# ============================================================

def plot_penalty(rows):
    groups = by_topology(rows)
    fig, axes = plt.subplots(1, len(groups), figsize=(5.5 * len(groups), 4.2),
                             squeeze=False)

    for ax, (topo, rs) in zip(axes[0], groups.items()):
        ks = sorted({num(r["penalty_k"]) for r in rs})
        means, medians = [], []
        for k in ks:
            vals = [num(r["optimal_prob_gain"]) for r in rs
                    if num(r["penalty_k"]) == k]
            ax.scatter([k] * len(vals), vals, alpha=0.4, s=18,
                       color="tab:blue")
            means.append(np.mean(vals))
            medians.append(np.median(vals))
        ax.plot(ks, means, "o-", color="tab:blue", label="Trung bình 5 seed")
        ax.plot(ks, medians, "s:", color="tab:purple", label="Median 5 seed")

        # Ngưỡng lý thuyết A = c*/2  <=>  k* = c* * k / (2A)
        r0 = rs[0]
        k_star = num(r0["dijkstra_cost"]) * num(r0["penalty_k"]) / (
            2 * num(r0["penalty_A"]))
        ax.axvline(k_star, color="tab:green", linestyle=":",
                   label=f"Ngưỡng A = c*/2 (k ≈ {k_star:.2f})")
        ax.axhline(1, color="tab:red", linestyle="--", label="Random")
        ax.set_xscale("log")
        ax.set_xticks(ks)
        ax.set_xticklabels([f"{k:g}" for k in ks])
        ax.xaxis.set_minor_formatter(plt.NullFormatter())
        ax.set_xlabel("k  (A = k · c_UB / 2)")
        ax.set_ylabel("Gain = P_opt / P_random")
        ax.set_title(f"{topo} ({r0['qubits']} qubit)")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

    fig.suptitle("Ảnh hưởng của hệ số penalty")
    save(fig, "report_penalty_gain.png")


# ============================================================
# 4. PATH: DIJKSTRA vs QAOA TOP-1
# ============================================================

def top1_feasible_path(row, edges, source, target):
    counts = json.loads(row["counts"])
    best = None
    for bitstring, shots in counts.items():
        bits = to_project_bits(bitstring, "qiskit")
        valid, path, cost = decode_selected_path(bits, edges, source, target)
        if valid and (best is None or shots > best[0]):
            best = (shots, path, cost)
    return best


def _segment_clearance(p, a, b):
    """Khoảng cách từ điểm p tới đoạn thẳng ab."""
    p, a, b = map(np.asarray, (p, a, b))
    ab = b - a
    t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1)
    return np.linalg.norm(p - (a + t * ab))


def _crossings(pos, edges):
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

    count = 0
    for i, (u1, v1) in enumerate(edges):
        for u2, v2 in edges[i + 1:]:
            if len({u1, v1, u2, v2}) < 4:
                continue
            a, b, c, d = pos[u1], pos[v1], pos[u2], pos[v2]
            if ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d):
                count += 1
    return count


def layered_layout(graph):
    """
    Layout theo lớp (DAG), cố định giữa các lần chạy.
    Thử các độ lệch dọc cho từng lớp và chọn layout sao cho
    không cạnh nào đi sát/xuyên qua node khác và ít giao cắt nhất.
    """
    from itertools import product

    layers = [sorted(nodes) for nodes in nx.topological_generations(graph)]
    edges = list(graph.edges())
    offsets = (-0.5, -0.25, 0.0, 0.25, 0.5)

    best_pos, best_score = None, None
    for shift in product(offsets, repeat=len(layers)):
        pos = {}
        for x, (nodes, dy) in enumerate(zip(layers, shift)):
            for i, node in enumerate(nodes):
                pos[node] = (float(x), (len(nodes) - 1) / 2 - i + dy)

        clearance = min(
            (_segment_clearance(pos[w], pos[u], pos[v])
             for u, v in edges for w in graph.nodes if w not in (u, v)),
            default=1.0,
        )
        score = (min(clearance, 0.35), -_crossings(pos, edges), -sum(map(abs, shift)))
        if best_score is None or score > best_score:
            best_pos, best_score = pos, score
    return best_pos


def path_edges(path):
    return list(zip(path, path[1:])) if path else []


def plot_paths(rows):
    fig, axes = plt.subplots(1, len(PATH_TOPOLOGIES),
                             figsize=(6 * len(PATH_TOPOLOGIES), 5))

    for ax, topo in zip(axes, PATH_TOPOLOGIES):
        rs = [r for r in rows if r["topology"] == topo]
        if not rs:
            ax.set_axis_off()
            continue

        # Run tốt nhất theo P_opt (minh họa trường hợp QAOA hoạt động tốt nhất)
        row = max(rs, key=lambda r: num(r["optimal_solution_probability"]))

        graph, source, target = load_topology_graph(topo)
        mapping = create_edge_mapping(graph)
        edges = [(*mapping[i]["edge"], mapping[i]["weight"])
                 for i in range(len(mapping))]

        dijkstra_path = row["dijkstra_path"].split("->")
        top1 = top1_feasible_path(row, edges, source, target)

        pos = layered_layout(graph)
        nx.draw_networkx_nodes(graph, pos, ax=ax, node_color="#dde6f5",
                               edgecolors="black", node_size=650)
        nx.draw_networkx_labels(graph, pos, ax=ax)
        nx.draw_networkx_edges(graph, pos, ax=ax, edge_color="lightgray",
                               arrows=True, arrowsize=14)
        nx.draw_networkx_edges(graph, pos, ax=ax,
                               edgelist=path_edges(dijkstra_path),
                               edge_color="tab:green", width=5, alpha=0.6,
                               arrows=True, arrowsize=14)

        if top1:
            shots, qaoa_path, qaoa_cost = top1
            nx.draw_networkx_edges(graph, pos, ax=ax,
                                   edgelist=path_edges(qaoa_path),
                                   edge_color="tab:red", width=2,
                                   style="dashed", arrows=True, arrowsize=14)
            qaoa_text = f"QAOA top-1: cost {qaoa_cost:g}"
        else:
            qaoa_text = "QAOA: không có nghiệm khả thi"

        nx.draw_networkx_edge_labels(
            graph, pos, ax=ax, font_size=8, label_pos=0.4,
            edge_labels={(u, v): d["weight"] for u, v, d in graph.edges(data=True)},
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"),
        )

        ax.set_title(
            f"{topo} | seed {row['seed']} | P_opt = "
            f"{num(row['optimal_solution_probability']):.4f}\n"
            f"Dijkstra: cost {num(row['dijkstra_cost']):g} | {qaoa_text}",
            fontsize=10,
        )
        ax.set_axis_off()

    handles = [
        plt.Line2D([], [], color="tab:green", linewidth=5, alpha=0.6,
                   label="Dijkstra (tối ưu)"),
        plt.Line2D([], [], color="tab:red", linewidth=2, linestyle="--",
                   label="QAOA top-1 khả thi"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2)
    fig.suptitle("Path tìm được: Dijkstra và QAOA (p = 1, k = 1.5, run có P_opt cao nhất)")
    save(fig, "report_path_comparison.png", rect=(0, 0.08, 1, 1))


# ============================================================
# MAIN
# ============================================================

def main():
    scaling = load_rows("qaoa_scaling.csv")
    datasets = [("QAOA k = 1.5", scaling, "tab:blue", "o")]
    if (RESULTS_DIR / "qaoa_scaling_k08.csv").exists():
        datasets.append(("QAOA k = 0.8", load_rows("qaoa_scaling_k08.csv"),
                         "tab:green", "^"))
    plot_scaling(datasets)
    plot_paths(scaling)
    plot_depth(load_rows("qaoa_depth.csv"))
    plot_penalty(load_rows("qaoa_penalty.csv"))


if __name__ == "__main__":
    main()
