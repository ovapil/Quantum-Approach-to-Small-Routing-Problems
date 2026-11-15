from binary_encoding import (
    bitstring_to_selected_edges,
    calculate_objective_cost,
)

from flow_constraints import (
    check_feasibility,
)


# ============================================================
# Qiskit bit ordering
# ============================================================

def qiskit_to_project_bitstring(
    qiskit_bitstring
):
    """
    Qiskit measurement:
        left ... right
        q_(n-1) ... q_0

    Project mapping:
        bitstring[0] -> variable 0

    Vì vậy phải đảo chuỗi.
    """

    cleaned = (
        qiskit_bitstring
        .replace(" ", "")
    )

    return cleaned[::-1]


# ============================================================
# Decode one measured bitstring
# ============================================================

def decode_bitstring(
    qiskit_bitstring,
    graph,
    mapping,
    source,
    destination
):
    project_bitstring = (
        qiskit_to_project_bitstring(
            qiskit_bitstring
        )
    )

    selected_edges = (
        bitstring_to_selected_edges(
            project_bitstring,
            mapping
        )
    )

    route_cost = (
        calculate_objective_cost(
            project_bitstring,
            mapping
        )
    )

    feasible, reason = (
        check_feasibility(
            graph,
            project_bitstring,
            mapping,
            source,
            destination
        )
    )

    return {
        "qiskit_bitstring":
            qiskit_bitstring,

        "project_bitstring":
            project_bitstring,

        "selected_edges":
            selected_edges,

        "cost":
            route_cost,

        "feasible":
            feasible,

        "reason":
            reason,
    }


# ============================================================
# Decode complete distribution
# ============================================================

def decode_distribution(
    counts,
    graph,
    mapping,
    source,
    destination,
    optimal_bitstring=None
):
    total_shots = sum(
        counts.values()
    )

    results = []

    for (
        qiskit_bitstring,
        count
    ) in counts.items():

        decoded = decode_bitstring(
            qiskit_bitstring,
            graph,
            mapping,
            source,
            destination
        )

        decoded["count"] = count

        decoded["probability"] = (
            count / total_shots
        )

        if optimal_bitstring is None:

            decoded["optimal"] = None

        else:

            decoded["optimal"] = (
                decoded[
                    "project_bitstring"
                ]
                == optimal_bitstring
            )

        results.append(
            decoded
        )

    results.sort(
        key=lambda item:
        item["probability"],
        reverse=True
    )

    return results


# ============================================================
# Print top results
# ============================================================

def print_top_results(
    results,
    top_k=10
):
    print(
        f"{'Qiskit':>8} | "
        f"{'Project':>8} | "
        f"{'Prob.':>8} | "
        f"{'Valid':>7} | "
        f"{'Cost':>6} | "
        f"{'Optimal':>7} | "
        f"Edges"
    )

    print("-" * 100)

    for result in results[:top_k]:

        print(
            f"{result['qiskit_bitstring']:>8} | "
            f"{result['project_bitstring']:>8} | "
            f"{result['probability']:8.4f} | "
            f"{str(result['feasible']):>7} | "
            f"{result['cost']:6} | "
            f"{str(result['optimal']):>7} | "
            f"{result['selected_edges']}"
        )