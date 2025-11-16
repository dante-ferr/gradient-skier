from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .map_canvas import MapCanvas


class CanvasPathRenderer:
    """Handles drawing the path on the canvas."""

    PATH_TAG = "path"
    PATH_COLOR = "red"
    PATH_WIDTH = 2

    def __init__(self, canvas: "MapCanvas"):
        self.canvas = canvas
        self.map_path_coords: list[tuple[float, float]] = []

    def render_path(self, path_points: list[tuple[float, float]]):
        """
        Renders the path on the canvas.

        Args:
            path_points (list[tuple[float, float]]): A list of (x, y) map coordinates.
        """
        self.map_path_coords = path_points
        self.canvas.delete(self.PATH_TAG)

        if len(path_points) < 2:
            return

        zoom = self.canvas.zoom_level
        # Convert map coordinates to canvas coordinates
        canvas_coords = [
            coord
            for point in path_points
            for coord in ((point[0] + 0.5) * zoom, (point[1] + 0.5) * zoom)
        ]

        self.canvas.create_line(
            *canvas_coords,
            fill=self.PATH_COLOR,
            width=self.PATH_WIDTH,
            tags=(self.PATH_TAG,)
        )

    def rescale(self):
        """Rescales the path based on the current canvas zoom level."""
        self.render_path(self.map_path_coords)

    def clear_path(self):
        """Removes the path from the canvas and clears the stored coordinates."""
        self.map_path_coords = []
        self.canvas.delete(self.PATH_TAG)
