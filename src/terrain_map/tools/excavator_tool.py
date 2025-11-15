from .terrain_tool import TerrainTool
from typing import TYPE_CHECKING
import numpy as np
from config import config

if TYPE_CHECKING:
    from terrain_map import TerrainMap


class ExcavatorTool(TerrainTool):
    """
    Tool that lowers the terrain height (digging a crater).
    """

    def __init__(self):
        super().__init__("Excavator")
        self.depth = config.TOOL.EXCAVATOR_DEPTH

    def apply(self, terrain_map: "TerrainMap", center_x: int, center_y: int) -> bool:
        mask, y_slice, x_slice = self._get_area_mask(terrain_map, center_x, center_y)

        if not mask.any():
            return False

        # Create a grid to calculate distance from the center for the falloff effect
        y_indices, x_indices = np.ogrid[y_slice, x_slice]
        dist_squared = (x_indices - center_x) ** 2 + (y_indices - center_y) ** 2

        # Normalize distance to a 0-1 range (0 at center, 1 at edge)
        # Adding a small epsilon to avoid division by zero if radius is 0
        normalized_dist = np.sqrt(dist_squared) / (self.radius + 1e-6)

        # Create a smooth falloff (e.g., cosine) for a concave shape
        # This will be 1 at the center and 0 at the radius edge
        falloff = (np.cos(normalized_dist * np.pi / 2) ** 2)[mask]

        # Apply depth reduction with falloff
        terrain_map.height_data[y_slice, x_slice][mask] -= self.depth * falloff

        # Ensure height remains non-negative
        np.clip(terrain_map.height_data, 0, None, out=terrain_map.height_data)
        return True
