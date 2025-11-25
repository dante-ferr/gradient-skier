import json
from pathlib import Path
from typing import Any, Dict, Union

class Config:
    """A class to hold and provide access to configuration settings from a JSON file."""

    def __init__(
        self, config_source: Union[str, Path, Dict[str, Any]] = "src/config.json"
    ):
        self._config_path: Path | None = None
        self._data: Dict[str, Any] = {}

        if isinstance(config_source, (str, Path)):
            self._config_path = Path(config_source)
            self._data = self._load_config()
        elif isinstance(config_source, dict):
            self._data = config_source
        else:
            raise TypeError(
                "config_source must be a string path, a Path object, or a dictionary."
            )

    def _load_config(self) -> dict:
        if self._config_path is None:
            return {}

        # Ensure path is string for compatibility with some environments
        path_str = str(self._config_path)

        try:
            with open(path_str, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # In frozen mode, let the caller handle the error or return empty
            # to avoid crashing import time if path is wrong initially
            return {}

    def __getattr__(self, name: str) -> Any:
        # Magic Logic: Convert MAP_WIDTH -> map_width
        key = name.lower() if name.isupper() else name

        if key in self._data:
            value = self._data[key]
            # Recursive wrapping for nested dicts
            if isinstance(value, dict):
                return Config(value)
            return value

        raise AttributeError(
            f"Configuration '{self._config_path or 'nested config'}' has no setting '{key}' (mapped from '{name}')"
        )
