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

        if self.skier_position == self.terrain_map.get_shelter_coords():
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

    def _move_skier(self):
        sx, sy = self.skier_position

        if self.terrain_map.is_global_minimum(int(sx), int(sy)):
            # If in the global minimum basin, move directly towards the shelter
            shelter_coords = self.terrain_map.get_shelter_coords()

            # Vector from player to shelter
            direction_vector = np.array(shelter_coords) - np.array(self.skier_position)

            # Normalize the vector to get a unit vector (length 1)
            distance = np.linalg.norm(direction_vector)
            if distance > 1:  # Move only if not already at the shelter
                move_vector = direction_vector / distance
            else:
                move_vector = direction_vector  # Arrived
        else:
            # Otherwise, follow the gradient
            gradient = self.terrain_map.get_gradient_at(int(sx), int(sy))
            # We need to normalize the gradient to control speed, let's assume a step size of 1 for now
            norm = np.linalg.norm(gradient)
            if norm > 0:
                move_vector = -gradient / norm  # Move against the gradient (downhill)
            else:
                move_vector = np.array([0.0, 0.0])  # Stuck in a local minimum

        new_position = (
            self.skier_position[0] + move_vector[0],
            self.skier_position[1] + move_vector[1],
        )

        # Clamp the new position to stay within the map boundaries
        clamped_x = np.clip(new_position[0], 0, self.terrain_map.width - 1)
        clamped_y = np.clip(new_position[1], 0, self.terrain_map.height - 1)

        new_position = (clamped_x, clamped_y)

        self.skier_position = new_position
        self.path_history.append(self.skier_position)
