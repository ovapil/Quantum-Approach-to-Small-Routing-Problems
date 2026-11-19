import networkx as nx

def create_test_topology():
    graph = nx.DiGraph()

    graph.add_edge("A", "B", weight=2)
    graph.add_edge("A", "C", weight=5)
    graph.add_edge("B", "D", weight=3)
    graph.add_edge("C", "D", weight=4)

    return graph


if __name__ == "__main__":
    graph = create_test_topology()

    print("Nodes:")
    print(list(graph.nodes))

    print("\nEdges:")
    for source, destination, data in graph.edges(data=True):
        print(f"{source} -> {destination}, "f"weight = {data['weight']}")