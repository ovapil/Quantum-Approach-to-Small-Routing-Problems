"""
Kiểm chứng mô hình QUBO bằng vét cạn (brute force).

Với mỗi topology và mỗi hệ số k (A = k * c_UB / 2):
    - Duyệt toàn bộ 2^|E| bitstring và tính năng lượng QUBO.
    - Kiểm tra ground state có phải path hợp lệ và trùng Dijkstra không.
    - Ghi khoảng cách năng lượng giữa nghiệm tối ưu và nghiệm
      không khả thi tốt nhất (energy_gap > 0 <=> ground state hợp lệ).

Output: experiments/results/qubo_verification.csv
Chạy:   python experiments/exp_qubo_verification.py
"""

import csv
from itertools import product
from math import isclose

from experiment_runner import (
    PROJECT_ROOT,
    load_topology_graph,
    bounded_penalty,
)

from binary_encoding import create_edge_mapping
from dijkstra_solver import solve_dijkstra
from metrics import decode_selected_path
from qubo_builder import build_qubo


TOPOLOGIES = ["topology_4", "topology_6", "topology_8", "topology_10"]

# k = 0.5 cố ý cho A có thể nằm dưới ngưỡng c*/2 để minh họa
PENALTY_KS = [0.5, 0.8, 1.0, 1.5]

OUTPUT_PATH = PROJECT_ROOT / "experiments" / "results" / "qubo_verification.csv"


def qubo_energy(x, qubo):
    """Năng lượng QUBO cho vector bit x (thứ tự project)."""
    energy = qubo["constant"]
    for i, a in qubo["linear"].items():
        if x[i]:
            energy += a
    for (i, j), q in qubo["quadratic"].items():
        if x[i] and x[j]:
            energy += q
    return energy


def verify_topology(topology_name):
    graph, source, target = load_topology_graph(topology_name)
    mapping = create_edge_mapping(graph)
    n = len(mapping)

    edges = [(*mapping[i]["edge"], mapping[i]["weight"]) for i in range(n)]
    dijkstra_path, dijkstra_cost = solve_dijkstra(graph, source, target)

    qubos = {}
    for k in PENALTY_KS:
        penalty = bounded_penalty(graph, source, target, k=k)
        qubos[k] = (
            penalty,
            build_qubo(graph, mapping, source=source,
                       destination=target, penalty=penalty),
        )

    # Theo dõi cho từng k
    stats = {
        k: {
            "ground_energy": float("inf"),
            "ground_states": [],
            "min_feasible_energy": float("inf"),
            "min_infeasible_energy": float("inf"),
        }
        for k in PENALTY_KS
    }

    for x in product((0, 1), repeat=n):
        bits = "".join(map(str, x))
        valid, path, _ = decode_selected_path(bits, edges, source, target)

        for k in PENALTY_KS:
            s = stats[k]
            e = qubo_energy(x, qubos[k][1])

            if e < s["ground_energy"] - 1e-9:
                s["ground_energy"] = e
                s["ground_states"] = [(valid, path)]
            elif isclose(e, s["ground_energy"], abs_tol=1e-9):
                s["ground_states"].append((valid, path))

            if valid:
                s["min_feasible_energy"] = min(s["min_feasible_energy"], e)
            else:
                s["min_infeasible_energy"] = min(s["min_infeasible_energy"], e)

    rows = []
    for k in PENALTY_KS:
        s = stats[k]
        penalty = qubos[k][0]
        ground_all_valid = all(v for v, _ in s["ground_states"])
        ground_paths = sorted(
            {"->".join(p) for v, p in s["ground_states"] if v}
        )
        matches = (
            ground_all_valid
            and ground_paths == ["->".join(dijkstra_path)]
        )

        rows.append({
            "topology": topology_name,
            "qubits": n,
            "state_space_size": 2 ** n,
            "penalty_k": k,
            "penalty_A": round(penalty, 4),
            "threshold_A": dijkstra_cost / 2,
            "A_above_threshold": penalty > dijkstra_cost / 2,
            "dijkstra_path": "->".join(dijkstra_path),
            "dijkstra_cost": dijkstra_cost,
            "ground_energy": round(s["ground_energy"], 6),
            "num_ground_states": len(s["ground_states"]),
            "ground_state_feasible": ground_all_valid,
            "ground_state_path": ";".join(ground_paths) or "-",
            "ground_matches_dijkstra": matches,
            "min_infeasible_energy": round(s["min_infeasible_energy"], 6),
            "energy_gap": round(
                s["min_infeasible_energy"] - s["min_feasible_energy"], 6
            ),
        })
    return rows


def main():
    print("=" * 100)
    print("QUBO VERIFICATION (BRUTE FORCE)")
    print("=" * 100)

    all_rows = []
    for topology in TOPOLOGIES:
        print(f"\nVerifying {topology} ...")
        all_rows.extend(verify_topology(topology))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)

    print()
    header = (
        f"{'topology':<12}{'k':>5}{'A':>8}{'c*/2':>7}"
        f"{'ground E':>10}{'#GS':>5}{'feasible':>10}"
        f"{'=Dijkstra':>11}{'gap':>9}  ground path"
    )
    print(header)
    print("-" * len(header) + "-" * 15)
    for r in all_rows:
        print(
            f"{r['topology']:<12}{r['penalty_k']:>5}{r['penalty_A']:>8.2f}"
            f"{r['threshold_A']:>7.1f}{r['ground_energy']:>10.2f}"
            f"{r['num_ground_states']:>5}{str(r['ground_state_feasible']):>10}"
            f"{str(r['ground_matches_dijkstra']):>11}{r['energy_gap']:>9.2f}"
            f"  {r['ground_state_path']}"
        )

    print(f"\n[PASS] CSV created: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
