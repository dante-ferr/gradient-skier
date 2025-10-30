from typing import TYPE_CHECKING, Literal
import numpy as np

if TYPE_CHECKING:
    from terrain_map import TerrainMap


class Match:
    # Number of consecutive steps within the same integer coordinate to be considered stuck.
    STUCK_AREA_STEPS = 10
    # The radius (in pixels) to check for confinement. If the skier hasn't moved
    # outside a box of this size for STUCK_AREA_STEPS, they are considered stuck.
    STUCK_AREA_RADIUS = 2.0

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
        if len(self.path_history) < self.STUCK_AREA_STEPS:
            return False

        recent_path = self.path_history[-self.STUCK_AREA_STEPS :]

        # Calculate the bounding box of the recent path
        min_x = min(p[0] for p in recent_path)
        max_x = max(p[0] for p in recent_path)
        min_y = min(p[1] for p in recent_path)
        max_y = max(p[1] for p in recent_path)

        # If the bounding box is smaller than the defined radius, the skier is stuck.
        if (max_x - min_x) < self.STUCK_AREA_RADIUS and (
            max_y - min_y
        ) < self.STUCK_AREA_RADIUS:
            print(
                f"Skier is stuck in an area for {self.STUCK_AREA_STEPS} steps! Match lost."
            )
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

        self.skier_position = new_position
        self.path_history.append(self.skier_position)
