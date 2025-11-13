import numpy as np
import heapq
from config import config
from typing import TYPE_CHECKING
from ._path import Path

if TYPE_CHECKING:
    from terrain_map import TerrainMap

# Define a structure for the priority queue items
PriorityQueueItem = tuple[float, tuple[int, int]]


class Pathfinder:
    """
    Handles A* pathfinding on a terrain map with custom gradient-based costs.
    """

    def __init__(self, terrain_map: "TerrainMap"):
        self.terrain_map = terrain_map
        self.width = terrain_map.width
        self.height = terrain_map.height

    def _get_neighbors(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        """
        Gets all 8 valid neighbors of a grid position.
        """
        x, y = pos
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Skip self

                nx, ny = x + dx, y + dy

                # Check bounds
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbors.append((nx, ny))
        return neighbors

    def _get_move_cost(self, pos_a: tuple[int, int], pos_b: tuple[int, int]) -> float:
        """
        Calculates the cost of moving from A to B, including the climb penalty.
        """
        # Get height at the center of the grid cells
        height_a = self.terrain_map.get_height_at(pos_a[0], pos_a[1])
        height_b = self.terrain_map.get_height_at(pos_b[0], pos_b[1])

        delta_height = height_b - height_a

        # Euclidean distance for diagonal/straight moves
        distance = np.linalg.norm(np.array(pos_a) - np.array(pos_b))

        # Base cost is related to distance
        move_cost = distance * config.pathfinding.FLAT_MOVE_COST

        # Apply climb penalty
        if delta_height > 0:  # Only penalize going uphill
            # Gradient is rise / run
            gradient = delta_height / distance
            # Penalty can be non-linear (e.g., squared) to make steep climbs very expensive
            climb_penalty = (gradient * config.pathfinding.CLIMB_COST_MULTIPLIER) ** 2
            move_cost += climb_penalty

        return move_cost

    def _heuristic(self, pos: tuple[int, int], end_pos: tuple[int, int]) -> float:
        """
        Admissible heuristic for A*: Euclidean distance * minimum move cost.
        This ensures we never overestimate the cost.
        """
        distance = np.linalg.norm(np.array(pos) - np.array(end_pos))
        return distance * config.pathfinding.FLAT_MOVE_COST

    def _reconstruct_path(
        self,
        came_from: dict[tuple[int, int], tuple[int, int]],
        current: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """
        Traces the path back from the end node to the start node.
        """
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()  # The path is from start to end
        return path

    def find_path(self, start_pos: tuple[int, int], end_pos: tuple[int, int]) -> Path:
        """
        Runs the A* algorithm to find the lowest-cost path.
        Returns a Path object containing the list of coordinates and the total cost.
        """

        # open_set is a priority queue: (f_score, (x, y))
        open_set: list[PriorityQueueItem] = []
        heapq.heappush(open_set, (0.0, start_pos))

        # came_from[n] = node preceding n on the cheapest path
        came_from: dict[tuple[int, int], tuple[int, int]] = {}

        # g_score[n] = cost of cheapest path from start to n
        g_score: dict[tuple[int, int], float] = {
            (x, y): float("inf") for x in range(self.width) for y in range(self.height)
        }
        g_score[start_pos] = 0.0

        # f_score[n] = g_score[n] + heuristic(n, end)
        f_score: dict[tuple[int, int], float] = {
            (x, y): float("inf") for x in range(self.width) for y in range(self.height)
        }
        f_score[start_pos] = self._heuristic(start_pos, end_pos)

        open_set_hash = {start_pos}  # For efficient "in open_set" checks

        while open_set:
            # Get the node with the lowest f_score
            current_f, current_pos = heapq.heappop(open_set)
            open_set_hash.remove(current_pos)

            if current_pos == end_pos:
                # Reached the end
                path_nodes = self._reconstruct_path(came_from, current_pos)
                return Path(path_nodes, g_score[current_pos])

            for neighbor_pos in self._get_neighbors(current_pos):
                # Calculate the cost of moving from current to this neighbor
                move_cost = self._get_move_cost(current_pos, neighbor_pos)
                tentative_g_score = g_score[current_pos] + move_cost

                if tentative_g_score < g_score[neighbor_pos]:
                    # This path to neighbor is better than any previous one. Record it.
                    came_from[neighbor_pos] = current_pos
                    g_score[neighbor_pos] = tentative_g_score
                    f_score[neighbor_pos] = tentative_g_score + self._heuristic(
                        neighbor_pos, end_pos
                    )

                    if neighbor_pos not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor_pos], neighbor_pos))
                        open_set_hash.add(neighbor_pos)

        # No path found
        return Path([], float("inf"))
