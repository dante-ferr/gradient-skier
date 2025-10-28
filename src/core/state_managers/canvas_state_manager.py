import customtkinter as ctk
from typing import Callable, Dict, Any, Union

CtkVariable = Union[ctk.BooleanVar, ctk.StringVar, ctk.IntVar, ctk.DoubleVar]


class CanvasStateManager:
    """A centralized state manager for canvas-related UI properties."""

    def __init__(self):
        self.vars: Dict[str, CtkVariable] = {
            "zoom": ctk.DoubleVar(value=1.0),
        }
        self._callbacks: Dict[str, list[Callable[[Any], None]]] = {
            "zoom": [],
        }

        for name, var in self.vars.items():
            var.trace_add("write", lambda *args, n=name: self._notify_callbacks(n))

    def add_callback(self, name: str, callback: Callable[[Any], None]):
        """Register a callback for a state variable change and call it immediately."""
        if name in self._callbacks:
            self._callbacks[name].append(callback)
            # Immediately call callback with current value
            callback(self.vars[name].get())
        else:
            raise ValueError(f"Unknown state variable: {name}")

    def _notify_callbacks(self, name: str):
        value = self.vars[name].get()

        if name in self._callbacks:
            for callback in self._callbacks[name]:
                callback(value)


canvas_state_manager = CanvasStateManager()
