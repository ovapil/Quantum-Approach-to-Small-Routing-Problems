from itertools import product

from topology import create_test_topology

from dijkstra_solver import solve_dijkstra

from binary_encoding import (
    create_edge_mapping,
    bitstring_to_selected_edges,
    calculate_objective_cost,
)

from flow_constraints import (
    check_feasibility,
)

from qubo_builder import (
    build_qubo,
    calculate_qubo_energy,
)


def generate_bitstrings(number_of_variables):
    for bits in product(
        "01",
        repeat=number_of_variables
    ):
        yield "".join(bits)


def solve_qubo_exact(
    graph,
    mapping,
    source,
    destination,
    penalty
):
    qubo = build_qubo(
        graph,
        mapping,
        source,
        destination,
        penalty
    )

    results = []

    for bitstring in generate_bitstrings(
        len(mapping)
    ):
        selected_edges = (
            bitstring_to_selected_edges(
                bitstring,
                mapping
            )
        )

        route_cost = (
            calculate_objective_cost(
                bitstring,
                mapping
            )
        )

        energy = calculate_qubo_energy(
            bitstring,
            mapping,
            qubo
        )

        feasible, reason = check_feasibility(
            graph,
            bitstring,
            mapping,
            source,
            destination
        )

        results.append(
            {
                "bitstring": bitstring,
                "selected_edges": selected_edges,
                "route_cost": route_cost,
                "energy": energy,
                "feasible": feasible,
                "reason": reason,
            }
        )

    results.sort(
        key=lambda item: (
            item["energy"],
            item["bitstring"]
        )
    )

    return results


if __name__ == "__main__":
    graph = create_test_topology()

    source = "A"
    destination = "D"

    penalty = 3.0

    mapping = create_edge_mapping(graph)

    results = solve_qubo_exact(
        graph,
        mapping,
        source,
        destination,
        penalty
    )

    print(
        f"Penalty A = {penalty}"
    )

    print("\nAll solutions:")

    for result in results:
        print(
            f"{result['bitstring']} | "
            f"energy={result['energy']:.2f} | "
            f"cost={result['route_cost']} | "
            f"feasible={result['feasible']} | "
            f"edges={result['selected_edges']}"
        )

    best = results[0]

    print("\nBest QUBO solution:")

    print(
        f"Bitstring: {best['bitstring']}"
    )

    print(
        f"Selected edges: "
        f"{best['selected_edges']}"
    )

    print(
        f"Route cost: "
        f"{best['route_cost']}"
    )

    print(
        f"QUBO energy: "
        f"{best['energy']}"
    )

    print(
        f"Feasible: "
        f"{best['feasible']}"
    )

    # --------------------------------------------------------
    # Dijkstra ground truth
    # --------------------------------------------------------

    dijkstra_path, dijkstra_cost = (
        solve_dijkstra(
            graph,
            source,
            destination
        )
    )

    print("\nDijkstra ground truth:")

    print(
        "Path: "
        + " -> ".join(
            dijkstra_path
        )
    )

    print(
        f"Cost: {dijkstra_cost}"
    )