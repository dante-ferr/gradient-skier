from PIL import Image, ImageDraw, ImageFont, ImageFilter
from PIL.ImageTk import PhotoImage
from interface.components.svg_image import SvgImage
import cairosvg
from io import BytesIO
from config import config


class EmojiPin:
    """
    A factory class that creates a composite image of a pin with an emoji on top.
    This approach avoids transparency issues with CTk widgets on a canvas
    by rendering the final pin as a single RGBA image.
    """

    def __init__(
        self,
        emoji: str,
        pin_color: str = "#FFFFFF",
        size: tuple[int, int] = (32, 32),
    ):
        """
        Initializes the EmojiPin factory.

        Args:
            emoji (str): The emoji character to display on the pin.
            pin_color (str): The fill color for the pin SVG.
            size (tuple[int, int]): The size of the pin image.
        """
        self.emoji = emoji
        self.pin_color = pin_color
        self.size = size
        self._cached_image: PhotoImage | None = None

    def get_image(self) -> PhotoImage:
        """
        Generates the composite pin image and returns it as a PhotoImage.
        The image is cached to avoid re-rendering on subsequent calls.
        """
        if self._cached_image:
            return self._cached_image

        pin_svg_path = str(config.ASSETS_PATH.joinpath("svg", "pin.svg"))
        pin_image_obj = SvgImage(
            svg_path=pin_svg_path, fill=self.pin_color, size=self.size
        )
        pin_image = pin_image_obj.pil_image

        shadow_offset = (0, 2)
        shadow_blur_radius = 5
        shadow_color = (0, 0, 0, 230)  # Darker semi-transparent black

        shadow_base = Image.new("RGBA", pin_image.size, shadow_color)
        shadow_mask = pin_image.getchannel("A")
        shadow_image = Image.new("RGBA", pin_image.size)
        shadow_image.paste(shadow_base, (0, 0), shadow_mask)

        blurred_shadow = shadow_image.filter(
            ImageFilter.GaussianBlur(radius=shadow_blur_radius)
        )

        composite_image = Image.new("RGBA", self.size, (0, 0, 0, 0))
        composite_image.paste(blurred_shadow, shadow_offset, blurred_shadow)
        composite_image.paste(pin_image, (0, 0), pin_image)

        try:
            emoji_image = self._render_emoji_image()
            # Calculate position to paste the emoji onto the pin's head
            paste_x = (self.size[0] - emoji_image.width) // 2
            paste_y = int(self.size[1] * 0.38) - (emoji_image.height // 2)
            composite_image.paste(emoji_image, (paste_x, paste_y), emoji_image)
        except Exception as e:
            print(f"Could not render emoji '{self.emoji}': {e}")
            # If emoji rendering fails, we still return the base pin.

        self._cached_image = PhotoImage(composite_image)
        return self._cached_image

    def _render_emoji_image(self) -> Image.Image:
        """
        Renders an emoji from the font file into a PIL Image using cairosvg.
        This bypasses FreeType's lack of SVG hooks.
        """
        font_path = str(config.ASSETS_PATH.joinpath("fonts", "NotoColorEmoji.ttf"))
        emoji_size_factor = 0.6
        emoji_pixel_size = int(self.size[0] * emoji_size_factor)

        svg_content = f"""
        <svg width="{emoji_pixel_size}" height="{emoji_pixel_size}" xmlns="http://www.w3.org/2000/svg">
            <style>
                @font-face {{
                    font-family: 'NotoColorEmoji';
                    src: url('file://{font_path}');
                }}
            </style>
            <text x="50%" y="50%" font-family="NotoColorEmoji" font-size="{emoji_pixel_size}"
                  dominant-baseline="central" text-anchor="middle">{self.emoji}</text>
        </svg>
        """

        png_data = cairosvg.svg2png(bytestring=svg_content.encode("utf-8"))
        return Image.open(BytesIO(png_data))
