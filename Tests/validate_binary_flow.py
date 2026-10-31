import json
import sys
from pathlib import Path

import networkx as nx


# ============================================================
# Setup project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


# ============================================================
# Import project modules
# ============================================================

from topology import create_test_topology

from binary_encoding import (
    create_edge_mapping,
    bitstring_to_selected_edges,
    calculate_objective_cost,
)

from flow_constraints import check_feasibility


# ============================================================
# Load test cases
# ============================================================

def load_test_cases():
    test_file = (
        PROJECT_ROOT
        / "Tests"
        / "qubo_test_cases.json"
    )

    with test_file.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# ============================================================
# Get mapping bit order
# ============================================================

def get_mapping_bit_order(mapping):
    """
    Convert edge mapping thành danh sách:

    [
        "A->B",
        "A->C",
        ...
    ]

    để đối chiếu với bit_order trong JSON test cases.
    """

    bit_order = []

    for index in range(len(mapping)):
        source, destination = mapping[index]["edge"]

        bit_order.append(
            f"{source}->{destination}"
        )

    return bit_order


# ============================================================
# Extra cycle stress test
# ============================================================

def test_extra_cycle_detection():
    """
    Stress test để kiểm tra trường hợp:

        A -> B -> D

    là route chính hợp lệ,

    nhưng đồng thời có thêm cycle:

        E -> F -> E

    Flow conservation vẫn có thể thỏa tại E và F:

        out - in = 0

    Tuy nhiên nghiệm này KHÔNG phải một simple
    source-to-destination path.

    check_path_structure() phải loại nghiệm này.
    """

    graph = nx.DiGraph()

    # Route chính
    graph.add_edge(
        "A",
        "B",
        weight=2
    )

    graph.add_edge(
        "B",
        "D",
        weight=3
    )

    # Cycle thừa
    graph.add_edge(
        "E",
        "F",
        weight=1
    )

    graph.add_edge(
        "F",
        "E",
        weight=1
    )

    mapping = create_edge_mapping(graph)

    print("\n" + "=" * 60)
    print("EXTRA CYCLE STRESS TEST")
    print("=" * 60)

    print("\nEdge mapping:")

    for index in range(len(mapping)):
        source, destination = mapping[index]["edge"]

        print(
            f"bit {index}: "
            f"{source}->{destination}"
        )

    # create_edge_mapping() đang sort edge.
    #
    # Expected order:
    #
    # bit 0 -> A->B
    # bit 1 -> B->D
    # bit 2 -> E->F
    # bit 3 -> F->E
    #
    # 1111:
    #
    # A -> B -> D
    #
    # +
    #
    # E -> F -> E
    #
    # Route chính hợp lệ nhưng có cycle thừa.
    bitstring = "1111"

    selected_edges = bitstring_to_selected_edges(
        bitstring,
        mapping
    )

    actual_valid, actual_reason = check_feasibility(
        graph,
        bitstring,
        mapping,
        source="A",
        destination="D"
    )

    print(f"\nBitstring: {bitstring}")
    print(f"Selected edges: {selected_edges}")
    print(f"Valid: {actual_valid}")
    print(f"Reason: {actual_reason}")

    if actual_valid is False:
        print(
            "[PASS] Extra cycle correctly rejected"
        )

        return True

    print(
        "[FAIL] Extra cycle was incorrectly accepted"
    )

    return False


# ============================================================
# Main validation
# ============================================================

def run_validation():
    test_data = load_test_cases()

    graph = create_test_topology()
    mapping = create_edge_mapping(graph)

    source = test_data["source"]
    destination = test_data["destination"]

    expected_bit_order = test_data["bit_order"]
    actual_bit_order = get_mapping_bit_order(
        mapping
    )

    print("=" * 60)
    print(
        "BINARY ENCODING + "
        "FLOW VALIDATION"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Validate bit order
    # --------------------------------------------------------

    print("\nChecking bit order...")

    if actual_bit_order != expected_bit_order:
        print("[FAIL] Bit order mismatch")

        print(
            f"Expected: {expected_bit_order}"
        )

        print(
            f"Actual:   {actual_bit_order}"
        )

        return False

    print("[PASS] Bit order matches")
    print(actual_bit_order)

    # --------------------------------------------------------
    # Run JSON test cases
    # --------------------------------------------------------

    test_cases = test_data["test_cases"]

    total = len(test_cases)
    passed = 0

    for test_case in test_cases:
        test_id = test_case["id"]
        bitstring = test_case["bitstring"]

        expected_cost = (
            test_case["expected_cost"]
        )

        expected_valid = (
            test_case["expected_valid"]
        )

        # Decode bitstring
        selected_edges = (
            bitstring_to_selected_edges(
                bitstring,
                mapping
            )
        )

        # Calculate objective cost
        actual_cost = (
            calculate_objective_cost(
                bitstring,
                mapping
            )
        )

        # Check feasibility
        (
            actual_valid,
            actual_reason
        ) = check_feasibility(
            graph,
            bitstring,
            mapping,
            source,
            destination
        )

        cost_pass = (
            actual_cost
            == expected_cost
        )

        valid_pass = (
            actual_valid
            == expected_valid
        )

        test_pass = (
            cost_pass
            and valid_pass
        )

        print("\n" + "-" * 60)

        print(
            f"{test_id}: "
            f"{bitstring}"
        )

        print(
            f"Selected edges: "
            f"{selected_edges}"
        )

        print(
            "Cost: "
            f"expected={expected_cost}, "
            f"actual={actual_cost}"
        )

        print(
            "Valid: "
            f"expected={expected_valid}, "
            f"actual={actual_valid}"
        )

        print(
            f"Reason: {actual_reason}"
        )

        if test_pass:
            print("[PASS]")
            passed += 1

        else:
            print("[FAIL]")

            if not cost_pass:
                print(
                    "  -> Objective cost mismatch"
                )

            if not valid_pass:
                print(
                    "  -> Feasibility mismatch"
                )

    # --------------------------------------------------------
    # Normal test summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(
        f"Passed: {passed}/{total}"
    )

    if passed != total:
        print(
            f"{total - passed} "
            "test(s) failed."
        )

        return False

    print(
        "All binary encoding and "
        "flow-conservation tests passed!"
    )

    # --------------------------------------------------------
    # Extra path-structure stress test
    # --------------------------------------------------------

    cycle_test_passed = (
        test_extra_cycle_detection()
    )

    if not cycle_test_passed:
        return False

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("FINAL VALIDATION RESULT")
    print("=" * 60)

    print(
        "[PASS] Binary encoding"
    )

    print(
        "[PASS] Objective cost"
    )

    print(
        "[PASS] Flow conservation"
    )

    print(
        "[PASS] Path structure"
    )

    print(
        "[PASS] Extra cycle detection"
    )

    print(
        "\nAll Week 2 validation tests passed!"
    )

    return True


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    success = run_validation()

    if not success:
        sys.exit(1)