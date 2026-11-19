import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from topology import create_test_topology

from dijkstra_solver import solve_dijkstra

from binary_encoding import (
    create_edge_mapping,
    calculate_objective_cost,
)

from flow_constraints import (
    calculate_node_flows,
)

from qubo_builder import (
    build_qubo,
    calculate_qubo_energy,
)

from exact_solver import (
    generate_bitstrings,
    solve_qubo_exact,
)

def calculate_direct_flow_penalty(
    graph,
    bitstring,
    mapping,
    source,
    destination
):

    selected_edges = []

    for index, bit in enumerate(bitstring):
        if bit == "1":
            selected_edges.append(
                mapping[index]["edge"]
            )

    flows = calculate_node_flows(
        graph,
        selected_edges
    )

    penalty_value = 0

    for node in graph.nodes:

        actual_balance = (
            flows[node]["out"]
            - flows[node]["in"]
        )

        if node == source:
            expected_balance = 1

        elif node == destination:
            expected_balance = -1

        else:
            expected_balance = 0

        violation = (
            actual_balance
            - expected_balance
        )

        penalty_value += (
            violation ** 2
        )

    return penalty_value

def test_qubo_coefficients(
    graph,
    mapping,
    source,
    destination
):
    penalty = 3.0

    qubo = build_qubo(
        graph,
        mapping,
        source,
        destination,
        penalty
    )

    expected_constant = 6.0

    expected_linear = {
        0: 2.0,
        1: 5.0,
        2: 3.0,
        3: 4.0,
    }

    expected_quadratic = {
        (0, 1): 6.0,
        (0, 2): -6.0,
        (1, 3): -6.0,
        (2, 3): 6.0,
    }

    passed = (
        qubo["constant"]
        == expected_constant
        and qubo["linear"]
        == expected_linear
        and qubo["quadratic"]
        == expected_quadratic
    )

    print("\nTEST 1 - QUBO COEFFICIENTS")

    if passed:
        print("[PASS] QUBO coefficients are correct")
    else:
        print("[FAIL] QUBO coefficients mismatch")

        print(
            "Expected constant:",
            expected_constant
        )

        print(
            "Actual constant:",
            qubo["constant"]
        )

        print(
            "Expected linear:",
            expected_linear
        )

        print(
            "Actual linear:",
            qubo["linear"]
        )

        print(
            "Expected quadratic:",
            expected_quadratic
        )

        print(
            "Actual quadratic:",
            qubo["quadratic"]
        )

    return passed

def test_energy_equivalence(
    graph,
    mapping,
    source,
    destination
):
    penalty = 3.0

    qubo = build_qubo(
        graph,
        mapping,
        source,
        destination,
        penalty
    )

    print(
        "\nTEST 2 - ENERGY EQUIVALENCE"
    )

    all_passed = True

    for bitstring in generate_bitstrings(
        len(mapping)
    ):

        objective_cost = (
            calculate_objective_cost(
                bitstring,
                mapping
            )
        )

        direct_penalty = (
            calculate_direct_flow_penalty(
                graph,
                bitstring,
                mapping,
                source,
                destination
            )
        )

        direct_energy = (
            objective_cost
            + penalty * direct_penalty
        )

        qubo_energy = (
            calculate_qubo_energy(
                bitstring,
                mapping,
                qubo
            )
        )

        if abs(
            direct_energy
            - qubo_energy
        ) > 1e-9:

            all_passed = False

            print(
                f"[FAIL] {bitstring}: "
                f"direct={direct_energy}, "
                f"QUBO={qubo_energy}"
            )

    if all_passed:
        print(
            "[PASS] All 16 bitstrings "
            "match direct objective + penalty"
        )

    return all_passed

def test_known_energies(
    graph,
    mapping,
    source,
    destination
):
    penalty = 3.0

    qubo = build_qubo(
        graph,
        mapping,
        source,
        destination,
        penalty
    )

    expected = {
        "0000": 6.0,
        "1010": 5.0,
        "0101": 9.0,
        "1111": 20.0,
    }

    print(
        "\nTEST 3 - KNOWN QUBO ENERGIES"
    )

    all_passed = True

    for bitstring, expected_energy in (
        expected.items()
    ):

        actual_energy = (
            calculate_qubo_energy(
                bitstring,
                mapping,
                qubo
            )
        )

        if abs(
            actual_energy
            - expected_energy
        ) <= 1e-9:

            print(
                f"[PASS] {bitstring}: "
                f"{actual_energy}"
            )

        else:
            all_passed = False

            print(
                f"[FAIL] {bitstring}: "
                f"expected={expected_energy}, "
                f"actual={actual_energy}"
            )

    return all_passed

def test_exact_optimum(
    graph,
    mapping,
    source,
    destination
):
    penalty = 3.0

    results = solve_qubo_exact(
        graph,
        mapping,
        source,
        destination,
        penalty
    )

    best = results[0]

    print(
        "\nTEST 4 - EXACT QUBO OPTIMUM"
    )

    passed = (
        best["bitstring"] == "1010"
        and best["route_cost"] == 5
        and best["feasible"] is True
        and abs(
            best["energy"] - 5.0
        ) <= 1e-9
    )

    if passed:
        print(
            "[PASS] Global optimum = 1010"
        )

        print(
            "       Route = A -> B -> D"
        )

        print(
            "       Cost = 5"
        )

    else:
        print(
            "[FAIL] Unexpected QUBO optimum"
        )

        print(best)

    return passed

def test_qubo_vs_dijkstra(
    graph,
    mapping,
    source,
    destination
):
    penalty = 3.0

    results = solve_qubo_exact(
        graph,
        mapping,
        source,
        destination,
        penalty
    )

    best = results[0]

    dijkstra_path, dijkstra_cost = (
        solve_dijkstra(
            graph,
            source,
            destination
        )
    )

    expected_edges = list(
        zip(
            dijkstra_path[:-1],
            dijkstra_path[1:]
        )
    )

    passed = (
        best["selected_edges"]
        == expected_edges
        and best["route_cost"]
        == dijkstra_cost
        and best["feasible"] is True
    )

    print(
        "\nTEST 5 - QUBO VS DIJKSTRA"
    )

    if passed:
        print(
            "[PASS] Exact QUBO optimum "
            "matches Dijkstra"
        )

        print(
            f"       Path: "
            f"{' -> '.join(dijkstra_path)}"
        )

        print(
            f"       Cost: {dijkstra_cost}"
        )

    else:
        print(
            "[FAIL] QUBO and Dijkstra mismatch"
        )

    return passed

def test_penalty_threshold(
    graph,
    mapping,
    source,
    destination
):
    print(
        "\nTEST 6 - PENALTY THRESHOLD"
    )

    results_low = solve_qubo_exact(
        graph,
        mapping,
        source,
        destination,
        penalty=2.0
    )

    best_low = results_low[0]

    low_pass = (
        best_low["bitstring"] == "0000"
        and best_low["feasible"] is False
    )

    results_boundary = solve_qubo_exact(
        graph,
        mapping,
        source,
        destination,
        penalty=2.5
    )

    energies_boundary = {
        result["bitstring"]:
        result["energy"]
        for result in results_boundary
    }

    boundary_pass = (
        abs(
            energies_boundary["0000"]
            - 5.0
        ) <= 1e-9
        and
        abs(
            energies_boundary["1010"]
            - 5.0
        ) <= 1e-9
    )

    results_safe = solve_qubo_exact(
        graph,
        mapping,
        source,
        destination,
        penalty=3.0
    )

    best_safe = results_safe[0]

    safe_pass = (
        best_safe["bitstring"] == "1010"
        and best_safe["feasible"] is True
    )

    if low_pass:
        print(
            "[PASS] A=2.0: "
            "invalid 0000 wins"
        )
    else:
        print(
            "[FAIL] Unexpected result at A=2.0"
        )

    if boundary_pass:
        print(
            "[PASS] A=2.5: "
            "0000 and 1010 tie at energy 5"
        )
    else:
        print(
            "[FAIL] Unexpected boundary "
            "at A=2.5"
        )

    if safe_pass:
        print(
            "[PASS] A=3.0: "
            "valid 1010 becomes optimum"
        )
    else:
        print(
            "[FAIL] Unexpected result at A=3.0"
        )

    return (
        low_pass
        and boundary_pass
        and safe_pass
    )

def run_validation():

    graph = create_test_topology()

    source = "A"
    destination = "D"

    mapping = create_edge_mapping(
        graph
    )

    print("=" * 65)
    print("QUBO VALIDATION")
    print("=" * 65)

    results = []

    results.append(
        test_qubo_coefficients(
            graph,
            mapping,
            source,
            destination
        )
    )

    results.append(
        test_energy_equivalence(
            graph,
            mapping,
            source,
            destination
        )
    )

    results.append(
        test_known_energies(
            graph,
            mapping,
            source,
            destination
        )
    )

    results.append(
        test_exact_optimum(
            graph,
            mapping,
            source,
            destination
        )
    )

    results.append(
        test_qubo_vs_dijkstra(
            graph,
            mapping,
            source,
            destination
        )
    )

    results.append(
        test_penalty_threshold(
            graph,
            mapping,
            source,
            destination
        )
    )

    passed = sum(results)
    total = len(results)

    print("\n" + "=" * 65)
    print("FINAL RESULT")
    print("=" * 65)

    print(
        f"Passed: {passed}/{total}"
    )

    if passed == total:

        print(
            "\nAll QUBO validation tests passed!"
        )

        print(
            "[PASS] QUBO formulation"
        )

        print(
            "[PASS] Coefficient expansion"
        )

        print(
            "[PASS] Energy calculation"
        )

        print(
            "[PASS] Exact optimization"
        )

        print(
            "[PASS] Dijkstra comparison"
        )

        print(
            "[PASS] Penalty behavior"
        )

        return True

    print(
        f"\n{total - passed} "
        "validation test(s) failed."
    )

    return False

if __name__ == "__main__":

    success = run_validation()

    if not success:
        sys.exit(1)