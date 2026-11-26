"""
So sánh QAOA với các baseline cổ điển CÙNG bài toán QUBO, CÙNG metrics, CÙNG cấu hình
(feedback giữa kỳ: "cần kế hoạch so sánh với các baselines cổ điển cùng metrics, cấu hình").

Cấu hình chung (giống thí nghiệm quy mô của QAOA):
    - topology 6 / 8 / 10, cùng QUBO, cùng hệ số penalty A = k * c_UB / 2 (k = 0.8)
    - cùng số mẫu: 2048 / lần chạy, cùng 10 seed (0–9)
    - cùng metrics: tỉ lệ khả thi, P_opt, gain so với random, top-1 match, optimality gap, runtime

Phương pháp:
    QAOA (p = 1)          đọc từ results/qaoa_scaling_k08.csv (không chạy lại)
    Simulated Annealing   heuristic cổ điển lấy mẫu trên cùng hàm năng lượng QUBO
    Random sampling       2048 bitstring ngẫu nhiên đều (chạy thật, không chỉ tính lý thuyết)
    Exhaustive QUBO       duyệt toàn bộ 2^n, nghiệm chính xác của QUBO
    Dijkstra              nghiệm chính xác trên đồ thị

Output:
    experiments/results/classical_baselines.csv      mỗi dòng = 1 lần chạy
    experiments/results/baseline_summary.csv         trung bình theo (phương pháp, topology)
    experiments/figures/report_baselines.png

Chạy:   python experiments/exp_classical_baselines.py
"""

import csv
import time
from collections import Counter
from pathlib import Path
from statistics import mean, median

import numpy as np
import matplotlib.pyplot as plt

from experiment_runner import PROJECT_ROOT, load_topology_graph, bounded_penalty

from binary_encoding import create_edge_mapping
from dijkstra_solver import solve_dijkstra
from metrics import calculate_metrics
from qubo_builder import build_qubo


# ============================================================
# CẤU HÌNH (giữ giống exp_qaoa_scaling.py)
# ============================================================

TOPOLOGIES = ["topology_6", "topology_8", "topology_10"]
PENALTY_K = 0.8
NUM_SAMPLES = 2048
SEEDS = list(range(10))

SA_SWEEPS = 100          # số vòng quét của Simulated Annealing
SA_T_MIN = 0.05          # nhiệt độ cuối; nhiệt độ đầu = |ΔE| lớn nhất có thể

QAOA_CSV = "qaoa_scaling_k08.csv"

RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"
FIGURES_DIR = PROJECT_ROOT / "experiments" / "figures"

METHOD_ORDER = ["QAOA (p=1)", "Simulated Annealing", "Random sampling",
                "Exhaustive QUBO", "Dijkstra"]


# ============================================================
# QUBO DẠNG MA TRẬN
# ============================================================

def qubo_arrays(qubo, n):
    """E(x) = constant + lin·x + 1/2 · xᵀ Q x  (Q đối xứng, đường chéo 0)."""
    lin = np.zeros(n)
    Q = np.zeros((n, n))
    for i, a in qubo["linear"].items():
        lin[i] += a
    for (i, j), q in qubo["quadratic"].items():
        if i == j:
            lin[i] += q          # x_i^2 = x_i
        else:
            Q[i, j] += q
            Q[j, i] += q
    return lin, Q


def energies(X, lin, Q, constant):
    return constant + X @ lin + 0.5 * np.einsum("ri,ij,rj->r", X, Q, X)


# ============================================================
# CÁC BỘ GIẢI CỔ ĐIỂN
# ============================================================

def simulated_annealing(lin, Q, num_reads, sweeps, rng):
    """
    SA một bit mỗi bước (Metropolis), chạy song song num_reads chuỗi bằng numpy.
    ΔE khi lật bit i = (1 − 2x_i) · (lin_i + Σ_j Q_ij x_j).
    """
    n = len(lin)
    X = rng.integers(0, 2, size=(num_reads, n)).astype(float)
    t_max = float(np.max(np.abs(lin) + np.abs(Q).sum(axis=1)))
    for T in np.geomspace(t_max, SA_T_MIN, sweeps):
        for i in rng.permutation(n):
            delta = (1 - 2 * X[:, i]) * (lin[i] + X @ Q[:, i])
            accept = (delta <= 0) | (
                rng.random(num_reads) < np.exp(-np.clip(delta, 0, None) / T)
            )
            X[accept, i] = 1 - X[accept, i]
    return X


def random_sampling(n, num_reads, rng):
    return rng.integers(0, 2, size=(num_reads, n)).astype(float)


def exhaustive_qubo(lin, Q, constant):
    n = len(lin)
    X = ((np.arange(2 ** n)[:, None] >> np.arange(n)) & 1).astype(float)
    return X[np.argmin(energies(X, lin, Q, constant))]


def to_counts(X):
    """Bitstring theo thứ tự project (bit i = cung mapping[i])."""
    return Counter("".join(str(int(b)) for b in row) for row in X)


# ============================================================
# MỘT DÒNG KẾT QUẢ (cùng schema cho mọi phương pháp)
# ============================================================

def make_row(method, topology, n, seed, penalty, samples, metric, runtime):
    return {
        "method": method,
        "topology": topology,
        "qubits": n,
        "seed": seed,
        "penalty_A": round(penalty, 4) if penalty is not None else "",
        "samples": samples,
        "feasibility_rate": metric["feasibility_rate"],
        "optimal_solution_probability": metric["optimal_solution_probability"],
        "optimal_prob_gain": metric["optimal_prob_gain"],
        "top1_match": metric["top1_match"],
        "optimality_gap": metric["optimality_gap"],
        "mean_feasible_cost": metric["mean_feasible_cost"],
        "runtime_seconds": runtime,
    }


def run_topology(topology):
    graph, source, target = load_topology_graph(topology)
    mapping = create_edge_mapping(graph)
    n = len(mapping)
    edges = [(*mapping[i]["edge"], mapping[i]["weight"]) for i in range(n)]

    t0 = time.perf_counter()
    dijkstra_path, c_star = solve_dijkstra(graph, source, target)
    t_dijkstra = time.perf_counter() - t0

    penalty = bounded_penalty(graph, source, target, k=PENALTY_K)
    qubo = build_qubo(graph, mapping, source=source,
                      destination=target, penalty=penalty)
    lin, Q = qubo_arrays(qubo, n)

    def metrics_of(counts, runtime):
        return calculate_metrics(counts, edges, source, target, c_star,
                                 bit_order="project", runtime_seconds=runtime)

    rows = []
    for seed in SEEDS:
        rng = np.random.default_rng(seed)

        t0 = time.perf_counter()
        X = simulated_annealing(lin, Q, NUM_SAMPLES, SA_SWEEPS, rng)
        t = time.perf_counter() - t0
        rows.append(make_row("Simulated Annealing", topology, n, seed, penalty,
                             NUM_SAMPLES, metrics_of(to_counts(X), t), t))

        t0 = time.perf_counter()
        X = random_sampling(n, NUM_SAMPLES, rng)
        t = time.perf_counter() - t0
        rows.append(make_row("Random sampling", topology, n, seed, penalty,
                             NUM_SAMPLES, metrics_of(to_counts(X), t), t))

    # Hai phương pháp chính xác: tất định, chạy 1 lần
    t0 = time.perf_counter()
    x_star = exhaustive_qubo(lin, Q, qubo["constant"])
    t = time.perf_counter() - t0
    rows.append(make_row("Exhaustive QUBO", topology, n, "-", penalty, 2 ** n,
                         metrics_of(to_counts([x_star]), t), t))

    dijkstra_bits = "".join(
        "1" if (u, v) in set(zip(dijkstra_path, dijkstra_path[1:])) else "0"
        for u, v, _ in edges
    )
    rows.append(make_row("Dijkstra", topology, n, "-", None, 1,
                         metrics_of({dijkstra_bits: 1}, t_dijkstra), t_dijkstra))
    return rows


def load_qaoa_rows():
    path = RESULTS_DIR / QAOA_CSV
    if not path.exists():
        print(f"[WARN] Không thấy {path.name}; bảng so sánh sẽ thiếu QAOA.")
        return []
    csv.field_size_limit(10 ** 9)
    with path.open(encoding="utf-8") as f:
        source_rows = [r for r in csv.DictReader(f) if r["topology"] in TOPOLOGIES]

    num = lambda v: float(v) if v not in ("", "None") else None
    return [{
        "method": "QAOA (p=1)",
        "topology": r["topology"],
        "qubits": int(r["qubits"]),
        "seed": int(r["seed"]),
        "penalty_A": num(r["penalty_A"]),
        "samples": int(r["shots"]),
        "feasibility_rate": num(r["feasibility_rate"]),
        "optimal_solution_probability": num(r["optimal_solution_probability"]),
        "optimal_prob_gain": num(r["optimal_prob_gain"]),
        "top1_match": r["match_optimal"] == "True",
        "optimality_gap": num(r["optimality_gap"]),
        "mean_feasible_cost": num(r["mean_feasible_cost"]),
        "runtime_seconds": num(r["runtime_seconds"]),
    } for r in source_rows]


# ============================================================
# TỔNG HỢP, LƯU, VẼ
# ============================================================

def summarize(rows):
    summary = []
    for method in METHOD_ORDER:
        for topology in TOPOLOGIES:
            rs = [r for r in rows
                  if r["method"] == method and r["topology"] == topology]
            if not rs:
                continue
            gaps = [r["optimality_gap"] for r in rs if r["optimality_gap"] is not None]
            summary.append({
                "method": method,
                "topology": topology,
                "qubits": rs[0]["qubits"],
                "runs": len(rs),
                "mean_feasibility_rate": mean(r["feasibility_rate"] for r in rs),
                "mean_optimal_probability": mean(
                    r["optimal_solution_probability"] for r in rs),
                "median_gain": median(r["optimal_prob_gain"] for r in rs),
                "top1_matches": sum(bool(r["top1_match"]) for r in rs),
                "mean_optimality_gap": mean(gaps) if gaps else None,
                "runs_without_feasible": len(rs) - len(gaps),
                "mean_runtime_seconds": mean(r["runtime_seconds"] for r in rs),
            })
    return summary


def save_csv(rows, name):
    path = RESULTS_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[PASS] CSV created: {path}")


def plot(summary):
    styles = {
        "QAOA (p=1)": ("tab:blue", "o", "-"),
        "Simulated Annealing": ("tab:green", "^", "-"),
        "Random sampling": ("tab:red", "s", "--"),
        "Exhaustive QUBO": ("tab:gray", "D", ":"),
        "Dijkstra": ("black", "x", ":"),
    }
    panels = [
        ("mean_optimal_probability", "Xác suất ra nghiệm tối ưu (P_opt)"),
        ("mean_feasibility_rate", "Tỉ lệ nghiệm khả thi"),
        ("mean_runtime_seconds", "Runtime trung bình / lần chạy (s)"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
    for ax, (col, title) in zip(axes, panels):
        zero_notes = []
        for method in METHOD_ORDER:
            rs = [s for s in summary if s["method"] == method]
            if not rs:
                continue
            color, marker, ls = styles[method]
            q = np.array([s["qubits"] for s in rs])
            v = np.array([s[col] for s in rs], dtype=float)
            ok = v > 0
            ax.plot(q[ok], v[ok], marker=marker, linestyle=ls, color=color,
                    label=method)
            zero_notes += [(x, method, color) for x in q[~ok]]
        for i, (x, method, color) in enumerate(zero_notes):
            ax.annotate(f"{method}: = 0", xy=(x, 0.03 + 0.07 * i),
                        xycoords=("data", "axes fraction"), xytext=(-14, 0),
                        textcoords="offset points", ha="right", va="bottom",
                        color=color, fontsize=8)
        ax.set_yscale("log")
        ax.set_xticks(sorted({s["qubits"] for s in summary}))
        ax.set_xlabel("Số qubit (= số cung)")
        ax.set_title(title)
        ax.grid(True, which="both", alpha=0.3)
    axes[0].legend(fontsize=8)
    fig.suptitle(
        f"QAOA so với baseline cổ điển trên cùng QUBO "
        f"(k = {PENALTY_K}, {NUM_SAMPLES} mẫu, {len(SEEDS)} seed)"
    )
    fig.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURES_DIR / "report_baselines.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[PASS] Figure created: {out}")


def main():
    print("=" * 100)
    print("QAOA vs CLASSICAL BASELINES (same QUBO, same metrics, same configuration)")
    print("=" * 100)

    rows = load_qaoa_rows()
    for topology in TOPOLOGIES:
        print(f"Running classical baselines on {topology} ...")
        rows.extend(run_topology(topology))

    save_csv(rows, "classical_baselines.csv")
    summary = summarize(rows)
    save_csv(summary, "baseline_summary.csv")

    print()
    header = (f"{'method':<20}{'topology':<13}{'runs':>5}{'feas':>9}{'P_opt':>9}"
              f"{'gain(med)':>11}{'top1':>7}{'gap':>8}{'runtime(s)':>12}")
    print(header)
    print("-" * len(header))
    for s in summary:
        gap = "-" if s["mean_optimality_gap"] is None else f"{s['mean_optimality_gap']:.3f}"
        print(f"{s['method']:<20}{s['topology']:<13}{s['runs']:>5}"
              f"{s['mean_feasibility_rate']:>9.4f}{s['mean_optimal_probability']:>9.4f}"
              f"{s['median_gain']:>11.1f}{s['top1_matches']:>4}/{s['runs']:<2}"
              f"{gap:>8}{s['mean_runtime_seconds']:>12.4f}")

    plot(summary)


if __name__ == "__main__":
    main()
