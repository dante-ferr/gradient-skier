import customtkinter as ctk
from typing import Callable, Dict, Any, Union

CtkVariable = Union[ctk.BooleanVar, ctk.StringVar, ctk.IntVar, ctk.DoubleVar]


class StateManager:
    """A base class for centralized state management of UI properties."""

    def __init__(self):
        self.vars: Dict[str, CtkVariable] = {}
        self._callbacks: Dict[str, list[Callable[[Any], None]]] = {}
        self._defaults: Dict[str, Any] = {}

    def _initialize_state(self, variables: Dict[str, CtkVariable]):
        """Initializes state variables, stores their initial values as defaults, and sets up tracing."""
        self.vars = variables
        self._callbacks = {name: [] for name in self.vars.keys()}
        self._defaults = {name: var.get() for name, var in self.vars.items()}

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
        """Notifies all registered callbacks for a given state variable."""
        value = self.vars[name].get()

        if name in self._callbacks:
            for callback in self._callbacks[name]:
                callback(value)

    def reset_to_defaults(self):
        """Resets all state variables to their default values."""
        for name, default_value in self._defaults.items():
            self.vars[name].set(default_value)
