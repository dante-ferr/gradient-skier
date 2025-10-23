import json
from pathlib import Path


class Config:
    """
    Loads configuration from a JSON file and provides easy, attribute-based access.
    e.g., config.SHELTER_DEPTH instead of config['SHELTER_DEPTH']
    """

    def __init__(self, config_path):
        """
        Initializes the Config object by loading from a JSON file.

        Args:
            config_path (str or Path): The path to the JSON configuration file.
        """
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")

        with open(config_path, "r") as f:
            config_data = json.load(f)

        for key, value in config_data.items():
            setattr(self, key, value)

    def update(self, new_config_dict):
        """
        Updates configuration with values from a dictionary, allowing for overrides.
        """
        if new_config_dict:
            for key, value in new_config_dict.items():
                setattr(self, key, value)


# Create a default generator config instance to be imported by other modules.
# This assumes the config file is in the same directory as this loader.
_config_dir = Path(__file__).parent
generator_config_path = _config_dir / "generator_config.json"
generator_config = Config(generator_config_path)
