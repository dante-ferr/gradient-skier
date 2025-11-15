import customtkinter as ctk
from .state_manager import StateManager


class CanvasStateManager(StateManager):
    """A centralized state manager for canvas-related UI properties."""

    def __init__(self):
        super().__init__()

        self._initialize_state(
            {
                "zoom": ctk.DoubleVar(value=1.0),
                "initial_zoom": ctk.IntVar(value=1),
                "map_loading": ctk.BooleanVar(value=False),
                "path_loading": ctk.BooleanVar(value=False),
                "hovered_gradient": ctk.StringVar(value="#FF0000"),
            }
        )


canvas_state_manager = CanvasStateManager()
