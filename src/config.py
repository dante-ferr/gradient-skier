import sys
from utils import Config as ConfigBase
from pathlib import Path


class Config(ConfigBase):
    def __init__(self):
        super().__init__("src/config.json")

        # These are top-level properties
        if self._config_path is not None:
            self.PROJECT_ROOT = self.get_project_root()
            self.ASSETS_PATH = self.PROJECT_ROOT / "assets"
            self.TERRAIN_SAVES_PATH = self.PROJECT_ROOT / "data" / "terrain_saves"

    def get_project_root(self) -> Path:
        """
        Determines the project's root directory, whether running from source
        or as a frozen executable (e.g., from PyInstaller).
        """
        if getattr(sys, "frozen", False):
            # If frozen, the root is the directory containing the executable.
            application_path = Path(sys.executable)
            return application_path.parent
        else:
            # If not frozen, we are running from source. The project root is derived
            # from this file's location.
            return Path(__file__).resolve().parent.parent


config = Config()
