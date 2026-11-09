from topology import create_test_topology
from binary_encoding import (
    create_edge_mapping,
    bitstring_to_selected_edges,
    calculate_objective_cost,
)


def calculate_node_flows(graph, selected_edges):

    flows = {}

    for node in graph.nodes:
        flows[node] = {
            "in": 0,
            "out": 0
        }

    for source, destination in selected_edges:
        flows[source]["out"] += 1
        flows[destination]["in"] += 1

    return flows


def check_flow_conservation(
    graph,
    selected_edges,
    source,
    destination
):
    flows = calculate_node_flows(
        graph,
        selected_edges
    )

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

        if actual_balance != expected_balance:
            return (
                False,
                (
                    f"Flow conservation violated at node {node}: "
                    f"expected balance {expected_balance}, "
                    f"got {actual_balance}"
                )
            )

    return True, "Flow conservation satisfied"


def check_path_structure(
    graph,
    selected_edges,
    source,
    destination
):

    if not selected_edges:
        return False, "No edges selected"

    flows = calculate_node_flows(
        graph,
        selected_edges
    )

    # Source phải có đúng 1 edge đi ra
    # và không có edge đi vào.
    if (
        flows[source]["out"] != 1
        or flows[source]["in"] != 0
    ):
        return (
            False,
            "Source must have exactly one outgoing edge "
            "and no incoming edge"
        )

    # Destination phải có đúng 1 edge đi vào
    # và không có edge đi ra.
    if (
        flows[destination]["in"] != 1
        or flows[destination]["out"] != 0
    ):
        return (
            False,
            "Destination must have exactly one incoming edge "
            "and no outgoing edge"
        )

    # Intermediate node:
    # hoặc không được dùng (0, 0),
    # hoặc nằm trên path (1, 1).
    for node in graph.nodes:
        if node in {source, destination}:
            continue

        node_in = flows[node]["in"]
        node_out = flows[node]["out"]

        if (node_in, node_out) not in {
            (0, 0),
            (1, 1)
        }:
            return (
                False,
                (
                    f"Invalid path structure at node {node}: "
                    f"in={node_in}, out={node_out}"
                )
            )

    # Theo route từ source đến destination.
    selected_set = set(selected_edges)

    current = source
    visited_nodes = {source}
    used_edges = set()

    while current != destination:
        outgoing = [
            (u, v)
            for u, v in selected_edges
            if u == current
        ]

        if len(outgoing) != 1:
            return (
                False,
                f"Expected one outgoing edge from {current}"
            )

        edge = outgoing[0]
        used_edges.add(edge)

        next_node = edge[1]

        if next_node in visited_nodes:
            return False, "Cycle detected"

        visited_nodes.add(next_node)
        current = next_node

    # Nếu còn edge được chọn nhưng không nằm trên
    # route source → destination thì đó là edge thừa/rời rạc.
    if used_edges != selected_set:
        return (
            False,
            "Extra or disconnected edges detected"
        )

    return True, "Selected edges form a valid path"


def check_feasibility(
    graph,
    bitstring,
    mapping,
    source,
    destination
):

    selected_edges = bitstring_to_selected_edges(
        bitstring,
        mapping
    )

    # Bước 1: kiểm tra flow conservation
    flow_valid, flow_reason = check_flow_conservation(
        graph,
        selected_edges,
        source,
        destination
    )

    if not flow_valid:
        return False, flow_reason

    # Bước 2: kiểm tra cấu trúc route
    path_valid, path_reason = check_path_structure(
        graph,
        selected_edges,
        source,
        destination
    )

    if not path_valid:
        return False, path_reason

    return True, "Valid source-to-destination path"


if __name__ == "__main__":
    graph = create_test_topology()

    source = "A"
    destination = "D"

    mapping = create_edge_mapping(graph)

    test_bitstrings = [
        "1010",
        "0101",
        "0000",
        "1000",
        "1001",
        "1110",
        "1111",
    ]

    for bitstring in test_bitstrings:
        selected_edges = bitstring_to_selected_edges(
            bitstring,
            mapping
        )

        cost = calculate_objective_cost(
            bitstring,
            mapping
        )

        valid, reason = check_feasibility(
            graph,
            bitstring,
            mapping,
            source,
            destination
        )

        print(f"\nBitstring: {bitstring}")
        print(f"Selected edges: {selected_edges}")
        print(f"Cost: {cost}")
        print(f"Feasible: {valid}")
        print(f"Reason: {reason}")