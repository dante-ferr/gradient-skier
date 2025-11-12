from typing import TYPE_CHECKING, Literal
import numpy as np
from config import config

if TYPE_CHECKING:
    from terrain_map import TerrainMap


class Match:
    def __init__(
        self, skier_starting_position: tuple[int, int], terrain_map: "TerrainMap"
    ):
        self.skier_position: tuple[float, float] = skier_starting_position
        self.terrain_map: "TerrainMap" = terrain_map
        self.path_history: list[tuple[float, float]] = [skier_starting_position]

        self.status: Literal["playing", "won", "lost"] = "playing"

    def step(self):
        sx_int, sy_int = int(self.skier_position[0]), int(self.skier_position[1])

        if (
            abs(self.skier_position[0] - self.terrain_map.get_shelter_coords()[0]) < 0.1
            and abs(self.skier_position[1] - self.terrain_map.get_shelter_coords()[1])
            < 0.1
        ):
            self.status = "won"
            return True

        self._move_skier()

        if self._is_stuck_in_area():
            self.status = "lost"
            return True

        return False

    def _is_stuck_in_area(self) -> bool:
        """
        Checks if the skier has been confined to a small area for the last
        `STUCK_AREA_STEPS` steps, indicating they are stuck.
        """
        stuck_steps = config.game.STUCK_AREA_STEPS
        stuck_radius = config.game.STUCK_AREA_RADIUS
        if len(self.path_history) < stuck_steps:
            return False

        recent_path = self.path_history[-stuck_steps:]

        # Calculate the bounding box of the recent path
        min_x = min(p[0] for p in recent_path)
        max_x = max(p[0] for p in recent_path)
        min_y = min(p[1] for p in recent_path)
        max_y = max(p[1] for p in recent_path)

        # If the bounding box is smaller than the defined radius, the skier is stuck.
        if (max_x - min_x) < stuck_radius and (max_y - min_y) < stuck_radius:
            print(f"Skier is stuck in an area for {stuck_steps} steps! Match lost.")
            return True

        return False

    def _get_shelter_move_vector(self, min_dist: float = 1.0) -> np.ndarray:
        """
        Calculates a normalized move vector pointing directly to the shelter.
        Returns a zero vector if the skier is closer than `min_dist`.
        """
        shelter_coords = self.terrain_map.get_shelter_coords()
        direction_vector = np.array(shelter_coords) - np.array(self.skier_position)
        distance = np.linalg.norm(direction_vector)

        if distance > min_dist:
            return direction_vector / distance  # Normalized vector
        elif distance > 1e-9:
            return direction_vector  # Very close, move the remaining distance
        return np.array([0.0, 0.0])  # At the destination

    def _move_skier(self):
        sx, sy = self.skier_position

        if self.terrain_map.is_global_minimum(int(sx), int(sy)):
            # If in the global minimum basin, move directly towards the shelter
            move_vector = self._get_shelter_move_vector()
        else:
            # Otherwise, follow the gradient
            gradient = self.terrain_map.get_gradient_at(int(sx), int(sy))
            norm = np.linalg.norm(gradient)
            if norm > 0:
                move_vector = -gradient / norm  # Move against the gradient (downhill)
            else:
                # Stuck in a local minimum (zero gradient), move towards shelter as a fallback.
                move_vector = self._get_shelter_move_vector(min_dist=2.0)

        new_position = (
            self.skier_position[0] + move_vector[0] * config.game.MOVE_SPEED,
            self.skier_position[1] + move_vector[1] * config.game.MOVE_SPEED,
        )

        # Clamp the new position to stay within the map boundaries
        clamped_x = np.clip(new_position[0], 0, self.terrain_map.width - 1)
        clamped_y = np.clip(new_position[1], 0, self.terrain_map.height - 1)

        new_position = (clamped_x, clamped_y)

        self.skier_position = new_position
        self.path_history.append(self.skier_position)
