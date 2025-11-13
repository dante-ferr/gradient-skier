import json
import numpy as np
from terrain_map.generator import MapGenerator
from terrain_map import TerrainMap
from config import config
from multiprocessing import Process, Queue
from typing import TYPE_CHECKING, cast
import customtkinter as ctk
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from terrain_map.generator.map_generator import MapGenerator


def generate_map_worker(queue: Queue):
    """Worker function to run in a separate process."""
    generator = MapGenerator()
    terrain_map = generator.generate(width=config.MAP_WIDTH, height=config.MAP_HEIGHT)
    queue.put(terrain_map)


class MapManager:
    MAP_RESULT_INTERVAL = 100

    def __init__(self):
        self.generator = MapGenerator()
        self.map: "TerrainMap | None" = None
        self.root: "ctk.CTk | None" = None
        self.result_queue: "Queue[TerrainMap]" = Queue()

        self._on_map_recreate_callbacks = []

    def set_root(self, root: ctk.CTk):
        self.root = root

    def add_map_recreate_callback(self, callback):
        self._on_map_recreate_callbacks.append(callback)

    def recreate_map(self):
        from state_managers import canvas_state_manager

        if self.root is None:
            raise RuntimeError("MapManager's root has not been set.")

        loading_var = cast(ctk.BooleanVar, canvas_state_manager.vars["loading"])
        loading_var.set(True)

        # Run generation in a separate process
        process = Process(target=generate_map_worker, args=(self.result_queue,))
        process.start()

        # Start polling for the result
        self.root.after(self.MAP_RESULT_INTERVAL, self._check_for_map_result)

    def _on_map_generated(self, terrain_map: TerrainMap):
        from state_managers import canvas_state_manager
        from game import game_manager

        self.map = terrain_map

        for callback in self._on_map_recreate_callbacks:
            callback()

        if map_manager.map is None:
            raise Exception("No map loaded")

        loading_var = cast(ctk.BooleanVar, canvas_state_manager.vars["loading"])
        loading_var.set(False)

        game_manager.calculate_initial_path()

    def _check_for_map_result(self):
        """Polls the queue for a generated map."""
        if not self.result_queue.empty():
            terrain_map = self.result_queue.get()
            self._on_map_generated(terrain_map)
        else:
            if self.root:
                self.root.after(self.MAP_RESULT_INTERVAL, self._check_for_map_result)

    def load_map_from_json(
        self, filepath: str = f"{config.TERRAIN_SAVES_PATH}/terrain_map.json"
    ):
        """Loads a terrain map from a JSON file and sets it as the current map."""
        try:
            with open(filepath, "r") as f:
                map_data = json.load(f)

            height_data = np.array(map_data["height_data"], dtype=np.uint8)

            self.map = TerrainMap(height_data)

            print(f"Successfully loaded map from {filepath}")

            for callback in self._on_map_recreate_callbacks:
                callback()

        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            print(f"Error loading map from {filepath}: {e}")


map_manager = MapManager()
