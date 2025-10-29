from typing import TYPE_CHECKING, Callable
import numpy as np

if TYPE_CHECKING:
    from terrain_map import TerrainMap


class Match:
    def __init__(
        self, skier_starting_position: tuple[int, int], terrain_map: "TerrainMap"
    ):
        self.skier_position: tuple[float, float] = skier_starting_position
        self.terrain_map = terrain_map
        self.render_callback: Callable | None = None
        self.path_history: list[tuple[float, float]] = [skier_starting_position]

    def step(self):
        if self.skier_position == self.terrain_map.get_shelter_coords():
            return True

        if self.render_callback:
            self.render_callback(self)

        self._move_skier()

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

        self.skier_position = (
            self.skier_position[0] + move_vector[0],
            self.skier_position[1] + move_vector[1],
        )
        self.path_history.append(self.skier_position)
