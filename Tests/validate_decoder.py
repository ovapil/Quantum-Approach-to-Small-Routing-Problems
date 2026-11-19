import sys
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
)

SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(
    0,
    str(SRC_DIR)
)


from topology import create_test_topology

from binary_encoding import (
    create_edge_mapping
)

from decoder import (
    qiskit_to_project_bitstring,
    decode_bitstring,
)


def main():

    graph = create_test_topology()

    mapping = create_edge_mapping(
        graph
    )

    # Qiskit displays:
    #
    # q3 q2 q1 q0
    #
    # Project expects:
    #
    # x0 x1 x2 x3
    #
    # Therefore project 1010
    # appears from Qiskit as 0101.

    qiskit_bitstring = "0101"

    project_bitstring = (
        qiskit_to_project_bitstring(
            qiskit_bitstring
        )
    )

    print(
        "Qiskit bitstring:",
        qiskit_bitstring
    )

    print(
        "Project bitstring:",
        project_bitstring
    )

    assert (
        project_bitstring
        == "1010"
    )

    result = decode_bitstring(
        qiskit_bitstring,
        graph,
        mapping,
        source="A",
        destination="D"
    )

    assert (
        result["selected_edges"]
        == [
            ("A", "B"),
            ("B", "D")
        ]
    )

    assert (
        result["cost"]
        == 5
    )

    assert (
        result["feasible"]
        is True
    )

    print(
        "[PASS] Bit ordering"
    )

    print(
        "[PASS] Selected edges"
    )

    print(
        "[PASS] Cost = 5"
    )

    print(
        "[PASS] Feasible route"
    )


if __name__ == "__main__":
    main()