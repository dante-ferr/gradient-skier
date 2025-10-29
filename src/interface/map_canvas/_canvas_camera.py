from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .map_canvas import MapCanvas


class CanvasCamera:

    def __init__(self, canvas: "MapCanvas"):
        self.canvas = canvas
        self._zoom_level = 1
        # The offset (in grid units) for drawing, used to simulate camera movement.
        self._grid_draw_offset: tuple[int, int] = (0, 0)

    @property
    def zoom_level(self) -> int:
        """The current magnification level of the canvas."""
        return self._zoom_level

    def set_zoom_level(self, value: int, origin_x: int, origin_y: int):
        """Sets the zoom level, clamping it to a minimum of 1."""
        if value < 1:
            value = 1
        if abs(value - self._zoom_level) < 1e-9:
            return

        self._zoom_level = value
