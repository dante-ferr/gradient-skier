import customtkinter as ctk
from config import config
from typing import Callable, cast
from ._game_path_manager import GamePathManager
from ._path import Path
from interface.components.overlay.message_overlay import MessageOverlay

class GameManager:
    def __init__(self):
        self._root: ctk.CTk | None = None
        self.start_point: tuple[int, int] = (0, 0)
        self.end_point = (config.MAP_WIDTH - 1, config.MAP_HEIGHT - 1)

        self.path_manager = GamePathManager(self.start_point, self.end_point)

        self.on_game_start_callbacks: list[Callable] = []

    @property
    def root(self):
        if not self._root:
            raise RuntimeError("Root has not been set.")
        return self._root

    @root.setter
    def root(self, value):
        self._root = value

    def set_root(self, root: ctk.CTk):
        self.root = root
        self.path_manager.set_root(root)
        self.start_new_game()

    def start_new_game(self, seed: int | None = None):
        """
        Resets the game to a new map and calculates the initial path.
        """
        # Import local
        from core import map_manager  # Local import to avoid circular dependency
        from state_managers import (
            game_state_manager,
        )  # Local import to avoid circular dependency

        map_manager.recreate_map(seed=seed)
        game_state_manager.reset_to_defaults()
        tool_charges_var = cast(
            ctk.IntVar, game_state_manager.vars["tool_charges_remaining"]
        )
        tool_charges_var.set(config.tool.MAX_TOOL_CHARGES)

        for callback in self.on_game_start_callbacks:
            callback()

    def add_on_path_recalculated_callback(self, callback: Callable[[Path], None]):
        self.path_manager.add_on_path_recalculated_callback(callback)

    def add_on_game_start_callback(self, callback: Callable):
        self.on_game_start_callbacks.append(callback)

    def calculate_initial_path(self):
        self.path_manager.calculate_initial_path()

    def use_tool_at(self, tool_type: str, x: int, y: int):
        """
        Public method called by the UI when the player clicks on the map.
        Applies a tool, modifies the map, and triggers a path recalculation.
        """
        # Import local
        from state_managers import (
            game_state_manager,
        )  # Local import to avoid circular dependency
        from core import map_manager

        if not map_manager.map:
            raise Exception("The map is not loaded.")

        tool_charges_var = cast(
            ctk.IntVar, game_state_manager.vars["tool_charges_remaining"]
        )

        if tool_charges_var.get() <= 0:
            return

        modification_success = map_manager.apply_tool(tool_type, x, y)

        if not modification_success:
            return

        tool_charges_var.set(tool_charges_var.get() - 1)

        # Recalculate the path on the modified terrain.
        # This is deferred if it's the last tool charge to allow the UI to update.
        if tool_charges_var.get() <= 0:
            self.root.after(1, self.path_manager.recalculate_current_path)

    def _set_player_can_interact(self, can_interact: bool):
        """
        Updates a state variable to enable/disable UI controls.
        This prevents user actions during path calculation.
        """
        # Import local
        from state_managers import game_state_manager

        cast(ctk.BooleanVar, game_state_manager.vars["player_can_interact"]).set(
            can_interact
        )

    def judge_match(self):
        from state_managers import game_state_manager

        won = (
            self.path_manager.current_cost
            <= self.path_manager.initial_cost * config.game.WIN_COST_MAX_PERCENTAGE
            and self.path_manager.current_path.is_valid
        )
        cast(ctk.BooleanVar, game_state_manager.vars["won"]).set(bool(won))

        MessageOverlay(
            (
                f"You won! Your map's traversal cost is at least {100 - config.game.WIN_COST_MAX_PERCENTAGE*100}% cheaper than the original."
                if won
                else f"You lost! Make sure your map's traversal cost is at least {100 - config.game.WIN_COST_MAX_PERCENTAGE*100}% cheaper than the original."
            ),
            "Result",
        )


game_manager = GameManager()
