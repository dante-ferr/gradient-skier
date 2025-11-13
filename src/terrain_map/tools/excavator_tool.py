from .terrain_tool import TerrainTool
from typing import TYPE_CHECKING
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

        if mask.size == 0:
            return False

        # Apply depth reduction to the masked area
        terrain_map.height_data[y_slice, x_slice][mask] -= self.depth

        # Ensure height remains non-negative
        terrain_map.height_data = terrain_map.height_data.clip(min=0)

        return True
