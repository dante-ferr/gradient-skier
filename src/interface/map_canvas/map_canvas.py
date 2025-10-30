import customtkinter as ctk
from ._canvas_map_renderer import CanvasMapRenderer
from ._canvas_camera import CanvasCamera
from ._canvas_scroller import CanvasScroller
from ._canvas_click_handler import CanvasClickHandler
from ._canvas_path_renderer import CanvasPathRenderer
from ._canvas_pins_renderer import CanvasPinsRenderer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game._match import Match

class MapCanvas(ctk.CTkCanvas):
    def __init__(self, parent, **kwargs):
        from core import map_manager
        from game import game_manager

        super().__init__(parent, highlightthickness=0, **kwargs)

        self.scroller = CanvasScroller(self)
        self.camera = CanvasCamera(self)
        self.map_renderer = CanvasMapRenderer(self)
        self.pins_renderer = CanvasPinsRenderer(self)
        self.path_renderer = CanvasPathRenderer(self)
        self.click_handler = CanvasClickHandler(self)

        self.after(
            400,
            lambda: self.pins_renderer.render_pin(
                map_manager.map.shelter_coords, "🏕️", pin_id="shelter"  # type: ignore
            ),
        )

        # map_manager.recreate_map()
        map_manager.load_map_from_json()
        self.map_renderer.render_map()

        self.configure(bg="black")

        game_manager.add_on_step_callback(self._match_render_callback)
        game_manager.match_start_callback = self._match_start_callback

    def _match_start_callback(self):
        self.path_renderer.clear_path()

    def _match_render_callback(self, match: "Match"):
        self.path_renderer.render_path(match.path_history)
        self.pins_renderer.render_pin(match.skier_position, "⛷️", pin_id="skier")

    @property
    def zoom_level(self) -> int:
        """The current magnification level of the canvas."""
        return self.camera.zoom_level

    def set_zoom_level(self, value: int, origin_x: int, origin_y: int):
        """
        Sets the zoom level by re-rendering and repositioning existing canvas items
        relative to a given origin point.
        """
        if abs(value - self.camera.zoom_level) < 1e-9:
            return

        old_zoom = self.camera.zoom_level
        self.camera.set_zoom_level(value, origin_x, origin_y)

        # Calculate how much the view needs to shift to keep the origin point stationary
        dx = (origin_x - self.scroller.last_x) * (value / old_zoom - 1)
        dy = (origin_y - self.scroller.last_y) * (value / old_zoom - 1)

        self.map_renderer.rescale()
        self.path_renderer.rescale()
        self.pins_renderer.rescale()

        self.scroller.last_x -= int(dx)
        self.scroller.last_y -= int(dy)
        self.scan_dragto(self.scroller.last_x, self.scroller.last_y, gain=1)

    def canvas_to_map_coords(self, canvas_x: int, canvas_y: int) -> tuple[int, int]:
        """
        Converts canvas screen coordinates to map grid coordinates.
        """
        # Get the current view offset of the canvas
        view_x = self.canvasx(0)
        view_y = self.canvasy(0)

        # Calculate the world coordinates by accounting for the view offset
        world_x = canvas_x + view_x
        world_y = canvas_y + view_y

        # Convert world coordinates to map grid coordinates by dividing by the zoom level
        map_x = int(world_x / self.zoom_level)
        map_y = int(world_y / self.zoom_level)

        return map_x, map_y
