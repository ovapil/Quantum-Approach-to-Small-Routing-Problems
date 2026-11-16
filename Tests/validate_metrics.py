
import sys
from pathlib import Path
from math import isclose

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from metrics import (
    calculate_metrics,
    decode_selected_path,
    shortest_path_dijkstra,
    scaling_info,
    save_results_csv,
    CSV_FIELDS,
)


EDGES = [
    ("A", "B", 2),
    ("A", "C", 5),
    ("B", "D", 3),
    ("C", "D", 4),
]

NODES = ["A", "B", "C", "D"]


def check(actual, expected):
    assert isclose(
        actual, expected,
        rel_tol=1e-9, abs_tol=1e-9
    ), (actual, expected)


def test_reference():
    path, cost = shortest_path_dijkstra(
        NODES, EDGES, "A", "D"
    )

    assert path == ["A", "B", "D"]
    assert cost == 5

    print("[PASS] Dijkstra reference")


def test_decoder():
    valid, path, cost = decode_selected_path(
        "1010", EDGES, "A", "D"
    )

    assert valid
    assert path == ["A", "B", "D"]
    assert cost == 5

    valid, path, cost = decode_selected_path(
        "0101", EDGES, "A", "D"
    )

    assert valid
    assert cost == 9

    for bits in ("0000", "1111", "1000"):
        valid, path, _ = decode_selected_path(
            bits, EDGES, "A", "D"
        )
        assert not valid
        assert path is None

    print("[PASS] Valid and invalid paths")


def test_metrics():
    # Synthetic counts, Qiskit bit order
    counts = {
        "0101": 5,
        "1010": 3,
        "0000": 8,
    }

    result = calculate_metrics(
        counts=counts,
        edges=EDGES,
        source="A",
        target="D",
        optimal_cost=5,
        bit_order="qiskit",
        runtime_seconds=0.25,
    )

    assert result["total_shots"] == 16
    assert result["feasible_shots"] == 8
    assert result["optimal_shots"] == 5

    check(result["feasibility_rate"], 0.5)
    check(result["optimal_solution_probability"], 0.3125)
    check(result["optimality_gap"], 0.0)
    check(result["mean_feasible_cost"], 6.5)

    print("[PASS] Feasibility rate")
    print("[PASS] Optimal-solution probability")
    print("[PASS] Optimality gap")
    print("[PASS] Mean feasible cost")

    return result


def test_special_cases():
    all_optimal = calculate_metrics(
        {"0101": 100},
        EDGES, "A", "D", 5,
    )

    check(all_optimal["feasibility_rate"], 1.0)
    check(all_optimal["optimal_solution_probability"], 1.0)

    no_feasible = calculate_metrics(
        {"0000": 100},
        EDGES, "A", "D", 5,
    )

    check(no_feasible["feasibility_rate"], 0.0)
    assert no_feasible["optimality_gap"] is None

    exhaustive = calculate_metrics(
        {f"{i:04b}": 1 for i in range(16)},
        EDGES, "A", "D", 5,
        bit_order="project",
    )

    assert exhaustive["feasible_shots"] == 2
    assert exhaustive["optimal_shots"] == 1

    print("[PASS] Special and exhaustive cases")


def test_scaling():
    info = scaling_info(NODES, EDGES)

    assert info["nodes"] == 4
    assert info["edges"] == 4
    assert info["variables"] == 4
    assert info["qubits"] == 4
    assert info["state_space_size"] == 16

    print("[PASS] Scaling information")


def test_csv(result):
    row = {
        **result,
        "experiment": "metrics_test",
        "topology": "topology_4",
        "method": "synthetic_test",
        "seed": None,
    }

    output = (
        ROOT / "experiments" / "results"
        / "metrics_test.csv"
    )

    save_results_csv(row, output)

    import csv

    with output.open(
        "r", encoding="utf-8", newline=""
    ) as file:
        reader = csv.DictReader(file)
        records = list(reader)

        assert reader.fieldnames == CSV_FIELDS
        assert len(records) == 1
        check(
            float(records[0]["feasibility_rate"]),
            0.5,
        )

    print("[PASS] CSV schema and values")


def main():
    print("=" * 60)
    print("WEEK 5 - METRICS VALIDATION")
    print("=" * 60)

    test_reference()
    test_decoder()
    result = test_metrics()
    test_special_cases()
    test_scaling()
    test_csv(result)

    print()
    print("Feasibility rate:", result["feasibility_rate"])
    print(
        "Optimal-solution probability:",
        result["optimal_solution_probability"],
    )
    print("Optimality gap:", result["optimality_gap"])

    print()
    print("ALL METRICS VALIDATIONS PASSED!")


if __name__ == "__main__":
    main()
