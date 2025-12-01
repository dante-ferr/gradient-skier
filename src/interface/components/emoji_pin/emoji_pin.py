from PIL import Image, ImageFont, ImageFilter, ImageDraw
from PIL.ImageTk import PhotoImage
from interface.components.svg_image import SvgImage
from config import config


class EmojiPin:
    EMOJI_SIZE_FACTOR = 0.7
    # Noto Color Emoji has embedded bitmaps, with 109px being a common size.
    _BITMAP_FONT_SIZE = 109

    def __init__(
        self,
        emoji: str,
        pin_color: str = "#FFFFFF",
        size: tuple[int, int] = (32, 32),
    ):
        self.emoji = emoji
        self.pin_color = pin_color
        self.size = size
        self._cached_image: PhotoImage | None = None
        self._pil_image: Image.Image | None = None

    def get_image(self) -> PhotoImage:
        if self._cached_image:
            return self._cached_image

        pil_img = self.get_pil_image()
        self._cached_image = PhotoImage(pil_img)
        return self._cached_image

    def get_pil_image(self) -> Image.Image:
        if self._pil_image:
            return self._pil_image

        # 1. Create the base pin image from an SVG template.
        pin_svg_path = str(config.ASSETS_PATH.joinpath("svg", "pin.svg"))
        pin_image_obj = SvgImage(
            svg_path=pin_svg_path, fill=self.pin_color, size=self.size
        )
        pin_image = pin_image_obj.pil_image

        # 2. Shadow
        shadow_blur_radius = 2
        shadow_color = (0, 0, 0, 230)
        shadow_base = Image.new("RGBA", pin_image.size, shadow_color)
        shadow_mask = pin_image.getchannel("A")
        shadow_image = Image.new("RGBA", pin_image.size)
        shadow_image.paste(shadow_base, (0, 0), shadow_mask)
        blurred_shadow = shadow_image.filter(
            ImageFilter.GaussianBlur(radius=shadow_blur_radius)
        )

        # 3. Composite the shadow and pin.
        composite_image = Image.new("RGBA", self.size, (0, 0, 0, 0))
        composite_image.paste(blurred_shadow, (0, 2), blurred_shadow)
        composite_image.paste(pin_image, (0, 0), pin_image)

        # 4. Render the emoji on top of the pin.
        self._draw_emoji_on_image(composite_image)

        self._pil_image = composite_image
        return self._pil_image

    def _draw_emoji_on_image(self, image: Image.Image) -> None:
        """
        Draws the emoji onto the image using native Pillow rendering.
        This method renders the emoji at a high resolution and then downscales it
        to prevent quality loss and avoid rendering errors with bitmap fonts.
        """
        font_path = str(config.ASSETS_PATH.joinpath("fonts", "NotoColorEmoji.ttf"))

        # Load the font at its native bitmap size to prevent a Pillow error.
        try:
            font = ImageFont.truetype(font_path, self._BITMAP_FONT_SIZE)
        except OSError:
            print(f"CRITICAL: Emoji font missing or invalid at {font_path}")
            raise

        # 1. Create a large temporary canvas for the raw emoji
        temp_size = (150, 150)
        temp_img = Image.new("RGBA", temp_size, (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)

        # 2. Draw the emoji onto the temporary canvas.
        temp_draw.text(
            (temp_size[0] / 2, temp_size[1] / 2),
            self.emoji,
            font=font,
            anchor="mm",
            embedded_color=True,
            fill="black",
        )

        # 3. Crop and resize the emoji to fit the pin.
        target_emoji_size = int(self.size[0] * self.EMOJI_SIZE_FACTOR)
        bbox = temp_img.getbbox()
        if bbox:
            temp_img = temp_img.crop(bbox)

            # Resize while maintaining aspect ratio.
            temp_img.thumbnail(
                (target_emoji_size, target_emoji_size), Image.Resampling.LANCZOS
            )

        # 4. Paste the emoji onto the main pin image.
        pin_center_x = self.size[0] // 2
        pin_center_y = int((self.size[1] / 2) * 0.9)

        paste_x = pin_center_x - (temp_img.width // 2)
        paste_y = pin_center_y - (temp_img.height // 2)

        image.paste(temp_img, (paste_x, paste_y), temp_img)
