import customtkinter as ctk
from ._canvas_map_renderer import CanvasMapRenderer
from ._canvas_camera import CanvasCamera
from ._canvas_scroller import CanvasScroller
from ._canvas_click_handler import CanvasClickHandler
from ._canvas_path_renderer import CanvasPathRenderer
from ._canvas_pins_renderer import CanvasPinsRenderer
from typing import TYPE_CHECKING, Optional, cast

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

        self.map_renderer.render_map()

        self.configure(bg="black")

        game_manager.add_on_step_callback(self._match_render_callback)
        game_manager.match_start_callback = self._match_start_callback

        self.gradient_display: Optional[int] = None
        self.bind("<Motion>", self._on_mouse_motion)

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

    def _on_mouse_motion(self, event):
        """
        Callback for mouse motion events. Checks if the mouse is over the path
        and displays the gradient information if it is.
        """
        x, y = event.x, event.y

        if self._is_over_path(x, y, 5):  # 5 pixels tolerance
            map_x, map_y = self.canvas_to_map_coords(x, y)
            gradient = self._get_gradient_info(map_x, map_y)
            self._display_gradient(gradient)
        else:
            self._clear_gradient_display()

    def _is_over_path(self, canvas_x: int, canvas_y: int, tolerance: int) -> bool:
        """
        Checks if the given canvas coordinates are within the tolerance distance of any path segment.
        """
        path_coords = self.path_renderer.map_path_coords
        if len(path_coords) < 2:
            return False

        view_x = self.canvasx(0)
        view_y = self.canvasy(0)
        mouse_world_x = canvas_x + view_x
        mouse_world_y = canvas_y + view_y

        zoom = self.zoom_level
        tolerance_sq = tolerance**2

        for i in range(len(path_coords) - 1):
            p1_map, p2_map = path_coords[i], path_coords[i + 1]

            # Convert segment endpoints from map to world coordinates
            p1_world_x = (p1_map[0] + 0.5) * zoom
            p1_world_y = (p1_map[1] + 0.5) * zoom
            p2_world_x = (p2_map[0] + 0.5) * zoom
            p2_world_y = (p2_map[1] + 0.5) * zoom

            # Vector for the line segment
            seg_dx, seg_dy = p2_world_x - p1_world_x, p2_world_y - p1_world_y
            seg_len_sq = seg_dx**2 + seg_dy**2

            if seg_len_sq < 1e-9:  # The segment is essentially a point
                dist_sq = (mouse_world_x - p1_world_x) ** 2 + (
                    mouse_world_y - p1_world_y
                ) ** 2
            else:
                # Project mouse position onto the line segment
                vec_p1_to_mouse_dx = mouse_world_x - p1_world_x
                vec_p1_to_mouse_dy = mouse_world_y - p1_world_y
                dot_product = vec_p1_to_mouse_dx * seg_dx + vec_p1_to_mouse_dy * seg_dy
                t = max(0, min(1, dot_product / seg_len_sq))

                closest_x = p1_world_x + t * seg_dx
                closest_y = p1_world_y + t * seg_dy
                dist_sq = (mouse_world_x - closest_x) ** 2 + (
                    mouse_world_y - closest_y
                ) ** 2

            if dist_sq <= tolerance_sq:
                return True
        return False

    def _get_gradient_info(self, map_x, map_y):
        """Gets the gradient information at the given map coordinates."""
        from core import map_manager

        if map_manager.map:
            gradient = map_manager.map.get_gradient_at(map_x, map_y)
            return f"{gradient[0]:.2f}, {gradient[1]:.2f}"
        return "No map loaded"

    def _display_gradient(self, gradient_text: str):
        """Displays the gradient information on the canvas."""
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
