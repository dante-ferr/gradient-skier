import numpy as np
from typing import TYPE_CHECKING
from config import config

if TYPE_CHECKING:
    from terrain_map import TerrainMap


class TerrainTool:
    """
    Base class for all terraforming tools. Defines the structure for
    applying effects to the terrain map.
    """

    def __init__(self, tool_name: str):
        self.name = tool_name
        self.radius = config.TOOL.TOOL_RADIUS

    def apply(self, terrain_map: "TerrainMap", center_x: int, center_y: int) -> bool:
        """
        Applies the tool effect to the given terrain map at the center coordinates.
        This method must be overridden by derived classes.

        Returns True if modification was successful, False otherwise.
        """
        raise NotImplementedError(
            "The 'apply' method must be implemented by derived tool classes."
        )

    def _get_area_mask(
        self, terrain_map: "TerrainMap", center_x: int, center_y: int
    ) -> tuple[np.ndarray, slice, slice]:
        """
        Calculates the mask for the circular area of effect (AoE) and
        returns the slice indices for the affected region.
        """
        y_min = max(0, center_y - self.radius)
        y_max = min(terrain_map.height, center_y + self.radius + 1)
        x_min = max(0, center_x - self.radius)
        x_max = min(terrain_map.width, center_x + self.radius + 1)

        # Create coordinates grid for the sliced area
        Y, X = np.ogrid[y_min:y_max, x_min:x_max]
        dist_squared = (X - center_x) ** 2 + (Y - center_y) ** 2

        mask = dist_squared <= self.radius**2
        return mask, slice(y_min, y_max), slice(x_min, x_max)
