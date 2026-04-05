from collections import defaultdict, deque
from typing import Any


def build_graph_metrics(graph: dict[str, Any]) -> dict[str, int | float]:
    """
    Compute basic quality metrics for a serialized graph.
    """
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    node_ids = [node["id"] for node in nodes]
    adjacency: dict[str, set[str]] = defaultdict(set)

    for node_id in node_ids:
        adjacency[node_id]

    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        adjacency[source].add(target)
        adjacency[target].add(source)

    node_count = len(nodes)
    edge_count = len(edges)
    isolated_nodes = sum(1 for node_id in node_ids if len(adjacency[node_id]) == 0)
    connected_components = _count_connected_components(node_ids, adjacency)
    largest_component_size = _largest_component_size(node_ids, adjacency)

    average_degree = (
        round(
            sum(len(adjacency[node_id]) for node_id in node_ids) / node_count,
            2,
        )
        if node_count
        else 0.0
    )

    density = (
        round((2 * edge_count) / (node_count * (node_count - 1)), 4)
        if node_count > 1
        else 0.0
    )

    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "isolated_nodes": isolated_nodes,
        "connected_components": connected_components,
        "largest_component_size": largest_component_size,
        "average_degree": average_degree,
        "density": density,
    }


def _count_connected_components(
    node_ids: list[str],
    adjacency: dict[str, set[str]],
) -> int:
    """
    Count the number of connected components in the graph.
    """
    visited: set[str] = set()
    components = 0

    for node_id in node_ids:
        if node_id in visited:
            continue

        components += 1
        _bfs(node_id, adjacency, visited)

    return components


def _largest_component_size(
    node_ids: list[str],
    adjacency: dict[str, set[str]],
) -> int:
    """
    Return the size of the largest connected component.
    """
    visited: set[str] = set()
    largest = 0

    for node_id in node_ids:
        if node_id in visited:
            continue

        size = _bfs(node_id, adjacency, visited)
        largest = max(largest, size)

    return largest


def _bfs(
    start_node: str,
    adjacency: dict[str, set[str]],
    visited: set[str],
) -> int:
    """
    Traverse one connected component and return its size.
    """
    queue: deque[str] = deque([start_node])
    visited.add(start_node)
    size = 0

    while queue:
        current = queue.popleft()
        size += 1

        for neighbor in adjacency[current]:
            if neighbor in visited:
                continue

            visited.add(neighbor)
            queue.append(neighbor)

    return size
