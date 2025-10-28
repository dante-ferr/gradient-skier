from typing import TYPE_CHECKING
import numpy as np
from PIL import Image, ImageTk
from matplotlib import cm
from core import map_manager

if TYPE_CHECKING:
    from .map_canvas import MapCanvas


class CanvasRenderer:
    """Handles drawing objects onto the MapCanvas."""

    def __init__(self, canvas: "MapCanvas"):
        from core.map_manager import map_manager

        self.canvas = canvas
        self.image_cache = {}
        self.original_pil_images = {}
        self.current_photo_images = {}

        map_manager.add_map_recreate_callback(self._clean_cache)

    def _clean_cache(self):
        self.image_cache = {}
        self.original_pil_images = {}
        self.current_photo_images = {}

    def render_map(self):
        """Generates a new map and renders it on the canvas."""
        terrain_map = map_manager.map
        if not terrain_map:
            return

        # Normalize height data (0-1) and apply a colormap (e.g., terrain)
        height_data = terrain_map.height_data
        colored_data = cm.terrain(height_data / 255.0)

        # Convert to an 8-bit RGBA image that PIL/Tkinter can use
        image_data = (colored_data * 255).astype(np.uint8)
        pil_image = Image.fromarray(image_data, "RGBA")

        # Store the original image for later rescaling
        self.original_pil_images["terrain_map"] = pil_image

        # Create the initial PhotoImage at 1x zoom
        photo_image = ImageTk.PhotoImage(pil_image)
        self.image_cache[("terrain_map", 1)] = photo_image
        self.current_photo_images["terrain_map"] = photo_image

        self.canvas.create_image(
            0, 0, image=photo_image, anchor="nw", tags="terrain_map"
        )

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
                return  # No original image to scale

            new_width = original_pil_image.width * zoom
            new_height = original_pil_image.height * zoom

            # Use NEAREST for sharp pixels, which is good for this type of map
            scaled_pil_image = original_pil_image.resize(
                (new_width, new_height), Image.NEAREST
            )
            new_photo_image = ImageTk.PhotoImage(scaled_pil_image)
            self.image_cache[cache_key] = new_photo_image

        self.canvas.itemconfig(tag, image=new_photo_image)
        # Keep a reference to the new image to prevent garbage collection
        self.current_photo_images[tag] = new_photo_image
