import json
import numpy as np
import importlib.resources
from terrain_map.generator import MapGenerator
from terrain_map import TerrainMap
from config import config
from multiprocessing import Process, Queue
from typing import TYPE_CHECKING, cast
import customtkinter as ctk
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from terrain_map.generator.map_generator import MapGenerator


def generate_map_worker(queue: Queue, seed: int | None = None):
    """Worker function to run in a separate process."""
    generator = MapGenerator()
    terrain_map = generator.generate(
        width=config.MAP_WIDTH, height=config.MAP_HEIGHT, seed=seed
    )
    queue.put(terrain_map)


class MapManager:
    MAP_RESULT_INTERVAL = 100

    def __init__(self):
        self.generator = MapGenerator()
        self._map: "TerrainMap | None" = None
        self.root: "ctk.CTk | None" = None
        self.result_queue: "Queue[TerrainMap]" = Queue()

        self._on_map_recreate_callbacks = []
        self._on_map_change_callbacks = []

    @property
    def map(self):
        if self._map is None:
            raise Exception("No map loaded")
        return self._map

    @map.setter
    def map(self, value):
        self._map = value

    def set_root(self, root: ctk.CTk):
        self.root = root

    def add_map_recreate_callback(self, callback):
        self._on_map_recreate_callbacks.append(callback)

    def add_map_change_callback(self, callback):
        self._on_map_change_callbacks.append(callback)

    def recreate_map(self, seed: int | None = None):
        from state_managers import canvas_state_manager

        if self.root is None:
            raise RuntimeError("MapManager's root has not been set.")

        map_loading_var = cast(ctk.BooleanVar, canvas_state_manager.vars["map_loading"])
        map_loading_var.set(True)

        process = Process(target=generate_map_worker, args=(self.result_queue, seed))
        process.start()

        # Poll for the result from the separate process.
        self.root.after(self.MAP_RESULT_INTERVAL, self._check_for_map_result)

    def _on_map_generated(self, terrain_map: TerrainMap):
        # Local imports to avoid circular dependencies.
        from state_managers import canvas_state_manager
        from state_managers import game_state_manager
        from game import game_manager

        self.map = terrain_map

        seed_var = cast(ctk.StringVar, game_state_manager.vars["current_seed"])
        seed_text = str(terrain_map.seed) if terrain_map.seed is not None else "N/A"
        seed_var.set(seed_text)

        for callback in self._on_map_recreate_callbacks:
            callback()

        game_manager.calculate_initial_path()

        map_loading_var = cast(ctk.BooleanVar, canvas_state_manager.vars["map_loading"])
        map_loading_var.set(False)

    def _check_for_map_result(self):
        """Polls the queue for a generated map."""
        if not self.result_queue.empty():
            terrain_map = self.result_queue.get()
            self._on_map_generated(terrain_map)
        else:
            if self.root:
                self.root.after(self.MAP_RESULT_INTERVAL, self._check_for_map_result)

    def load_map_from_json(self, filepath: str | None = None):
        """Loads a terrain map from a JSON file and sets it as the current map."""
        try:
            if filepath is None:
                filepath = str(
                    importlib.resources.files("data")
                    / "terrain_saves"
                    / "terrain_map.json"
                )
            with open(
                filepath, "r"
            ) as f:  # Not using importlib.resources.open_text as we need the filepath
                map_data = json.load(f)

            height_data = np.array(map_data["height_data"], dtype=np.uint8)

            self.map = TerrainMap(height_data, seed=map_data.get("seed"))

            print(f"Successfully loaded map from {filepath}")

            for callback in self._on_map_recreate_callbacks:
                callback()

        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            print(f"Error loading map from {filepath}: {e}")

    def apply_tool(self, tool_type: str, center_x: int, center_y: int) -> bool:
        successful_mod = self.map.apply_tool(tool_type, center_x, center_y)

        for callback in self._on_map_change_callbacks:
            callback()

        return successful_mod


map_manager = MapManager()
