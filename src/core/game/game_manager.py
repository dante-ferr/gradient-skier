import customtkinter as ctk
from config import config
from typing import Callable, cast
from ._pathfinder import Pathfinder
from ._path import Path
from state_managers import game_state_manager
from core import map_manager

class GameManager:

    def __init__(self):
        self.root: ctk.CTk | None = None
        self.start_point: tuple[int, int] = (0, 0)
        self.end_point = (config.MAP_WIDTH - 1, config.MAP_HEIGHT - 1)

        # Path and cost
        self.initial_path: Path = Path([], 0.0)
        self.initial_cost: float = (
            0.0  # Kept for quick comparison, though path object has it
        )
        self.current_path: Path = Path([], 0.0)
        self.current_cost: float = 0.0  # Kept for quick comparison

        # Callbacks for UI updates
        # This callback will pass the new path object
        self.on_path_recalculated_callbacks: list[Callable[[Path], None]] = []
        self.on_game_start_callbacks: list[Callable] = []

    def set_root(self, root: ctk.CTk):
        self.root = root
        # Start the game as soon as the map is ready (or on a button press)
        self.start_new_game()

    def start_new_game(self):
        """
        Resets the game to a new map and calculates the initial path.
        """
        map_manager.recreate_map()

        # Reset game state variables
        game_state_manager.reset_to_defaults()
        tool_charges_var = cast(
            ctk.IntVar, game_state_manager.vars["tool_charges_remaining"]
        )
        tool_charges_var.set(config.tool.MAX_TOOL_CHARGES)

        for callback in self.on_game_start_callbacks:
            callback()

    def add_on_path_recalculated_callback(self, callback: Callable[[Path], None]):
        self.on_path_recalculated_callbacks.append(callback)

    def add_on_game_start_callback(self, callback: Callable):
        self.on_game_start_callbacks.append(callback)

    def calculate_initial_path(self):
        """Calculates the path on the unmodified map and stores it as the "goal to beat"."""
        self._calculate_path(is_initial=True)

    def _recalculate_current_path(self):
        """Calculates the path on the *modified* map and checks for a win."""
        self._calculate_path(is_initial=False)

    def _calculate_path(self, is_initial: bool):
        """
        Finds a path, updates the game state, and notifies the UI.

        Args:
            is_initial: If True, sets the initial path cost as the baseline.
                        Otherwise, it calculates the current path and checks for a win.
        """
        if not map_manager.map:
            return

        # Disable UI while calculating
        self._set_player_can_interact(False)

        print("Finding path...")
        pathfinder = Pathfinder(map_manager.map)
        path_obj = pathfinder.find_path(self.start_point, self.end_point)
        print("Path found.")

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
            cast(ctk.BooleanVar, game_state_manager.vars["won"]).set(False)
        else:
            # Check for win condition on subsequent calculations
            won = self.current_cost < self.initial_cost and self.current_path.is_valid
            cast(ctk.BooleanVar, game_state_manager.vars["won"]).set(won)

        # Notify UI to draw the new path
        self._fire_path_recalculated_callbacks()
        self._set_player_can_interact(True)

    def use_tool_at(self, tool_type: str, x: int, y: int):
        """
        Public method called by the UI when the player clicks on the map.
        Applies a tool, modifies the map, and triggers a path recalculation.
        """
        if not map_manager.map:
            raise Exception("The map is not loaded.")

        tool_charges_var = cast(
            ctk.IntVar, game_state_manager.vars["tool_charges_remaining"]
        )

        if tool_charges_var.get() <= 0:
            print("No tool charges remaining.")
            return

        print(f"Using tool '{tool_type}' at ({x}, {y})")

        # 1. Modify the terrain
        # We assume MapManager has a method like this
        modification_success = map_manager.map.apply_tool(tool_type, x, y)

        if not modification_success:
            print("Tool use failed (e.g., out of bounds)")
            return

        # 2. Decrement tool charges
        tool_charges_var.set(tool_charges_var.get() - 1)

        # 3. Recalculate the path on the modified terrain
        # Use root.after(1) to allow the UI to update (e.g., show "loading")
        # before starting the potentially expensive calculation.
        if self.root:
            self.root.after(1, self._recalculate_current_path)
        else:
            self._recalculate_current_path()  # Run synchronously if no root

    def _fire_path_recalculated_callbacks(self):
        """
        Notifies all subscribed UI components about the new path.
        """
        for callback in self.on_path_recalculated_callbacks:
            callback(self.current_path)

    def _set_player_can_interact(self, can_interact: bool):
        """
        Updates a state variable to enable/disable UI controls, preventing
        actions during path calculation.
        """
        cast(ctk.BooleanVar, game_state_manager.vars["player_can_interact"]).set(
            can_interact
        )


game_manager = GameManager()
