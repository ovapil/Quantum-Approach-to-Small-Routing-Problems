"""
Thí nghiệm quy mô: QAOA p = 1 trên topology 4/6/8/10, nhiều seed.

Tăng tốc (feedback giữa kỳ: "cần tăng tốc quá trình đánh giá thực nghiệm"):
    - Chạy song song các cặp (topology, seed), N_JOBS process cùng lúc.
    - Tùy chọn backend Aer (C++) thay cho primitives tham chiếu của Qiskit:
          Git Bash:    QAOA_BACKEND=aer python experiments/exp_qaoa_scaling.py
          PowerShell:  $env:QAOA_BACKEND="aer"; python experiments/exp_qaoa_scaling.py

Output: experiments/results/<OUTPUT_NAME>
"""

import os
import sys
import time
from itertools import product
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from experiment_runner import run_many, save_experiment_csv


# ============================================================
# CẤU HÌNH
# ============================================================

TOPOLOGIES = ["topology_4", "topology_6", "topology_8", "topology_10"]
QAOA_DEPTH = 1
SHOTS = 2048
SEEDS = list(range(10))
MAXITER = None                         # None -> 300 * p
PENALTY_K = 0.8                        # 1.5 = cấu hình gốc
OUTPUT_NAME = "qaoa_scaling_k08.csv"  # "qaoa_scaling.csv" = cấu hình gốc
N_JOBS = None                          # None = nửa số luồng CPU; 1 = tuần tự như cũ


def penalty_k_for(topology):
    # topology_4: c_UB = c*, nên k = 0.8 nằm dưới ngưỡng A > c*/2 -> giữ 1.5
    return 1.5 if topology == "topology_4" else PENALTY_K


def main():
    backend = os.environ.get("QAOA_BACKEND", "reference")
    configs = [
        dict(
            topology_name=topology,
            p=QAOA_DEPTH,
            penalty=None,
            penalty_k=penalty_k_for(topology),
            shots=SHOTS,
            seed=seed,
            maxiter=MAXITER,
        )
        for topology, seed in product(TOPOLOGIES, SEEDS)
    ]

    print("=" * 75)
    print("QAOA SCALABILITY EXPERIMENT")
    print("=" * 75)
    print(f"Topologies: {TOPOLOGIES}")
    print(f"p = {QAOA_DEPTH} | shots = {SHOTS} | seeds = {SEEDS}")
    print(f"Penalty: A = {PENALTY_K} * c_UB / 2 (topology_4 giữ k = 1.5)")
    print(f"Backend: {backend} | N_JOBS: {N_JOBS or 'auto'} | runs: {len(configs)}")
    print("=" * 75)

    start = time.perf_counter()
    outputs = run_many(configs, n_jobs=N_JOBS)
    wall_time = time.perf_counter() - start

    results, failures = [], []
    for out in outputs:
        if "error" in out:
            failures.append(out)
            continue
        out["experiment"] = "qaoa_scaling"
        out["backend"] = backend
        results.append(out)

    print("\nSUMMARY")
    print("-" * 75)
    for r in results:
        print(
            f"{r['topology']:<12} | qubits={r['qubits']:>2} | seed={r['seed']}"
            f" | feas={r['feasibility_rate']:.4f}"
            f" | P_opt={r['optimal_solution_probability']:.4f}"
            f" | gain={r['optimal_prob_gain']:.2f}"
            f" | top1={r['match_optimal']}"
            f" | success={r['optimization_success']}"
            f" | {r['runtime_seconds']:.2f}s"
        )
    for f in failures:
        print(f"[FAIL] {f['topology_name']} seed={f['seed']}: {f['error']}")

    if results:
        output_path = PROJECT_ROOT / "experiments" / "results" / OUTPUT_NAME
        save_experiment_csv(results, output_path)
        print(f"\n[PASS] CSV created: {output_path}")

    total_run_time = sum(r["runtime_seconds"] for r in results)
    print(f"Successful runs: {len(results)}/{len(configs)}")
    print(
        f"Wall time: {wall_time:.1f}s | tổng runtime các run: {total_run_time:.1f}s"
        f" | tăng tốc ~x{total_run_time / wall_time:.1f}"
    )


if __name__ == "__main__":
    main()
