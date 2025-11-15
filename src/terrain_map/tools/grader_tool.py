import numpy as np
from .terrain_tool import TerrainTool
from typing import TYPE_CHECKING
from config import config

if TYPE_CHECKING:
    from terrain_map import TerrainMap


class GraderTool(TerrainTool):
    """
    Tool that smooths the terrain by pulling heights toward the mean,
    directly reducing local gradients.
    """

    def __init__(self):
        super().__init__("Grader")
        self.intensity = config.TOOL.GRADER_INTENSITY

    def apply(self, terrain_map: "TerrainMap", center_x: int, center_y: int) -> bool:
        mask, y_slice, x_slice = self._get_area_mask(terrain_map, center_x, center_y)

        # Get the heights of the affected area
        aoe_height_data = terrain_map.height_data[y_slice, x_slice]
        aoe_values = aoe_height_data[mask]  # Values within the circle

        if aoe_values.size <= 1:  # Need at least two points to average
            return False

        mean_height = np.mean(aoe_values)

        # Create a grid to calculate distance from the center for the falloff effect
        y_indices, x_indices = np.ogrid[y_slice, x_slice]
        dist_squared = (x_indices - center_x) ** 2 + (y_indices - center_y) ** 2

        # Normalize distance to a 0-1 range (0 at center, 1 at edge)
        normalized_dist = np.sqrt(dist_squared) / (self.radius + 1e-6)

        # Create a smooth falloff (e.g., cosine) for a convex shape
        # This will be 1 at the center and 0 at the radius edge
        falloff = (np.cos(normalized_dist * np.pi / 2) ** 2)[mask]

        # Calculate the change: difference from mean * intensity
        change = (mean_height - aoe_values) * self.intensity * falloff

        # Apply the smoothing change back to the height data
        aoe_height_data[mask] += change

        return True
