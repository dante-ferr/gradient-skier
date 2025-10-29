from typing import TYPE_CHECKING
from interface.components.emoji_pin import EmojiPin

if TYPE_CHECKING:
    from .map_canvas import MapCanvas


class CanvasPinsRenderer:
    def __init__(self, canvas: "MapCanvas"):
        self.canvas = canvas
        self.pins = {}

    def render_pin(
        self, position: tuple[float, float], emoji: str = "⛷️", pin_id: str = "skier"
    ):
        """
        Renders or updates a pin on the canvas. If a pin with the given pin_id
        already exists, it's moved. Otherwise, a new pin is created.

        Args:
            position (tuple[float, float]): The (x, y) map coordinates for the pin.
            emoji (str): The emoji to display on the pin.
            pin_id (str): A unique identifier for the pin (e.g., 'skier', 'shelter').
        """
        map_x, map_y = position
        zoom = self.canvas.zoom_level
        canvas_x = map_x * zoom
        canvas_y = map_y * zoom

        if pin_id in self.pins:
            # Pin exists, just move it
            self.canvas.coords(pin_id, canvas_x, canvas_y)
            self.pins[pin_id]["map_pos"] = position
        else:
            # Pin doesn't exist, create it
            pin_factory = EmojiPin(emoji=emoji, size=(56, 56))
            pin_image = pin_factory.get_image()

            # Use create_image with the 'tags' parameter to identify the pin
            canvas_item_id = self.canvas.create_image(
                canvas_x, canvas_y, image=pin_image, anchor="s", tags=(pin_id,)
            )

            # Store pin info. We must keep a reference to the image.
            self.pins[pin_id] = {
                "image": pin_image,
                "canvas_item_id": canvas_item_id,
                "map_pos": position,
            }
