from typing import TYPE_CHECKING
import numpy as np
from PIL import Image, ImageTk
from matplotlib import cm
from core import map_manager

if TYPE_CHECKING:
    from .map_canvas import MapCanvas


class CanvasMapRenderer:
    """Handles drawing objects onto the MapCanvas."""

    def __init__(self, canvas: "MapCanvas"):
        from core import map_manager

        self.canvas = canvas
        self._reset_cache()

        map_manager.add_map_change_callback(self.change_map)

    def _reset_cache(self):
        self.image_cache = {}
        self.original_pil_images = {}
        self.current_photo_images = {}

    def _create_terrain_image(self):
        terrain_map = map_manager.map

        height_data = terrain_map.height_data
        colored_data = cm.terrain(height_data / 255.0)  # type: ignore

        image_data = (colored_data * 255).astype(np.uint8)
        pil_image = Image.fromarray(image_data, "RGBA")

        self.original_pil_images["terrain_map"] = pil_image

        photo_image = ImageTk.PhotoImage(pil_image)
        self.image_cache[("terrain_map", 1)] = photo_image
        self.current_photo_images["terrain_map"] = photo_image

        return photo_image

    def render_map(self):
        """Generates a new map and renders it on the canvas."""
        print("rendering map")
        tag = "terrain_map"
        self._reset_cache()
        new_photo_image = self._create_terrain_image()

        # Check if the image item already exists
        if self.canvas.find_withtag(tag):
            self.canvas.itemconfig(tag, image=new_photo_image)
        else:
            self.canvas.create_image(0, 0, image=new_photo_image, anchor="nw", tags=tag)

        self.rescale()

    def change_map(self):
        tag = "terrain_map"

        self._reset_cache()
        new_photo_image = self._create_terrain_image()
        self.canvas.itemconfig(tag, image=new_photo_image)

        self.rescale()

    def rescale(self):
        """Rescales the 'terrain_map' image based on the current canvas zoom level."""
        tag = "terrain_map"
        zoom = self.canvas.zoom_level
        cache_key = (tag, zoom)

        if cache_key in self.image_cache:
            new_photo_image = self.image_cache[cache_key]
        else:
            original_pil_image = self.original_pil_images.get(tag)
            if not original_pil_image:
                return

            new_width = int(original_pil_image.width * zoom)
            new_height = int(original_pil_image.height * zoom)

            scaled_pil_image = original_pil_image.resize(
                (new_width, new_height), Image.NEAREST  # type: ignore
            )
            new_photo_image = ImageTk.PhotoImage(scaled_pil_image)
            self.image_cache[cache_key] = new_photo_image

        old_coords = self.canvas.coords(tag)
        old_x, old_y = old_coords if old_coords else (0, 0)
        self.canvas.coords(tag, old_x, old_y)
        self.canvas.itemconfig(tag, image=new_photo_image)
        self.current_photo_images[tag] = new_photo_image
