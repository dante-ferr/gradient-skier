from pathlib import Path
from utils import Config

_config_dir = Path(__file__).parent
generator_config_path = _config_dir / "generator_config.json"
generator_config = Config(generator_config_path)
