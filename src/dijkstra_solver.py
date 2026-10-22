import networkx as nx

from topology import create_test_topology


def solve_dijkstra(graph, source, destination):
    try:
        shortest_path = nx.dijkstra_path(
            graph,
            source=source,
            target=destination,
            weight="weight"
        )

        shortest_cost = nx.dijkstra_path_length(
            graph,
            source=source,
            target=destination,
            weight="weight"
        )

        return shortest_path, shortest_cost

    except nx.NetworkXNoPath:
        return None, None


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
        print(f"No path exists from {source} to {destination}")
    else:
        print(f"Source: {source}")
        print(f"Destination: {destination}")
        print(f"Shortest path: {' -> '.join(path)}")
        print(f"Shortest cost: {cost}")