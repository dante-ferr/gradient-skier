import sys
import os
from pathlib import Path
from utils import Config as ConfigBase

class Config(ConfigBase):

    def __init__(self):
        if getattr(sys, "frozen", False):
            self.root_path = Path(sys._MEIPASS)
            self.config_path = self.root_path / "config.json"
        else:
            src_dir = Path(__file__).resolve().parent
            self.root_path = src_dir.parent
            self.config_path = src_dir / "config.json"

        if not self.config_path.exists():
            print(f"\n[CRITICAL] Config NOT found at: {self.config_path}")
            if getattr(sys, "frozen", False):
                print(f"[DEBUG] Listing _MEIPASS root ({self.root_path}):")
                try:
                    for item in self.root_path.iterdir():
                        print(f" - {item.name}")
                except Exception:
                    pass

        super().__init__(self.config_path)

    @property
    def PROJECT_ROOT(self) -> Path:
        return self.root_path

    @property
    def ASSETS_PATH(self):
        return self.root_path / "assets"

    @property
    def TERRAIN_SAVES_PATH(self):
        return self.root_path / "data" / "terrain_saves"


config = Config()
