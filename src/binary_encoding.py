from topology import create_test_topology


def create_edge_mapping(graph):
    edges = sorted(
        graph.edges(data=True),
        key=lambda edge: (edge[0], edge[1])
    )

    mapping = {}

    for index, (source, destination, data) in enumerate(edges):
        mapping[index] = {
            "variable": f"x_{source}{destination}",
            "edge": (source, destination),
            "weight": data["weight"]
        }

    return mapping


def validate_bitstring(bitstring, mapping):
    if len(bitstring) != len(mapping):
        raise ValueError(
            f"Bitstring length must be {len(mapping)}, "
            f"but received {len(bitstring)}."
        )

    if any(bit not in {"0", "1"} for bit in bitstring):
        raise ValueError(
            "Bitstring must contain only 0 and 1."
        )


def bitstring_to_selected_edges(bitstring, mapping):
    validate_bitstring(bitstring, mapping)

    selected_edges = []

    for index, bit in enumerate(bitstring):
        if bit == "1":
            selected_edges.append(
                mapping[index]["edge"]
            )

    return selected_edges


def calculate_objective_cost(bitstring, mapping):
    validate_bitstring(bitstring, mapping)

    total_cost = 0

    for index, bit in enumerate(bitstring):
        if bit == "1":
            total_cost += mapping[index]["weight"]

    return total_cost


def print_edge_mapping(mapping):
    print("Edge mapping:")

    for index, info in mapping.items():
        source, destination = info["edge"]

        print(
            f"bit {index}: "
            f"{info['variable']} -> "
            f"{source} -> {destination}, "
            f"weight = {info['weight']}"
        )


if __name__ == "__main__":
    graph = create_test_topology()

    mapping = create_edge_mapping(graph)

    print_edge_mapping(mapping)

    test_bitstrings = [
        "0000",
        "1000",
        "1010",
        "0101",
        "1111"
    ]

    print("\nBitstring tests:")

    for bitstring in test_bitstrings:
        selected_edges = bitstring_to_selected_edges(
            bitstring,
            mapping
        )

        cost = calculate_objective_cost(
            bitstring,
            mapping
        )

        print(f"\nBitstring: {bitstring}")
        print(f"Selected edges: {selected_edges}")
        print(f"Objective cost: {cost}")