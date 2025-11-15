import numpy as np
from scipy.ndimage import sobel
from config import config
from .tools import ExcavatorTool, FillerTool, GraderTool
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tools import TerrainTool
class TerrainMap:
    """
    Holds the 2D height data for the terrain and provides
    pre-calculated gradient maps for pathfinding cost analysis.
    Also manages terraforming tool application.
    """

    def __init__(self, height_data: np.ndarray):
        """
        Initializes the map with 2D height data (0-255).
        """
        self.height_data: np.ndarray = height_data.astype(float)
        self.height, self.width = height_data.shape

        # Using a dictionary of tool objects follows the Strategy pattern.
        self._tools: "dict[str, TerrainTool]" = {
            "excavator": ExcavatorTool(),
            "filler": FillerTool(),
            "grader": GraderTool(),
        }

        # Pre-calculate gradient maps
        self._calculate_gradients()

    def _calculate_gradients(self):
        """
        Uses a Sobel filter to calculate the partial derivatives (gradient)
        of the terrain, storing them in gradient_x and gradient_y.
        """
        # gradient_y corresponds to df/dy (changes along axis 0).
        self.gradient_y = sobel(self.height_data, axis=0)
        # gradient_x corresponds to df/dx (changes along axis 1).
        self.gradient_x = sobel(self.height_data, axis=1)

    def get_height_at(self, px: int, py: int) -> float:
        """Gets the height at a specific pixel coordinate."""
        if 0 <= px < self.width and 0 <= py < self.height:
            return self.height_data[py, px]
        return 0.0

    def get_gradient_magnitude_at(self, px: int, py: int) -> float:
        """
        Calculates the gradient magnitude (steepness) at a pixel, which is
        used as the core of the A* pathfinding cost.
        """
        if 0 <= px < self.width and 0 <= py < self.height:
            gx = self.gradient_x[py, px]
            gy = self.gradient_y[py, px]
            return np.sqrt(gx**2 + gy**2)
        return np.inf  # Out-of-bounds is infinitely expensive

    def apply_tool(self, tool_type: str, center_x: int, center_y: int) -> bool:
        """
        Applies a tool's effect and recalculates gradients if the map was modified.
        Returns True if the modification was successful.
        """
        tool = self._tools.get(tool_type)

        if tool is None:
            raise Exception(f"Unknown tool type: {tool_type}")

        modified = tool.apply(self, center_x, center_y)

        if modified:
            # Gradients must be recalculated after any terrain modification.
            self._calculate_gradients()
            return True

        return False
