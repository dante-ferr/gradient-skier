import customtkinter as ctk
from .base_state_manager import BaseStateManager


class CanvasStateManager(BaseStateManager):
    """A centralized state manager for canvas-related UI properties."""

    def __init__(self):
        super().__init__()

        self._initialize_state(
            {
                "zoom": ctk.DoubleVar(value=1.0),
                "initial_zoom": ctk.IntVar(value=1),
            }
        )


canvas_state_manager = CanvasStateManager()
