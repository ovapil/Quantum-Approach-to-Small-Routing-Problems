
from itertools import product

from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector

from validate_qubo_energy import (
    PENALTY_A,
    evaluate,
    get_expected_ising_coefficients,
)

# ==================================================
# WEEK 4 - QISKIT COST HAMILTONIAN & BIT ORDER
# Project bits: x0 x1 x2 x3
# Qiskit strings: q3 q2 q1 q0
# ==================================================

NUM_QUBITS = 4

BIT_ORDER = [
    "A->B",
    "A->C",
    "B->D",
    "C->D",
]


def pauli_label(qubit_indices):
    """Create a Qiskit Pauli string."""
    chars = ["I"] * NUM_QUBITS

    for index in qubit_indices:
        chars[NUM_QUBITS - 1 - index] = "Z"

    return "".join(chars)


def build_qiskit_hamiltonian():
    assert PENALTY_A == 10

    offset, h, J = get_expected_ising_coefficients()

    terms = [("I" * NUM_QUBITS, offset)]

    for i, coefficient in enumerate(h):
        terms.append(
            (pauli_label([i]), coefficient)
        )

    for (i, j), coefficient in J.items():
        terms.append(
            (pauli_label([i, j]), coefficient)
        )

    return SparsePauliOp.from_list(terms)


def project_to_qiskit(bits):
    return bits[::-1]


def qiskit_to_project(bits):
    return bits.replace(" ", "")[::-1]


def validate_pauli_labels():
    print("=" * 60)
    print("QISKIT PAULI LABEL VALIDATION")
    print("=" * 60)

    expected = {
        (0,): "IIIZ",
        (1,): "IIZI",
        (2,): "IZII",
        (3,): "ZIII",
        (0, 1): "IIZZ",
        (0, 2): "IZIZ",
        (1, 3): "ZIZI",
        (2, 3): "ZZII",
    }

    for indices, expected_label in expected.items():
        actual = pauli_label(indices)

        assert actual == expected_label

        print(
            f"Qubits {indices}: {actual} [PASS]"
        )

    print("[PASS] Pauli labels verified!")


def validate_bit_order():
    print()
    print("=" * 60)
    print("QISKIT BIT ORDER VALIDATION")
    print("=" * 60)

    for bits in product((0, 1), repeat=NUM_QUBITS):
        project_bits = "".join(map(str, bits))
        qiskit_bits = project_to_qiskit(project_bits)

        # Prepare the same bit configuration in a circuit
        circuit = QuantumCircuit(NUM_QUBITS)

        for i, bit in enumerate(bits):
            if bit == 1:
                circuit.x(i)

        state = Statevector.from_instruction(circuit)
        probabilities = state.probabilities_dict()

        assert len(probabilities) == 1

        measured_bits = next(iter(probabilities))

        assert abs(
            probabilities[measured_bits] - 1.0
        ) < 1e-9

        assert measured_bits == qiskit_bits
        assert qiskit_to_project(measured_bits) == project_bits

        print(
            f"Project={project_bits} | "
            f"Qiskit={measured_bits} | PASS"
        )

    print("[PASS] All 16 bit orders verified!")


def validate_qiskit_hamiltonian():
    hamiltonian = build_qiskit_hamiltonian()

    print()
    print("=" * 60)
    print("QISKIT SPARSE PAULI HAMILTONIAN")
    print("=" * 60)

    print(f"Penalty A = {PENALTY_A}")

    print("\nPauli terms:")
    for label, coefficient in hamiltonian.to_list():
        print(f"  {label}: {coefficient.real:g}")

    print()
    print(
        f"{'Project':<10}"
        f"{'Qiskit':<10}"
        f"{'QUBO':<10}"
        f"{'Pauli Energy':<15}"
    )
    print("-" * 60)

    for bits in product((0, 1), repeat=NUM_QUBITS):
        project_bits = "".join(map(str, bits))
        qiskit_bits = project_to_qiskit(project_bits)

        _, _, qubo_energy, _ = evaluate(bits)

        # Qiskit basis string uses q3 q2 q1 q0
        state = Statevector.from_label(qiskit_bits)

        pauli_energy = state.expectation_value(
            hamiltonian
        )

        assert abs(pauli_energy.imag) < 1e-9

        energy = float(pauli_energy.real)

        assert abs(energy - qubo_energy) < 1e-9, (
            f"Mismatch at {project_bits}: "
            f"QUBO={qubo_energy}, "
            f"Pauli={energy}"
        )

        print(
            f"{project_bits:<10}"
            f"{qiskit_bits:<10}"
            f"{qubo_energy:<10}"
            f"{energy:<15g}"
        )

    print(
        "\n[PASS] SparsePauliOp energies match "
        "all 16 QUBO energies!"
    )


def main():
    print("Project edge order:", BIT_ORDER)
    validate_pauli_labels()
    validate_bit_order()
    validate_qiskit_hamiltonian()

    print()
    print("=" * 60)
    print("ALL QISKIT VALIDATIONS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
