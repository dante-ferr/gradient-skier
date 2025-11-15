import customtkinter as ctk
from multiprocessing import Process, Queue
from typing import Callable, cast

from ._pathfinder import Pathfinder
from ._path import Path
from terrain_map import TerrainMap


def find_path_worker(
    queue: "Queue[tuple[Path, bool]]",
    terrain_map: TerrainMap,
    start: tuple[int, int],
    end: tuple[int, int],
    is_initial: bool,
):
    """
    Worker function to run in a separate process.
    Calculates the path and puts the result (Path object and is_initial flag)
    into the queue.
    """
    pathfinder = Pathfinder(terrain_map)
    path_obj = pathfinder.find_path(start, end)
    queue.put((path_obj, is_initial))


class GamePathManager:

    # Interval to check for path calculation results
    PATH_RESULT_INTERVAL = 100

    def __init__(self, start_point: tuple[int, int], end_point: tuple[int, int]):
        self.root: ctk.CTk | None = None
        self.start_point = start_point
        self.end_point = end_point

        # Path and cost
        self.initial_path: Path = Path([], 0.0)
        self.initial_cost: float = 0.0
        self.current_path: Path = Path([], 0.0)
        self.current_cost: float = 0.0

        # Queue for async path results
        self.path_queue: "Queue[tuple[Path, bool]]" = Queue()

        # Callbacks for UI updates
        self.on_path_recalculated_callbacks: list[Callable[[Path], None]] = []

    def set_root(self, root: ctk.CTk):
        self.root = root

    def add_on_path_recalculated_callback(self, callback: Callable[[Path], None]):
        self.on_path_recalculated_callbacks.append(callback)

    def calculate_initial_path(self):
        """Calculates the path on the unmodified map and stores it as the "goal to beat"."""
        self._calculate_path(is_initial=True)

    def recalculate_current_path(self):
        """Calculates the path on the *modified* map and checks for a win."""
        self._calculate_path(is_initial=False)

    def _calculate_path(self, is_initial: bool):
        """
        Spawns a worker process to find a path asynchronously.

        Args:
            is_initial: If True, the result will be set as the initial path.
        """
        from core import map_manager
        from state_managers import canvas_state_manager, game_state_manager

        if not self.root:
            raise RuntimeError("Root has not been set.")

        if not map_manager.map:
            raise Exception("The map is not loaded.")

        path_loading_var = cast(
            ctk.BooleanVar, canvas_state_manager.vars["path_loading"]
        )
        path_loading_var.set(True)
        player_can_interact_var = cast(
            ctk.BooleanVar, game_state_manager.vars["player_can_interact"]
        )
        player_can_interact_var.set(False)

        current_map = map_manager.map

        process = Process(
            target=find_path_worker,
            args=(
                self.path_queue,
                current_map,
                self.start_point,
                self.end_point,
                is_initial,
            ),
        )
        process.start()

        self.root.after(self.PATH_RESULT_INTERVAL, self._check_for_path_result)

    def _check_for_path_result(self):
        """Polls the queue for a generated path."""
        if not self.path_queue.empty():
            path_obj, is_initial = self.path_queue.get()
            self._on_path_found(path_obj, is_initial)
        else:
            if self.root:
                self.root.after(self.PATH_RESULT_INTERVAL, self._check_for_path_result)

    def _on_path_found(self, path_obj: Path, is_initial: bool):
        """Processes the pathfinding result from the worker."""
        from state_managers import game_state_manager, canvas_state_manager
        from game import game_manager

        self.current_path = path_obj
        self.current_cost = path_obj.total_cost

        cast(ctk.DoubleVar, game_state_manager.vars["current_path_cost"]).set(
            self.current_cost
        )

        if is_initial:
            self.initial_path = path_obj
            self.initial_cost = path_obj.total_cost
            cast(ctk.DoubleVar, game_state_manager.vars["initial_path_cost"]).set(
                self.initial_cost
            )
        else:
            game_manager.judge_match()

        path_loading_var = cast(
            ctk.BooleanVar, canvas_state_manager.vars["path_loading"]
        )
        path_loading_var.set(False)
        player_can_interact_var = cast(
            ctk.BooleanVar, game_state_manager.vars["player_can_interact"]
        )
        player_can_interact_var.set(True)

        self._fire_path_recalculated_callbacks()

    def _fire_path_recalculated_callbacks(self):
        """Notifies all subscribed UI components about the new path."""
        for callback in self.on_path_recalculated_callbacks:
            callback(self.current_path)
