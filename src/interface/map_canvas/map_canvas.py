import customtkinter as ctk
from ._canvas_map_renderer import CanvasMapRenderer
from ._canvas_camera import CanvasCamera
from ._canvas_scroller import CanvasScroller
from ._canvas_click_handler import CanvasClickHandler
from ._canvas_path_renderer import CanvasPathRenderer
from ._canvas_pins_renderer import CanvasPinsRenderer
from typing import TYPE_CHECKING, Optional, cast

if TYPE_CHECKING:
    from game._path import Path


class MapCanvas(ctk.CTkCanvas):

    def __init__(self, parent, **kwargs):
        from game import game_manager

        super().__init__(parent, highlightthickness=0, **kwargs)

        self.scroller = CanvasScroller(self)
        self.camera = CanvasCamera(self)
        self.map_renderer = CanvasMapRenderer(self)
        self.pins_renderer = CanvasPinsRenderer(self)
        self.path_renderer = CanvasPathRenderer(self)
        self.click_handler = CanvasClickHandler(self)

        self._setup_pins()

        self.map_renderer.render_map()
        self.configure(bg="black")

        game_manager.add_on_path_recalculated_callback(self._path_recalculated_callback)
        game_manager.add_on_game_start_callback(self._on_new_game_started)

        self.gradient_display: Optional[int] = None
        self.bind("<Motion>", self._on_mouse_motion)

    def _setup_pins(self):
        """Renders the start and end pins."""
        from core import map_manager
        from game import game_manager

        # We need to wait for the map to load before rendering pins,
        # so this is the safest way to ensure map_manager.map is available.
        if map_manager.map is None:
            # If map is not ready yet, defer the setup
            self.after(50, self._setup_pins)
            return

        # Initial call to render the fixed start and end pins
        self.pins_renderer.render_pin(game_manager.start_point, "🏠", pin_id="start")
        self.pins_renderer.render_pin(game_manager.end_point, "🏁", pin_id="end")

    def _path_recalculated_callback(self, path: "Path"):
        """
        Callback for when the pathfinding algorithm generates a new path.
        """
        self.path_renderer.render_path(path.nodes)

    def _on_new_game_started(self):
        """
        Callback for when a new game is started.
        """
        self.map_renderer.render_map()

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

    def _on_mouse_motion(self, event):
        """
        Callback for mouse motion events. Displays the gradient magnitude
        (steepness) of the terrain tile under the cursor.
        """
        from core import map_manager

        x, y = event.x, event.y

        # Only check if the player is allowed to interact (i.e., not calculating a path)
        from state_managers import game_state_manager

        player_can_interact_var = cast(
            ctk.BooleanVar, game_state_manager.vars["player_can_interact"]
        )

        if player_can_interact_var.get():
            map_x, map_y = self.canvas_to_map_coords(x, y)

            if (
                map_manager.map
                and 0 <= map_x < map_manager.map.width
                and 0 <= map_y < map_manager.map.height
            ):
                gradient_magnitude = self._get_gradient_info(map_x, map_y)
                self._display_gradient(gradient_magnitude)
            else:
                self._clear_gradient_display()
        else:
            self._clear_gradient_display()

    def _get_gradient_info(self, map_x: int, map_y: int) -> str:
        """
        Gets the gradient magnitude (steepness) at the given map coordinates.
        Uses the available `get_gradient_magnitude_at` method.
        """
        from core import map_manager

        if map_manager.map:
            # Use gradient magnitude which directly relates to climb cost
            magnitude = map_manager.map.get_gradient_magnitude_at(map_x, map_y)
            return f"{magnitude:.2f}"
        return "No map loaded"

    def _display_gradient(self, gradient_text: str):
        """Displays the gradient information in the state manager."""
        from state_managers import canvas_state_manager

        hovered_gradient_var = cast(
            ctk.StringVar, canvas_state_manager.vars["hovered_gradient"]
        )
        hovered_gradient_var.set(gradient_text)

    def _clear_gradient_display(self):
        """Clears the gradient information from the canvas."""
        from state_managers import canvas_state_manager

        hovered_gradient_var = cast(
            ctk.StringVar, canvas_state_manager.vars["hovered_gradient"]
        )
        hovered_gradient_var.set("")
