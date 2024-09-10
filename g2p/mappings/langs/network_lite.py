from collections import deque
from typing import Any, Iterable, Iterator


class DiGraph:
    """A simple directed graph class

    Most functions raise KeyError if called with a node u or v not in the graph.
    """

    def __init__(self) -> None:
        """Contructor, empty if no data, else load from data"""
        self._edges: dict = {}

    def clear(self):
        """Clear the graph"""
        self._edges.clear()

    def update(self, edges: Iterable, nodes: Iterable):
        """Update the graph with new edges and nodes"""
        for node in nodes:
            self.add_node(node)
        for u, v in edges:
            self.add_edge(u, v)

    def add_node(self, u):
        """Add a node to the graph"""
        if u not in self._edges:
            self._edges[u] = []

    def add_edge(self, u, v):
        """Add a directed edge from u to v"""
        self.add_node(u)
        self.add_node(v)
        if v not in self._edges[u]:
            self._edges[u].append(v)

    def add_edges_from(self, edges: Iterable):
        """Add edges from a list of tuples"""
        for u, v in edges:
            self.add_edge(u, v)

    @property  # read-only
    def nodes(self):
        """Return the nodes"""
        return self._edges.keys()

    @property  # read-only
    def edges(self) -> Iterator:
        """Iterate over all edges"""
        for u, neighbours in self._edges.items():
            for v in neighbours:
                yield u, v

    def __contains__(self, u) -> bool:
        """Check if a node is in the graph"""
        return u in self._edges

    def has_path(self, u, v) -> bool:
        """Check if there is a path from u to v"""
        if v not in self._edges:
            raise KeyError(f"Node {v} not in graph")
        visited: set = set()
        return self._has_path(u, v, visited)

    def _has_path(self, u, v, visited: set) -> bool:
        """Helper function for has_path"""
        visited.add(u)
        if u == v:
            return True
        for neighbour in self._edges[u]:
            if neighbour not in visited:
                if self._has_path(neighbour, v, visited):
                    return True
        return False

    def successors(self, u) -> Iterator:
        """Return the successors of u"""
        return iter(self._edges[u])

    def descendants(self, u) -> set:
        """Return the descendants of u"""
        visited: set = set()
        self._descendants(u, visited)
        visited.remove(u)
        return visited

    def _descendants(self, u, visited: set):
        """Helper function for descendants"""
        visited.add(u)
        for neighbour in self._edges[u]:
            if neighbour not in visited:
                self._descendants(neighbour, visited)

    def ancestors(self, u):
        """Return the ancestors of u"""
        reversed_graph = DiGraph()
        reversed_graph.add_edges_from((v, u) for u, v in self.edges)
        for node in self.nodes:
            reversed_graph.add_node(node)
        return reversed_graph.descendants(u)

    def shortest_path(self, u, v) -> list:
        """Return the shortest path from u to v

        Algorithm: Dijsktra's algorithm for unweighted graphs, which is just BFS

        Returns:
            list: the shortest path from u to v
        Raises:
            KeyError: if u or v is not in the graph
            ValueError: if there is no path from u to v
        """

        if v not in self._edges:
            raise KeyError(f"Node {v} not in graph")
        visited = {u: None}  # dict of {node: predecessor on shortest path from u}
        queue: deque[Any] = deque()
        while True:
            if u == v:
                rev_path = []
                while u is not None:
                    rev_path.append(u)
                    u = visited[u]
                return list(reversed(rev_path))
            for neighbour in self._edges[u]:
                if neighbour not in visited:
                    visited[neighbour] = u
                    queue.append(neighbour)
            if len(queue) == 0:
                raise ValueError(f"No path from {u} to {v}")
            u = queue.popleft()


def node_link_graph(data: dict):
    """Replacement for networkx.node_link_graph"""
    if not data.get("directed", False):
        raise ValueError("Graph must be directed")
    if data.get("multigraph", True):
        raise ValueError("Graph must not be a multigraph")
    if not isinstance(data.get("nodes", None), list):
        raise ValueError('data["nodes"] must be a list')
    if not isinstance(data.get("links", None), list):
        raise ValueError('data["links"] must be a list')

    graph = DiGraph()
    for node in data["nodes"]:
        graph.add_node(node["id"])
    for edge in data["links"]:
        graph.add_edge(edge["source"], edge["target"])
    return graph


def node_link_data(graph: DiGraph):
    """Replacement for networkx.node_link_data"""
    nodes = [{"id": node} for node in graph.nodes]
    links = [{"source": u, "target": v} for u, v in graph.edges]
    return {
        "directed": True,
        "graph": {},
        "links": links,
        "multigraph": False,
        "nodes": nodes,
    }
