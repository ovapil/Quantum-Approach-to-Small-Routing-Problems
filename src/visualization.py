import matplotlib.pyplot as plt
import networkx as nx

from topology import create_test_topology
from dijkstra_solver import solve_dijkstra


def draw_graph(
    graph,
    shortest_path=None,
    shortest_cost=None
):
    pos = {
        "A": (0, 1),
        "B": (2, 1),
        "C": (0, 0),
        "D": (2, 0),
    }

    nx.draw_networkx_nodes(
        graph,
        pos,
        node_size=1800
    )

    nx.draw_networkx_labels(
        graph,
        pos,
        font_size=12
    )

    nx.draw_networkx_edges(
        graph,
        pos,
        arrows=True,
        arrowsize=20,
        width=1.5
    )

    edge_labels = nx.get_edge_attributes(
        graph,
        "weight"
    )

    nx.draw_networkx_edge_labels(
        graph,
        pos,
        edge_labels=edge_labels
    )

    if shortest_path is not None:
        path_edges = list(
            zip(
                shortest_path[:-1],
                shortest_path[1:]
            )
        )

        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=path_edges,
            arrows=True,
            arrowsize=20,
            width=4
        )

        title = f"Dijkstra: {' -> '.join(shortest_path)}"

        if shortest_cost is not None:
            title += f" | Cost = {shortest_cost}"

        plt.title(title)

    else:
        plt.title("No path found")

    plt.axis("off")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    graph = create_test_topology()

    source = "A"
    destination = "D"

    path, cost = solve_dijkstra(
        graph,
        source,
        destination
    )

    if path is None:
        print(
            f"No path exists from "
            f"{source} to {destination}"
        )
    else:
        print(f"Source: {source}")
        print(f"Destination: {destination}")
        print(f"Shortest path: {' -> '.join(path)}")
        print(f"Shortest cost: {cost}")

    draw_graph(
        graph,
        shortest_path=path,
        shortest_cost=cost
    )