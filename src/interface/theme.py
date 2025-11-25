import json
import sys
import os
from pathlib import Path

class Theme:
    def __init__(self, theme_name: str):
        self.path = self._get_asset_path(f"themes/{theme_name}.json")

        with open(self.path, "r") as file:
            data = json.load(file)

        self.icon_color = data["CTkLabel"]["text_color"][1]
        self.select_border_color = data["CTkButton"]["border_color"][1]

    def _get_asset_path(self, relative_path: str) -> Path:
        """
        Resolves the path to an asset, working for both local dev and PyInstaller.
        """
        # 1. Check if running as PyInstaller OneFile (sys._MEIPASS exists)
        if hasattr(sys, "_MEIPASS"):
            base_path = Path(sys._MEIPASS) / "assets"

        # 2. Local Development mode
        else:
            # Current file is src/interface/theme.py
            # We need to go up two levels (interface -> src) to find 'assets' folder in root
            # Adjust .parent count based on your folder structure
            base_path = Path(__file__).parent.parent.parent / "assets"

        return base_path / relative_path


default_theme = "orange"
theme = Theme(default_theme)
