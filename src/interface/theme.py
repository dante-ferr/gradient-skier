import json
from pathlib import Path


class Theme:
    ASSETS_PATH = Path(__file__).resolve().parent.parent.parent / "assets"

    def __init__(self, theme_name: str):
        self.path = f"{self.ASSETS_PATH}/themes/{theme_name}.json"

        with open(self.path, "r") as file:
            data = json.load(file)

        self.icon_color = data["CTkLabel"]["text_color"][1]
        self.select_border_color = data["CTkButton"]["border_color"][1]


default_theme = "rime"
theme = Theme(default_theme)
