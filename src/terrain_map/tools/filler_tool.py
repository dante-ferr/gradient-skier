from .terrain_tool import TerrainTool
from typing import TYPE_CHECKING
import numpy as np
from config import config

if TYPE_CHECKING:
    from terrain_map import TerrainMap


class FillerTool(TerrainTool):
    """
    Tool that raises the terrain height (building a ramp/bridge).
    """

    def __init__(self):
        super().__init__("Filler")
        self.height_increase = config.TOOL.FILLER_HEIGHT

    def apply(self, terrain_map: "TerrainMap", center_x: int, center_y: int) -> bool:
        mask, y_slice, x_slice = self._get_area_mask(terrain_map, center_x, center_y)

        if not mask.any():
            return False

        # Create a grid to calculate distance from the center for the falloff effect
        y_indices, x_indices = np.ogrid[y_slice, x_slice]
        dist_squared = (x_indices - center_x) ** 2 + (y_indices - center_y) ** 2

        # Normalize distance to a 0-1 range (0 at center, 1 at edge)
        normalized_dist = np.sqrt(dist_squared) / (self.radius + 1e-6)

        # Create a smooth falloff (e.g., cosine) for a convex shape
        # This will be 1 at the center and 0 at the radius edge
        falloff = (np.cos(normalized_dist * np.pi / 2) ** 2)[mask]

        # Apply height increase with falloff
        terrain_map.height_data[y_slice, x_slice][mask] += (
            self.height_increase * falloff
        )

        return True
