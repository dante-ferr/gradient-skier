import customtkinter as ctk
from config import config
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .map_canvas import MapCanvas


class CanvasScroller:
    def __init__(self, canvas: "MapCanvas"):
        self.canvas = canvas
        self.canvas.after(1, self._center_canvas)

        self.last_x: int = 0
        self.last_y: int = 0

        self.scrolling = False

        self.canvas.after(250, self.configure_zoom)

        self.canvas.bind("<Configure>", self._on_resize)

    def configure_zoom(self):
        from state_managers import canvas_state_manager

        initial_zoom: int = min(
            self.canvas_size[0] // config.MAP_WIDTH,
            self.canvas_size[1] // config.MAP_HEIGHT,
        )

        initial_zoom_var = cast(
            ctk.DoubleVar, canvas_state_manager.vars["initial_zoom"]
        )
        initial_zoom_var.set(initial_zoom)

        self.min_zoom = initial_zoom - config.canvas.ZOOM_LEFT_OFFSET
        self.max_zoom = initial_zoom + config.canvas.ZOOM_RIGHT_OFFSET

        self._bind_scroll_events()

        self._set_zoom(initial_zoom, self.canvas_size[0] // 2, self.canvas_size[1] // 2)
        self._center_canvas()

    def _bind_scroll_events(self):
        from state_managers import canvas_state_manager

        canvas_state_manager.add_callback("zoom", self._on_zoom_change)

        self.canvas.bind("<ButtonPress-3>", self._start_scroll)
        self.canvas.bind("<B3-Motion>", self._on_scroll)
        self.canvas.bind("<ButtonRelease-3>", self._stop_scroll)
        # For Windows and MacOS
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        # For Linux
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)

    def _on_resize(self, event):
        """Handle window resizing."""
        self.configure_zoom()

    def _start_scroll(self, event):
        """Start scrolling when the right mouse button is pressed."""
        self.scrolling = True
        self.scroll_start_x = event.x - self.last_x
        self.scroll_start_y = event.y - self.last_y

    def _on_scroll(self, event):
        """Scroll the canvas based on mouse movement."""
        if self.scrolling:
            scroll_x = int(event.x - self.scroll_start_x)
            scroll_y = int(event.y - self.scroll_start_y)
            scroll_x, scroll_y = self._clamped_scroll_position(scroll_x, scroll_y)

            self.canvas.scan_dragto(scroll_x, scroll_y, gain=1)
            self.last_x = scroll_x
            self.last_y = scroll_y

    def _clamped_scroll_position(self, x: int, y: int) -> tuple[int, int]:
        """Clamp the scroll position to the canvas boundaries."""
        from core import map_manager

        zoom = self.canvas.zoom_level

        canvas_width, canvas_height = self.canvas_size
        map_pixel_width, map_pixel_height = (
            map_manager.map.width * zoom,
            map_manager.map.height * zoom,
        )

        # Calculate boundaries to ensure map corners don't pass the canvas center.
        min_x = -map_pixel_width + canvas_width // 2
        max_x = +canvas_width // 2
        min_y = -map_pixel_height + canvas_height // 2
        max_y = +canvas_height // 2

        x = int(max(min_x, min(max_x, x)))
        y = int(max(min_y, min(max_y, y)))

        return x, y

    def _center_canvas(self):
        from core import map_manager

        if not map_manager.map:
            return

        canvas_width, canvas_height = self.canvas_size
        zoom = self.canvas.zoom_level
        canvas_center_x = canvas_width // 2 - (map_manager.map.width * zoom) // 2
        canvas_center_y = canvas_height // 2 - (map_manager.map.height * zoom) // 2

        self.canvas.scan_dragto(canvas_center_x, canvas_center_y, gain=1)
        self.last_x = canvas_center_x
        self.last_y = canvas_center_y

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling for zooming."""
        zoom = -1
        if event.num == 5 or event.delta < 0:
            # Scroll down, zoom out
            zoom = self.canvas.zoom_level - config.canvas.STEPS_PER_SCROLL
        elif event.num == 4 or event.delta > 0:
            # Scroll up, zoom in
            zoom = self.canvas.zoom_level + config.canvas.STEPS_PER_SCROLL

        if zoom != -1:
            self._set_zoom(zoom, event.x, event.y)

    def _set_zoom(self, new_zoom, origin_x: int = 0, origin_y: int = 0):
        from state_managers import canvas_state_manager

        self._on_zoom_change(new_zoom, origin_x, origin_y)
        zoom_var = cast(ctk.IntVar, canvas_state_manager.vars["zoom"])
        zoom_var.set(new_zoom)

    def _on_zoom_change(self, new_zoom, origin_x: int = 0, origin_y: int = 0):
        """Clamp new_zoom and execute the zoom at each frame."""
        new_zoom = int(new_zoom)
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
        if new_zoom != self.canvas.zoom_level:
            self.canvas.set_zoom_level(new_zoom, origin_x, origin_y)

    @property
    def canvas_size(self):
        return (self.canvas.winfo_width(), self.canvas.winfo_height())

    def _stop_scroll(self, event):
        """Stop scrolling when the right mouse button is released."""
        self.scrolling = False
