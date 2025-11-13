class Path:
    """
    A data class to hold the results of a pathfinding operation.

    Encapsulates the list of nodes and the total cost of the path.
    """

    def __init__(self, nodes: list[tuple[float, float]], total_cost: float):
        self.nodes: list[tuple[float, float]] = nodes
        self.total_cost: float = total_cost

    @property
    def is_valid(self) -> bool:
        """Returns True if a path was found (cost is not infinite)."""
        return self.total_cost != float("inf") and len(self.nodes) > 0

    @property
    def node_count(self) -> int:
        """Returns the number of nodes in the path."""
        return len(self.nodes)
