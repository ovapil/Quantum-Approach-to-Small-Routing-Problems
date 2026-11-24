import numpy as np

from scipy.optimize import minimize

from qiskit.circuit.library import qaoa_ansatz
from qiskit.primitives import (
    StatevectorEstimator,
    StatevectorSampler,
)
from qiskit.quantum_info import SparsePauliOp


# ============================================================
# QUBO -> Ising cost Hamiltonian
# ============================================================

def qubo_to_cost_operator(
    qubo,
    num_qubits
):
    """
    Chuyển:

        E(x)
        =
        constant
        + sum(a_i*x_i)
        + sum(q_ij*x_i*x_j)

    với:

        x_i = (1 - Z_i) / 2

    thành:

        H
        =
        offset
        + sum(h_i*Z_i)
        + sum(J_ij*Z_i*Z_j)

    Trả về:
        cost_operator : phần Hamiltonian không chứa offset
        offset        : hằng số năng lượng
        h             : hệ số Z_i
        J             : hệ số Z_i Z_j
    """

    offset = float(qubo["constant"])

    h = {
        i: 0.0
        for i in range(num_qubits)
    }

    J = {}

    # --------------------------------------------------------
    # Linear QUBO terms:
    #
    # a_i*x_i
    # =
    # a_i/2 - a_i/2 * Z_i
    # --------------------------------------------------------

    for i, coefficient in qubo["linear"].items():

        coefficient = float(coefficient)

        offset += coefficient / 2.0

        h[i] -= coefficient / 2.0

    # --------------------------------------------------------
    # Quadratic QUBO terms:
    #
    # q_ij*x_i*x_j
    #
    # =
    # q_ij/4
    # * (1 - Z_i - Z_j + Z_i*Z_j)
    # --------------------------------------------------------

    for (
        i,
        j
    ), coefficient in qubo["quadratic"].items():

        coefficient = float(coefficient)

        offset += coefficient / 4.0

        h[i] -= coefficient / 4.0
        h[j] -= coefficient / 4.0

        J[(i, j)] = (
            J.get((i, j), 0.0)
            + coefficient / 4.0
        )

    # --------------------------------------------------------
    # Build SparsePauliOp
    # --------------------------------------------------------

    terms = []

    for i, coefficient in h.items():

        if abs(coefficient) > 1e-12:
            terms.append(
                (
                    "Z",
                    [i],
                    coefficient
                )
            )

    for (
        i,
        j
    ), coefficient in J.items():

        if abs(coefficient) > 1e-12:
            terms.append(
                (
                    "ZZ",
                    [i, j],
                    coefficient
                )
            )

    cost_operator = (
        SparsePauliOp.from_sparse_list(
            terms,
            num_qubits=num_qubits
        )
    )

    return (
        cost_operator,
        offset,
        h,
        J
    )


# ============================================================
# QAOA cost function
# ============================================================

def make_cost_function(
    circuit,
    parameter_order,
    cost_operator,
    estimator,
    history,
    offset
):
    """
    Tạo hàm cost cho scipy.optimize.minimize().
    """

    def cost_function(parameter_values):

        parameter_map = dict(
            zip(
                parameter_order,
                parameter_values
            )
        )

        bound_circuit = (
            circuit.assign_parameters(
                parameter_map
            )
        )

        job = estimator.run(
            [
                (
                    bound_circuit,
                    cost_operator
                )
            ]
        )

        result = job.result()[0]

        energy_without_offset = float(
            np.real(
                result.data.evs
            )
        )

        full_energy = (
            energy_without_offset
            + offset
        )

        history.append(
            full_energy
        )

        # Offset không ảnh hưởng vị trí optimum,
        # nên optimizer chỉ cần minimize phần operator.
        return energy_without_offset

    return cost_function


# ============================================================
# Run QAOA
# ============================================================

def run_qaoa(
    cost_operator,
    offset=0.0,
    reps=1,
    shots=2048,
    seed=42,
    maxiter=None,
    restarts=3,
):
    """
    Chạy QAOA bằng:
        - qaoa_ansatz
        - StatevectorEstimator
        - COBYLA (multi-start)
        - StatevectorSampler
    """

    # --------------------------------------------------------
    # Build QAOA circuit
    # --------------------------------------------------------

    circuit = qaoa_ansatz(
        cost_operator,
        reps=reps,
        flatten=True,
    )

    parameter_order = list(circuit.parameters)

    # --------------------------------------------------------
    # Optimization (multi-start COBYLA)
    # --------------------------------------------------------

    if maxiter is None:
       maxiter = 300 * reps

    rng = np.random.default_rng(seed)
    estimator = StatevectorEstimator(seed=seed)

    history = []
    best = None

    for _ in range(restarts):
        x0 = rng.uniform(0.0, np.pi, size=len(parameter_order))

        cost_function = make_cost_function(
            circuit,
            parameter_order,
            cost_operator,
            estimator,
            history,
            offset,
        )

        res = minimize(
            cost_function,
            x0,
            method="COBYLA",
            options={"maxiter": maxiter, "rhobeg": 0.5},
        )

        if best is None or res.fun < best[0].fun:
            best = (res, x0)

    optimization_result, initial_parameters = best
    optimal_parameters = optimization_result.x

    # --------------------------------------------------------
    # Sample with optimal parameters
    # --------------------------------------------------------

    optimal_circuit = circuit.assign_parameters(
        dict(zip(parameter_order, optimal_parameters))
    )

    measurement_circuit = optimal_circuit.copy()
    measurement_circuit.measure_all()

    sampler = StatevectorSampler(seed=seed)
    sample_result = sampler.run(
        [measurement_circuit],
        shots=shots,
    ).result()[0]

    counts = sample_result.data.meas.get_counts()

    probabilities = {
        bitstring: count / shots
        for bitstring, count in counts.items()
    }

    final_parameter_map = {
        str(parameter): float(value)
        for parameter, value in zip(parameter_order, optimal_parameters)
    }

    return {
        "success": optimization_result.success,
        "message": optimization_result.message,
        "reps": reps,
        "shots": shots,
        "restarts": restarts,
        "parameters": final_parameter_map,
        "initial_parameters": initial_parameters.tolist(),
        "expectation_value": float(optimization_result.fun + offset),
        "history": history,
        "counts": counts,
        "probabilities": probabilities,
        "circuit": circuit,
    }
# ============================================================

if __name__ == "__main__":

    from topology import (
        create_test_topology
    )

    from binary_encoding import (
        create_edge_mapping
    )

    from qubo_builder import (
        build_qubo
    )

    from decoder import (
        decode_distribution,
        print_top_results,
    )

    graph = create_test_topology()

    mapping = create_edge_mapping(
        graph
    )

    qubo = build_qubo(
        graph,
        mapping,
        source="A",
        destination="D",
        penalty=3.0
    )

    (
        cost_operator,
        offset,
        h,
        J
    ) = qubo_to_cost_operator(
        qubo,
        num_qubits=len(mapping)
    )

    print("=" * 60)
    print("ISING / COST HAMILTONIAN")
    print("=" * 60)

    print(
        "Offset:",
        offset
    )

    print(
        "h:",
        h
    )

    print(
        "J:",
        J
    )

    print(
        "\nOperator:"
    )

    print(
        cost_operator
    )

    print("\n" + "=" * 60)
    print("RUN QAOA")
    print("=" * 60)

    result = run_qaoa(
        cost_operator,
        offset=offset,
        reps=1,
        shots=2048,
        seed=42,
        maxiter=150
    )

    decoded_results = decode_distribution(
        result["counts"],
        graph,
        mapping,
        source="A",
        destination="D",
        optimal_bitstring="1010"
    )

    print("\n" + "=" * 100)
    print("DECODED QAOA RESULTS")
    print("=" * 100)

    print_top_results(
        decoded_results,
        top_k=10
    )

    print(
        "\nOptimization success:",
        result["success"]
    )

    print(
        "Message:",
        result["message"]
    )

    print(
        "\nFinal parameters:"
    )

    for name, value in (
        result["parameters"].items()
    ):
        print(
            f"{name} = {value:.6f}"
        )

    print(
        "\nFinal expectation value:",
        result["expectation_value"]
    )

    print(
        "\nOptimizer evaluations:",
        len(result["history"])
    )

    print(
        "\nTop measured bitstrings:"
    )

    sorted_probabilities = sorted(
        result["probabilities"].items(),
        key=lambda item: item[1],
        reverse=True
    )

    for bitstring, probability in (
        sorted_probabilities[:10]
    ):
        print(
            f"{bitstring}: "
            f"{probability:.4f}"
        )