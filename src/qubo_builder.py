from topology import create_test_topology
from binary_encoding import (
    create_edge_mapping,
    validate_bitstring,
)


def build_flow_expression(
    graph,
    mapping,
    node,
    source,
    destination
):

    if node == source:
        b_v = 1
    elif node == destination:
        b_v = -1
    else:
        b_v = 0

    constant = -b_v

    coefficients = {}

    for index, info in mapping.items():
        edge_source, edge_destination = info["edge"]

        coefficient = 0

        if edge_source == node:
            coefficient += 1

        if edge_destination == node:
            coefficient -= 1

        if coefficient != 0:
            coefficients[index] = coefficient

    return constant, coefficients


def build_qubo(
    graph,
    mapping,
    source,
    destination,
    penalty
):

    number_of_variables = len(mapping)

    constant = 0.0

    linear = {
        index: float(mapping[index]["weight"])
        for index in range(number_of_variables)
    }

    quadratic = {}

    for node in graph.nodes:
        flow_constant, flow_coefficients = (
            build_flow_expression(
                graph,
                mapping,
                node,
                source,
                destination
            )
        )

        constant += (
            penalty
            * (flow_constant ** 2)
        )

        coefficient_items = list(
            flow_coefficients.items()
        )

        for index, a_i in coefficient_items:
            linear[index] += (
                penalty
                * (
                    (a_i ** 2)
                    + 2 * flow_constant * a_i
                )
            )

        for i in range(len(coefficient_items)):
            index_i, a_i = coefficient_items[i]

            for j in range(
                i + 1,
                len(coefficient_items)
            ):
                index_j, a_j = (
                    coefficient_items[j]
                )

                key = tuple(
                    sorted(
                        (index_i, index_j)
                    )
                )

                quadratic[key] = (
                    quadratic.get(key, 0.0)
                    + penalty
                    * 2
                    * a_i
                    * a_j
                )

    # Xóa coefficient bằng 0 để output sạch
    linear = {
        index: value
        for index, value in linear.items()
        if abs(value) > 1e-12
    }

    quadratic = {
        key: value
        for key, value in quadratic.items()
        if abs(value) > 1e-12
    }

    return {
        "constant": constant,
        "linear": linear,
        "quadratic": quadratic
    }


def calculate_qubo_energy(
    bitstring,
    mapping,
    qubo
):

    validate_bitstring(
        bitstring,
        mapping
    )

    x = [
        int(bit)
        for bit in bitstring
    ]

    energy = qubo["constant"]

    for index, coefficient in qubo["linear"].items():
        energy += (
            coefficient
            * x[index]
        )

    for (
        index_i,
        index_j
    ), coefficient in qubo["quadratic"].items():

        energy += (
            coefficient
            * x[index_i]
            * x[index_j]
        )

    return energy


def build_symmetric_qubo_matrix(
    mapping,
    qubo
):

    n = len(mapping)

    matrix = [
        [0.0 for _ in range(n)]
        for _ in range(n)
    ]

    # Linear term đi vào diagonal
    for index, coefficient in qubo["linear"].items():
        matrix[index][index] = coefficient

    # Quadratic coefficient phải chia đôi
    for (
        index_i,
        index_j
    ), coefficient in qubo["quadratic"].items():

        half = coefficient / 2.0

        matrix[index_i][index_j] = half
        matrix[index_j][index_i] = half

    return matrix


def print_qubo(
    mapping,
    qubo
):
    print("QUBO constant:")
    print(qubo["constant"])

    print("\nLinear coefficients:")

    for index in range(len(mapping)):
        coefficient = qubo["linear"].get(
            index,
            0.0
        )

        variable = mapping[index]["variable"]

        print(
            f"{variable}: {coefficient}"
        )

    print("\nQuadratic coefficients:")

    if not qubo["quadratic"]:
        print("(none)")

    else:
        for (
            index_i,
            index_j
        ), coefficient in sorted(
            qubo["quadratic"].items()
        ):
            variable_i = (
                mapping[index_i]["variable"]
            )

            variable_j = (
                mapping[index_j]["variable"]
            )

            print(
                f"{variable_i} * "
                f"{variable_j}: "
                f"{coefficient}"
            )


def print_qubo_matrix(
    mapping,
    matrix
):
    variables = [
        mapping[index]["variable"]
        for index in range(len(mapping))
    ]

    print("\nSymmetric QUBO matrix:")
    print(
        "        "
        + " ".join(
            f"{variable:>8}"
            for variable in variables
        )
    )

    for index, row in enumerate(matrix):
        print(
            f"{variables[index]:>8} "
            + " ".join(
                f"{value:8.2f}"
                for value in row
            )
        )


if __name__ == "__main__":
    graph = create_test_topology()

    source = "A"
    destination = "D"

    mapping = create_edge_mapping(graph)

    penalty = 3.0

    qubo = build_qubo(
        graph,
        mapping,
        source,
        destination,
        penalty
    )

    print(
        f"Penalty A = {penalty}"
    )

    print_qubo(
        mapping,
        qubo
    )

    matrix = build_symmetric_qubo_matrix(
        mapping,
        qubo
    )

    print_qubo_matrix(
        mapping,
        matrix
    )

    print("\nEnergy tests:")

    for bitstring in [
        "0000",
        "1010",
        "0101",
        "1111"
    ]:
        energy = calculate_qubo_energy(
            bitstring,
            mapping,
            qubo
        )

        print(
            f"{bitstring}: "
            f"energy = {energy}"
        )