import json
from pathlib import Path
from itertools import product

WEIGHTS = [2, 5, 3, 4]
PENALTY_A = 10  # Gia tri penalty thu nghiem

def evaluate(bits):
    x0, x1, x2, x3 = bits

    # Shortest-path objective
    cost = (
        2 * x0
        + 5 * x1
        + 3 * x2
        + 4 * x3
    )

    # Flow conservation residuals
    residuals = {
        "A": x0 + x1 - 1,
        "B": x2 - x0,
        "C": x3 - x1,
        "D": x2 + x3 - 1,
    }

    # Penalty calculation
    penalty = PENALTY_A * sum(
        r ** 2 for r in residuals.values()
    )

    # Total QUBO energy
    energy = cost + penalty

    # Valid solution if all constraints satisfied
    valid = all(
        r == 0 for r in residuals.values()
    )

    return cost, penalty, energy, valid

def validate_all_bitstrings():
    results = []

    print("=" * 55)
    print("QUBO ENERGY VALIDATION")
    print("=" * 55)

    print(f"Penalty A = {PENALTY_A}")
    print(
        f"{'Bits':<8}"
        f"{'Cost':<8}"
        f"{'Penalty':<10}"
        f"{'Energy':<10}"
        f"{'Valid':<8}"
    )
    print("-" * 55)

    for bits in product((0, 1), repeat=4):
        bitstring = "".join(map(str, bits))

        cost, penalty, energy, valid = evaluate(bits)

        results.append(
            (bitstring, energy, valid)
        )

        print(
            f"{bitstring:<8}"
            f"{cost:<8}"
            f"{penalty:<10}"
            f"{energy:<10}"
            f"{str(valid):<8}"
        )

    # Find the minimum energy
    best = min(
        results,
        key=lambda item: item[1]
    )

    print()
    print("Best solution:", best)

    assert best == ("1010", 5, True)

    # Expected valid solutions
    valid_solutions = {
        bits for bits, _, valid in results if valid
    }

    assert valid_solutions == {"1010", "0101"}

    print("[PASS] Optimal QUBO solution verified!")
    print("[PASS] Valid bitstrings verified!")

def get_expected_coefficients():
    a = PENALTY_A

    constant = 2 * a

    linear = {
        "x0": 2,
        "x1": 5,
        "x2": 3,
        "x3": 4,
    }

    quadratic = {
        "x0*x1": 2 * a,
        "x0*x2": -2 * a,
        "x1*x3": -2 * a,
        "x2*x3": 2 * a,
    }

    return constant, linear, quadratic


def print_expected_coefficients():
    constant, linear, quadratic = (
        get_expected_coefficients()
    )

    print()
    print("=" * 55)
    print("EXPECTED QUBO COEFFICIENTS")
    print("=" * 55)

    print("Constant:", constant)

    print("\nLinear coefficients:")
    for name, value in linear.items():
        print(f"  {name}: {value}")

    print("\nQuadratic coefficients:")
    for name, value in quadratic.items():
        print(f"  {name}: {value}")

def get_expected_qubo_matrix():
    a = PENALTY_A

    # For symmetric Q:
    # Q[i][j] = quadratic_coefficient / 2
    # because x^T Q x counts off-diagonal pairs twice.

    q = [
        [2,  a, -a,  0],
        [a,  5,  0, -a],
        [-a, 0,  3,  a],
        [0, -a,  a,  4],
    ]

    constant = 2 * a

    return q, constant


def calculate_matrix_energy(bits, q, constant):
    energy = constant

    for i in range(4):
        for j in range(4):
            energy += bits[i] * q[i][j] * bits[j]

    return energy


def validate_qubo_matrix():
    q, constant = get_expected_qubo_matrix()

    print()
    print("=" * 55)
    print("EXPECTED SYMMETRIC QUBO MATRIX")
    print("=" * 55)

    print(f"Penalty A = {PENALTY_A}")
    print(f"Constant = {constant}")
    print()

    print("        x0    x1    x2    x3")
    for i, row in enumerate(q):
        values = "".join(
            f"{value:6}" for value in row
        )
        print(f"x{i}  {values}")

    # Compare two equivalent QUBO formulations:
    # 1. Objective + squared flow penalties
    # 2. Constant + x^T Q x

    for bits in product((0, 1), repeat=4):
        _, _, original_energy, _ = evaluate(bits)

        matrix_energy = calculate_matrix_energy(
            bits, q, constant
        )

        bitstring = "".join(map(str, bits))

        assert original_energy == matrix_energy, (
            f"Energy mismatch for {bitstring}: "
            f"original={original_energy}, "
            f"matrix={matrix_energy}"
        )

    print()
    print(
        "[PASS] QUBO matrix matches "
        "all 16 original energies!"
    )

def validate_penalty_values():
    candidates = [1, 2, 2.5, 3, 5, 10]

    print()
    print("=" * 55)
    print("PENALTY A VALIDATION")
    print("=" * 55)

    for a in candidates:
        results = []

        for bits in product((0, 1), repeat=4):
            bitstring = "".join(map(str, bits))

            x0, x1, x2, x3 = bits

            cost = sum(
                w * x for w, x in zip(WEIGHTS, bits)
            )

            residuals = [
                x0 + x1 - 1,
                x2 - x0,
                x3 - x1,
                x2 + x3 - 1,
            ]

            violation = sum(r ** 2 for r in residuals)
            energy = cost + a * violation
            valid = violation == 0

            results.append((bitstring, energy, valid))

        min_energy = min(r[1] for r in results)

        winners = [
            r for r in results
            if r[1] == min_energy
        ]

        all_valid = all(r[2] for r in winners)
        unique_optimal = (
            len(winners) == 1
            and winners[0][0] == "1010"
        )

        print(
            f"A={a:<5} "
            f"Min Energy={min_energy:<6} "
            f"Winners={[r[0] for r in winners]} "
            f"All Valid={all_valid}"
        )

        if a > 2.5:
            assert unique_optimal

    print(
        "[PASS] All tested A > 2.5 "
        "produce the expected unique optimum!"
    )

def validate_expected_test_cases():
    test_file = (
        Path(__file__).resolve().parent
        / "qubo_test_cases.json"
    )

    with open(test_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["topology"] == "topology_4"
    assert data["bit_order"] == [
        "A->B", "A->C", "B->D", "C->D"
    ]
    assert data["penalty_A"] == PENALTY_A

    print()
    print("=" * 55)
    print("EXPECTED QUBO TEST CASE VALIDATION")
    print("=" * 55)

    test_cases = data["test_cases"]
    assert len(test_cases) == 8

    for tc in test_cases:
        bitstring = tc["bitstring"]

        assert len(bitstring) == 4
        assert set(bitstring) <= {"0", "1"}

        bits = tuple(int(bit) for bit in bitstring)

        cost, penalty, energy, valid = evaluate(bits)

        assert cost == tc["expected_cost"], (
            f"{tc['id']}: Cost mismatch"
        )

        assert penalty == tc["expected_penalty"], (
            f"{tc['id']}: Penalty mismatch"
        )

        assert energy == tc["expected_energy"], (
            f"{tc['id']}: Energy mismatch"
        )

        assert valid == tc["expected_valid"], (
            f"{tc['id']}: Validity mismatch"
        )

        print(
            f"[PASS] {tc['id']} | "
            f"Bits={bitstring} | "
            f"Energy={energy} | "
            f"Valid={valid}"
        )

    print()
    print(
        f"[PASS] All {len(test_cases)} "
        "expected test cases verified!"
    )

def get_expected_ising_coefficients():
    q, qubo_constant = get_expected_qubo_matrix()

    # Ising form:
    # E(z) = offset + sum(h_i * z_i)
    #                + sum(J_ij * z_i * z_j)

    n = len(q)

    # Local field coefficients
    h = [
        -q[i][i] / 2
        - sum(q[i][j] for j in range(n) if j != i) / 2
        for i in range(n)
    ]

    # Pairwise interaction coefficients
    # Q is symmetric, so J_ij = Q_ij / 2.
    J = {
        (i, j): q[i][j] / 2
        for i in range(n)
        for j in range(i + 1, n)
        if q[i][j] != 0
    }

    # Constant offset in Ising formulation
    offset = (
        qubo_constant
        + sum(q[i][i] for i in range(n)) / 2
        + sum(
            q[i][j]
            for i in range(n)
            for j in range(i + 1, n)
        ) / 2
    )

    return offset, h, J


def calculate_ising_energy(spins, offset, h, J):
    energy = offset

    # Local field terms
    for i in range(len(spins)):
        energy += h[i] * spins[i]

    # Pairwise interactions
    for (i, j), coefficient in J.items():
        energy += (
            coefficient * spins[i] * spins[j]
        )

    return energy


def validate_qubo_to_ising():
    offset, h, J = get_expected_ising_coefficients()

    print()
    print("=" * 55)
    print("QUBO TO ISING VALIDATION")
    print("=" * 55)

    print(f"Penalty A = {PENALTY_A}")
    print(f"Ising constant offset = {offset}")

    print("\nLocal field coefficients:")
    for i, value in enumerate(h):
        print(f"  h{i}: {value}")

    print("\nInteraction coefficients:")
    for (i, j), value in J.items():
        print(f"  J{i}{j}: {value}")

    # Expected values for topology 4
    assert offset == 2 * PENALTY_A + 7
    assert h == [-1.0, -2.5, -1.5, -2.0]

    print()
    print(
        f"{'Bits':<8}"
        f"{'Spins':<23}"
        f"{'QUBO':<10}"
        f"{'Ising':<10}"
    )
    print("-" * 55)

    count = 0

    for bits in product((0, 1), repeat=4):
        bitstring = "".join(map(str, bits))

        # Mapping: x = (1 - z) / 2
        # Therefore: z = 1 - 2*x
        spins = tuple(1 - 2 * x for x in bits)

        _, _, qubo_energy, _ = evaluate(bits)

        ising_energy = calculate_ising_energy(
            spins, offset, h, J
        )

        assert abs(qubo_energy - ising_energy) < 1e-9, (
            f"Energy mismatch for {bitstring}: "
            f"QUBO={qubo_energy}, "
            f"Ising={ising_energy}"
        )

        print(
            f"{bitstring:<8}"
            f"{str(spins):<23}"
            f"{qubo_energy:<10}"
            f"{ising_energy:<10}"
        )

        count += 1

    print()
    print(
        f"[PASS] QUBO and Ising energies "
        f"match for all {count} bitstrings!"
    )

def main():
    validate_all_bitstrings()
    print_expected_coefficients()
    validate_qubo_matrix()
    validate_penalty_values()
    validate_expected_test_cases()
    validate_qubo_to_ising()

    print()
    print("=" * 55)
    print("ALL QUBO VALIDATIONS PASSED!")
    print("=" * 55)


if __name__ == "__main__":
    main()
