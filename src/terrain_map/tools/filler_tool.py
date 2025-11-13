from .terrain_tool import TerrainTool
from typing import TYPE_CHECKING
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

        if mask.size == 0:
            return False

        # Apply height increase to the masked area
        terrain_map.height_data[y_slice, x_slice][mask] += self.height_increase

        return True
