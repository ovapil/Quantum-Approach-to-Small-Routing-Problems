"""
Đo giới hạn mô phỏng QAOA trên máy tính cổ điển.

Phần A - Tài nguyên mạch của các topology thật:
    số qubit, số hạng ZZ, độ sâu mạch và số cổng CX sau transpile (p = 1, 2, 3).

Phần B - Chi phí mô phỏng theo số qubit n:
    thời gian và bộ nhớ của MỘT lần đánh giá Estimator (p = 1) trên Hamiltonian
    giả lập có mật độ ZZ giống topology_10. Dừng khi một lần đánh giá vượt
    TIME_BUDGET_S hoặc hết RAM. Ước lượng thời gian một lần chạy QAOA đầy đủ
    = thời gian/lần đánh giá x EVALS_PER_RUN.

Output:
    experiments/results/circuit_resources.csv
    experiments/results/simulation_limit.csv
    experiments/figures/simulation_limit.png

Chạy:   python experiments/exp_simulation_limit.py
Lưu ý:  máy RAM <= 8 GB nên đặt MAX_QUBITS = 22.
"""

import csv
import time
import tracemalloc

import numpy as np
import matplotlib.pyplot as plt

from qiskit import transpile
from qiskit.circuit.library import qaoa_ansatz
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp

from experiment_runner import (
    PROJECT_ROOT,
    load_topology_graph,
    bounded_penalty,
)

from binary_encoding import create_edge_mapping
from qubo_builder import build_qubo
from qaoa_solver import qubo_to_cost_operator


TOPOLOGIES = ["topology_4", "topology_6", "topology_8", "topology_10"]
DEPTHS = [1, 2, 3]

MIN_QUBITS = 8
MAX_QUBITS = 24
STEP = 2
REPEATS = 3
TIME_BUDGET_S = 60.0
EVALS_PER_RUN = 900          # 300 * p * 3 restarts (p = 1)
SEED = 0

RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"
FIGURES_DIR = PROJECT_ROOT / "experiments" / "figures"


# ============================================================
# PHẦN A - TÀI NGUYÊN MẠCH
# ============================================================

def circuit_resources():
    rows = []
    for topology in TOPOLOGIES:
        graph, source, target = load_topology_graph(topology)
        mapping = create_edge_mapping(graph)
        n = len(mapping)
        penalty = bounded_penalty(graph, source, target, k=1.5)
        qubo = build_qubo(graph, mapping, source=source,
                          destination=target, penalty=penalty)
        operator, _, _, J = qubo_to_cost_operator(qubo, num_qubits=n)
        zz_terms = sum(1 for c in J.values() if abs(c) > 1e-12)

        for p in DEPTHS:
            circuit = qaoa_ansatz(operator, reps=p, flatten=True)
            compiled = transpile(
                circuit,
                basis_gates=["cx", "rz", "sx", "x"],
                optimization_level=1,
                seed_transpiler=SEED,
            )
            ops = compiled.count_ops()
            rows.append({
                "topology": topology,
                "qubits": n,
                "zz_terms": zz_terms,
                "p": p,
                "depth": compiled.depth(),
                "cx_count": ops.get("cx", 0),
                "total_gates": sum(ops.values()),
            })
            print(
                f"  {topology:<12} n={n:>2} ZZ={zz_terms:>3} p={p} "
                f"depth={compiled.depth():>4} CX={ops.get('cx', 0):>4}"
            )
    return rows


# ============================================================
# PHẦN B - CHI PHÍ MÔ PHỎNG THEO n
# ============================================================

def synthetic_operator(n, zz_per_qubit, rng):
    terms = [("Z", [i], rng.uniform(-1, 1)) for i in range(n)]
    all_pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    m = min(len(all_pairs), round(zz_per_qubit * n))
    for idx in rng.choice(len(all_pairs), size=m, replace=False):
        i, j = all_pairs[idx]
        terms.append(("ZZ", [i, j], rng.uniform(-1, 1)))
    return SparsePauliOp.from_sparse_list(terms, num_qubits=n)


def time_one_evaluation(n, zz_per_qubit, rng):
    operator = synthetic_operator(n, zz_per_qubit, rng)
    circuit = qaoa_ansatz(operator, reps=1, flatten=True)
    params = rng.uniform(0, np.pi, size=circuit.num_parameters)
    estimator = StatevectorEstimator()

    def evaluate():
        estimator.run([(circuit, operator, params)]).result()

    times = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        evaluate()
        times.append(time.perf_counter() - start)
        if times[-1] > TIME_BUDGET_S:
            break

    tracemalloc.start()
    evaluate()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return float(np.median(times)), peak / 2**20


def simulation_limit(zz_per_qubit):
    rng = np.random.default_rng(SEED)
    rows = []
    for n in range(MIN_QUBITS, MAX_QUBITS + 1, STEP):
        try:
            t_eval, peak_mib = time_one_evaluation(n, zz_per_qubit, rng)
        except MemoryError:
            print(f"  n={n}: MemoryError -> dừng")
            break

        row = {
            "qubits": n,
            "state_space_size": 2 ** n,
            "time_per_eval_s": t_eval,
            "est_full_run_s": t_eval * EVALS_PER_RUN,
            "peak_memory_mib": peak_mib,
            "theoretical_statevector_mib": 16 * 2 ** n / 2**20,
        }
        rows.append(row)
        print(
            f"  n={n:>2} | eval={t_eval:9.4f}s | "
            f"full run ~{row['est_full_run_s'] / 60:9.2f} min | "
            f"peak={peak_mib:9.1f} MiB | "
            f"statevector={row['theoretical_statevector_mib']:9.1f} MiB"
        )
        if t_eval > TIME_BUDGET_S:
            print(f"  Vượt TIME_BUDGET_S={TIME_BUDGET_S}s -> dừng")
            break
    return rows


def fit_growth(rows):
    """Fit log2(time) = a + b*n trên các điểm n >= 12 (bỏ overhead cố định)."""
    pts = [(r["qubits"], r["time_per_eval_s"]) for r in rows if r["qubits"] >= 12]
    if len(pts) < 2:
        pts = [(r["qubits"], r["time_per_eval_s"]) for r in rows]
    n, t = np.array(pts, dtype=float).T
    b, a = np.polyfit(n, np.log2(t), 1)
    return a, b


# ============================================================
# OUTPUT
# ============================================================

def save_csv(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[PASS] CSV created: {path}")


def plot(rows, fit, real_qubits):
    a, b = fit
    n = np.array([r["qubits"] for r in rows])
    t = np.array([r["time_per_eval_s"] for r in rows])
    mem = np.array([r["peak_memory_mib"] for r in rows])
    mem_theory = np.array([r["theoretical_statevector_mib"] for r in rows])

    n_ext = np.arange(n.min(), 31)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    ax = axes[0]
    ax.semilogy(n, t, "o-", label="Đo thực tế")
    ax.semilogy(n_ext, 2 ** (a + b * n_ext), "--",
                label=f"Ngoại suy (x{2 ** b:.2f}/qubit)")
    ax.set_xlabel("Số qubit n")
    ax.set_ylabel("Thời gian 1 lần đánh giá (s)")
    ax.set_title("Thời gian mô phỏng (QAOA p = 1)")

    ax = axes[1]
    ax.semilogy(n, mem, "o-", label="Peak RAM đo được")
    ax.semilogy(n_ext, 16 * 2.0 ** n_ext / 2**20, "--",
                label="Statevector lý thuyết (16·2ⁿ B)")
    ax.set_xlabel("Số qubit n")
    ax.set_ylabel("Bộ nhớ (MiB)")
    ax.set_title("Bộ nhớ mô phỏng")

    for ax in axes:
        for q in real_qubits:
            ax.axvline(q, color="gray", linestyle=":", linewidth=1)
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()

    fig.suptitle("Đường chấm dọc: số qubit của topology 4 / 6 / 8 / 10")
    fig.tight_layout()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURES_DIR / "simulation_limit.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[PASS] Figure created: {out}")


def main():
    print("=" * 80)
    print("PART A - CIRCUIT RESOURCES")
    print("=" * 80)
    resource_rows = circuit_resources()
    save_csv(resource_rows, RESULTS_DIR / "circuit_resources.csv")

    ref = next(r for r in resource_rows if r["topology"] == "topology_10")
    zz_per_qubit = ref["zz_terms"] / ref["qubits"]
    real_qubits = sorted({r["qubits"] for r in resource_rows})

    print("\n" + "=" * 80)
    print(f"PART B - SIMULATION LIMIT (ZZ/qubit = {zz_per_qubit:.2f})")
    print("=" * 80)
    limit_rows = simulation_limit(zz_per_qubit)
    save_csv(limit_rows, RESULTS_DIR / "simulation_limit.csv")

    if len(limit_rows) < 2:
        print("Không đủ điểm đo để ngoại suy.")
        return

    fit = fit_growth(limit_rows)
    a, b = fit
    print(f"\nThời gian tăng khoảng x{2 ** b:.2f} cho mỗi qubit thêm vào.")
    for n in (26, 28, 30):
        t = 2 ** (a + b * n)
        print(
            f"  Ngoại suy n={n}: ~{t:.1f}s/lần đánh giá, "
            f"~{t * EVALS_PER_RUN / 3600:.1f} giờ/lần chạy QAOA, "
            f"statevector {16 * 2 ** n / 2**30:.1f} GiB"
        )

    plot(limit_rows, fit, real_qubits)


if __name__ == "__main__":
    main()
