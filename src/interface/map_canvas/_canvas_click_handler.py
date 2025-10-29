from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .map_canvas import MapCanvas


class CanvasClickHandler:
    """Handles click events on the map canvas to start a match."""

    def __init__(self, canvas: "MapCanvas"):
        self.canvas = canvas
        self.canvas.bind("<Button-1>", self._on_canvas_click)

    def _on_canvas_click(self, event):
        """
        Callback for the left-click event on the canvas.

        If a match is not currently running, this method converts the click's
        screen coordinates to map coordinates and starts a new match from that point,
        provided it's a valid starting location.
        """
        from game import game_manager
        from core import map_manager

        # Do nothing if a match is already in progress
        if game_manager.match:
            print("Cannot start a new match while one is in progress.")
            return

        # Convert screen coordinates (event.x, event.y) to map grid coordinates
        map_x, map_y = self.canvas.canvas_to_map_coords(event.x, event.y)

        # Check if the selected point is a valid start point on the current map
        if map_manager.map and map_manager.map.is_valid_start_point(map_x, map_y):
            print(f"Valid start point clicked. Starting match at ({map_x}, {map_y}).")
            game_manager.run_match_simulation((map_x, map_y))
        else:
            print(
                f"Invalid start point at ({map_x}, {map_y}). Please click on a higher altitude area."
            )
