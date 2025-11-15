import customtkinter as ctk
from .state_manager import StateManager
from config import config
from typing import Union

CtkVariable = Union[ctk.BooleanVar, ctk.StringVar, ctk.IntVar, ctk.DoubleVar]


class GameStateManager(StateManager):
    """A centralized state manager for game state and UI properties."""

    def __init__(self):
        super().__init__()
        self._initialize_state(
            {
                "tool_charges_remaining": ctk.IntVar(
                    value=config.TOOL.MAX_TOOL_CHARGES
                ),
                # Cost of the path on the original, unmodified map.
                "initial_path_cost": ctk.DoubleVar(value=0.0),
                # Cost of the path on the current, modified map.
                "current_path_cost": ctk.DoubleVar(value=0.0),
                # True if current_path_cost < initial_path_cost.
                "won": ctk.BooleanVar(value=False),
                # Disables UI interaction while pathfinding is in progress.
                "player_can_interact": ctk.BooleanVar(value=False),
                # The tool currently selected by the player.
                "selected_tool": ctk.StringVar(value="excavator"),
                # The seed of the current map.
                "current_seed": ctk.StringVar(value="N/A"),
            }
        )


game_state_manager = GameStateManager()
