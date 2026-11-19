
import json
from pathlib import Path

# ==================================================
# WEEK 4 - DECODER EXPECTED CASE VALIDATION
# ==================================================

TEST_FILE = (
    Path(__file__).resolve().parent
    / "decoder_expected_cases.json"
)

EDGES = [
    ("A", "B", 2),
    ("A", "C", 5),
    ("B", "D", 3),
    ("C", "D", 4),
]


def check_flow(bits):
    x0, x1, x2, x3 = bits

    residuals = [
        x0 + x1 - 1,
        x2 - x0,
        x3 - x1,
        x2 + x3 - 1,
    ]

    return all(r == 0 for r in residuals)


def get_path(bits):
    if not check_flow(bits):
        return None

    selected = [
        edge for bit, edge in zip(bits, EDGES)
        if bit == 1
    ]

    path = ["A"]
    current = "A"
    used = set()

    while current != "D":
        outgoing = [
            (i, edge)
            for i, edge in enumerate(selected)
            if edge[0] == current and i not in used
        ]

        if len(outgoing) != 1:
            return None

        index, edge = outgoing[0]
        used.add(index)
        current = edge[1]
        path.append(current)

        if len(path) > len(EDGES) + 1:
            return None

    if len(used) != len(selected):
        return None

    return path


def validate_cases():
    with open(TEST_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["topology"] == "topology_4"
    assert data["source"] == "A"
    assert data["destination"] == "D"
    assert data["qiskit_bit_order"] == "q3q2q1q0"

    edge_names = [f"{u}->{v}" for u, v, _ in EDGES]

    assert data["project_bit_order"] == edge_names

    for i, edge_name in enumerate(edge_names):
        assert data["qubit_mapping"][f"q{i}"] == edge_name

    cases = data["test_cases"]
    assert len(cases) == 8
    assert len({tc["id"] for tc in cases}) == len(cases)

    print("=" * 65)
    print("DECODER EXPECTED CASE VALIDATION")
    print("=" * 65)

    for tc in cases:
        qiskit_bits = tc["qiskit_bitstring"]

        assert len(qiskit_bits) == 4
        assert set(qiskit_bits) <= {"0", "1"}

        # Qiskit: q3 q2 q1 q0
        # Project: x0 x1 x2 x3
        project_bits = qiskit_bits[::-1]

        assert (
            project_bits == tc["expected_project_bitstring"]
        ), f"{tc['id']}: bit ordering mismatch"

        bits = tuple(int(x) for x in project_bits)

        cost = sum(
            bit * weight
            for bit, (_, _, weight) in zip(bits, EDGES)
        )

        valid = check_flow(bits)
        path = get_path(bits)

        assert cost == tc["expected_cost"], (
            f"{tc['id']}: cost mismatch"
        )

        assert valid == tc["expected_valid"], (
            f"{tc['id']}: validity mismatch"
        )

        assert path == tc["expected_path"], (
            f"{tc['id']}: path mismatch"
        )

        print(
            f"[PASS] {tc['id']} | "
            f"Qiskit={qiskit_bits} | "
            f"Project={project_bits} | "
            f"Valid={valid} | "
            f"Cost={cost} | "
            f"Path={path}"
        )

    print()
    print(f"[PASS] All {len(cases)} decoder cases verified!")


if __name__ == "__main__":
    validate_cases()
