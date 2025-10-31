import json
from pathlib import Path
from typing import Any, Dict, Union


class Config:
    """A class to hold and provide access to configuration settings from a JSON file."""

    def __init__(
        self, config_source: Union[str, Path, Dict[str, Any]] = "src/config.json"
    ):
        if isinstance(config_source, (str, Path)):
            # These are only for the top-level config object and help the static analyzer.
            # They do not assign values; the values are loaded dynamically below.

            self._config_path: Path | None = Path(config_source)
            self._data = self._load_config()
        elif isinstance(config_source, dict):
            self._config_path = None  # No file path for nested configs
            self._data = config_source
        else:
            raise TypeError(
                "config_source must be a string path, a Path object, or a dictionary."
            )

    def _load_config(self) -> dict:
        if self._config_path is None:
            return {}
        with open(self._config_path, "r") as f:
            return json.load(f)

    def __getattr__(self, name: str) -> Any:
        # Converts Python's UPPER_SNAKE_CASE attribute access to json's snake_case for lookup.
        key = name.lower() if name.isupper() else name
        if key in self._data:
            value = self._data[key]
            if isinstance(value, dict):
                # If the value is a dictionary, return a new Config instance for it
                return Config(value)
            return value
        raise AttributeError(
            f"Configuration '{self._config_path or 'nested config'}' has no setting '{key}'"
        )


config = Config()
