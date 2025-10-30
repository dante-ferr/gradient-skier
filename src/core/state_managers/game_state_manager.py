import customtkinter as ctk
from .state_manager import StateManager


class GameStateManager(StateManager):
    """A centralized state manager for canvas-related UI properties."""

    def __init__(self):
        super().__init__()

        self._initialize_state(
            {
                "attempts": ctk.IntVar(value=0),
                "won": ctk.BooleanVar(value=False),
                "attempts_before_first_victory": ctk.IntVar(value=-1),
            }
        )


game_state_manager = GameStateManager()
