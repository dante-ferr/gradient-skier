import json
import numpy as np
from terrain_map.generator import MapGenerator
from terrain_map import TerrainMap
from config import config
from typing import TYPE_CHECKING


class MapManager:
    def __init__(self):
        self.generator = MapGenerator()
        self.map: "TerrainMap | None" = None

        self._on_map_recreate_callbacks = []

    def add_map_recreate_callback(self, callback):
        self._on_map_recreate_callbacks.append(callback)

    def recreate_map(self):
        terrain_map, _ = self.generator.generate(
            width=config.MAP_WIDTH, height=config.MAP_HEIGHT
        )
        self.map = terrain_map

        for callback in self._on_map_recreate_callbacks:
            callback()

    def load_map_from_json(
        self, filepath: str = f"{config.TERRAIN_SAVES_PATH}/terrain_map.json"
    ):
        """Loads a terrain map from a JSON file and sets it as the current map."""
        try:
            with open(filepath, "r") as f:
                map_data = json.load(f)

            height_data = np.array(map_data["height_data"], dtype=np.uint8)
            shelter_coords = tuple(map_data["shelter_coords"])
            start_altitude_threshold = map_data["start_altitude_threshold"]

            self.map = TerrainMap(height_data, shelter_coords, start_altitude_threshold)

            print(f"Successfully loaded map from {filepath}")

            for callback in self._on_map_recreate_callbacks:
                callback()

        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            print(f"Error loading map from {filepath}: {e}")


map_manager = MapManager()
