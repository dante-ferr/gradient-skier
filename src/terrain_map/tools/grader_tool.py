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

        # Calculate the change: difference from mean * intensity
        change = (mean_height - aoe_values) * self.intensity

        # Apply the smoothing change back to the height data
        aoe_height_data[mask] += change

        return True
