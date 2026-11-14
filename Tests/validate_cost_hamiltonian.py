
from itertools import product

from validate_qubo_energy import (
    PENALTY_A,
    evaluate,
    get_expected_ising_coefficients,
)


# ==================================================
# WEEK 4 - COST HAMILTONIAN VALIDATION
# Topology: 4 nodes
# Bit order: [A->B, A->C, B->D, C->D]
# ==================================================


EXPECTED_H = [-1.0, -2.5, -1.5, -2.0]

EXPECTED_J = {
    (0, 1): 5.0,
    (0, 2): -5.0,
    (1, 3): -5.0,
    (2, 3): 5.0,
}


# ==================================================
# 1. BUILD EXPECTED COST HAMILTONIAN
# ==================================================

def build_cost_hamiltonian():
    offset, h, J = get_expected_ising_coefficients()

    assert PENALTY_A == 10, (
        "Expected coefficients assume PENALTY_A = 10"
    )

    assert offset == 27.0
    assert h == EXPECTED_H
    assert J == EXPECTED_J

    return offset, h, J


# ==================================================
# 2. CALCULATE HAMILTONIAN ENERGY
# ==================================================

def calculate_hamiltonian_energy(bits, offset, h, J):
    # Binary to spin:
    # x=0 -> z=+1
    # x=1 -> z=-1

    spins = tuple(1 - 2 * bit for bit in bits)

    energy = offset

    # Single-qubit Pauli-Z contributions
    for i, coefficient in enumerate(h):
        energy += coefficient * spins[i]

    # Two-qubit Pauli-Z interactions
    for (i, j), coefficient in J.items():
        energy += (
            coefficient * spins[i] * spins[j]
        )

    return energy


# ==================================================
# 3. VALIDATE ALL 16 BITSTRINGS
# ==================================================

def validate_hamiltonian_energy():
    offset, h, J = build_cost_hamiltonian()

    print("=" * 65)
    print("COST HAMILTONIAN VALIDATION")
    print("=" * 65)

    print(f"Penalty A = {PENALTY_A}")
    print(f"Constant offset = {offset}")

    print("\nLocal fields:")
    for i, coefficient in enumerate(h):
        print(f"h{i} = {coefficient}")

    print("\nInteraction coefficients:")
    for (i, j), coefficient in J.items():
        print(f"J{i}{j} = {coefficient}")

    print()
    print(
        f"{'Bits':<10}"
        f"{'QUBO':<12}"
        f"{'Hamiltonian':<16}"
        f"{'Match':<10}"
    )
    print("-" * 65)

    count = 0

    for bits in product((0, 1), repeat=4):
        bitstring = "".join(map(str, bits))

        # Reference energy from Week 3
        _, _, qubo_energy, _ = evaluate(bits)

        # Cost Hamiltonian energy
        hamiltonian_energy = (
            calculate_hamiltonian_energy(
                bits, offset, h, J
            )
        )

        match = abs(
            qubo_energy - hamiltonian_energy
        ) < 1e-9

        assert match, (
            f"Energy mismatch at {bitstring}: "
            f"QUBO={qubo_energy}, "
            f"Hamiltonian={hamiltonian_energy}"
        )

        print(
            f"{bitstring:<10}"
            f"{qubo_energy:<12}"
            f"{hamiltonian_energy:<16}"
            f"{str(match):<10}"
        )

        count += 1

    assert count == 16

    print()
    print(
        f"[PASS] Hamiltonian energies match "
        f"QUBO for all {count} bitstrings!"
    )


# ==================================================
# 4. CHECK EXPECTED OPTIMAL SOLUTION
# ==================================================

def validate_optimal_solution():
    offset, h, J = build_cost_hamiltonian()

    results = []

    for bits in product((0, 1), repeat=4):
        bitstring = "".join(map(str, bits))

        energy = calculate_hamiltonian_energy(
            bits, offset, h, J
        )

        results.append((bitstring, energy))

    best = min(results, key=lambda item: item[1])

    assert best[0] == "1010"
    assert abs(best[1] - 5) < 1e-9

    print()
    print("Optimal bitstring:", best[0])
    print("Minimum Hamiltonian energy:", best[1])

    print("[PASS] Optimal Hamiltonian solution verified!")


# ==================================================
# 5. MAIN
# ==================================================

def main():
    validate_hamiltonian_energy()
    validate_optimal_solution()

    print()
    print("=" * 65)
    print("ALL COST HAMILTONIAN VALIDATIONS PASSED!")
    print("=" * 65)


if __name__ == "__main__":
    main()
