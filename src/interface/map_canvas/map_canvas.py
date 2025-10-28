import customtkinter as ctk
from ._canvas_renderer import CanvasRenderer
from ._canvas_camera import CanvasCamera

class MapCanvas(ctk.CTkCanvas):
    def __init__(self, parent, **kwargs):
        from core import map_manager

        super().__init__(parent, highlightthickness=0, **kwargs)

        self.camera = CanvasCamera(self)
        self.renderer = CanvasRenderer(self)

        # map_manager.recreate_map()
        map_manager.load_map_from_json()
        self.renderer.render_map()

        self.configure(bg="black")

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
        self.camera.set_zoom_level(value)

        self.renderer.rescale()
