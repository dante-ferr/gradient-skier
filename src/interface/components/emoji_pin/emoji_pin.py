from PIL import Image, ImageFont, ImageFilter
from PIL.ImageTk import PhotoImage
from interface.components.svg_image import SvgImage
from config import config
from pilmoji import Pilmoji


class EmojiPin:
    EMOJI_SIZE_FACTOR = 0.7

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

        # 1. Base do Pin (SVG)
        pin_svg_path = str(config.ASSETS_PATH.joinpath("svg", "pin.svg"))
        pin_image_obj = SvgImage(
            svg_path=pin_svg_path, fill=self.pin_color, size=self.size
        )
        pin_image = pin_image_obj.pil_image

        # 2. Sombra
        shadow_blur_radius = 5
        shadow_color = (0, 0, 0, 230)
        shadow_base = Image.new("RGBA", pin_image.size, shadow_color)
        shadow_mask = pin_image.getchannel("A")
        shadow_image = Image.new("RGBA", pin_image.size)
        shadow_image.paste(shadow_base, (0, 0), shadow_mask)
        blurred_shadow = shadow_image.filter(
            ImageFilter.GaussianBlur(radius=shadow_blur_radius)
        )

        # 3. Composição Inicial
        composite_image = Image.new("RGBA", self.size, (0, 0, 0, 0))
        composite_image.paste(blurred_shadow, (0, 2), blurred_shadow)
        composite_image.paste(pin_image, (0, 0), pin_image)

        # 4. Renderização do Emoji
        try:
            self._draw_emoji_on_image(composite_image)
        except Exception as e:
            print(f"Could not render emoji '{self.emoji}': {e}")

        self._pil_image = composite_image
        return self._pil_image

    def _draw_emoji_on_image(self, image: Image.Image) -> None:
        """
        Draws the emoji directly onto the image using Pilmoji.
        Uses a bundled standard font to calculate correct sizing.
        """
        font_path = str(config.ASSETS_PATH.joinpath("fonts", "Roboto-Regular.ttf"))

        emoji_size = int(self.size[0] * self.EMOJI_SIZE_FACTOR)

        try:
            font = ImageFont.truetype(font_path, emoji_size)
        except OSError:
            print(f"Font not found at {font_path}. Fallback to default.")
            font = ImageFont.load_default()

        with Pilmoji(image) as pilmoji:
            em_x = int((self.size[0] - emoji_size) / 2)
            em_y = int(((self.size[1] - emoji_size) / 2) * 0.5)

            pilmoji.text(
                (em_x, em_y),
                self.emoji,
                font=font,
                anchor="mm",
                emoji_position_offset=(0, 0),
            )
