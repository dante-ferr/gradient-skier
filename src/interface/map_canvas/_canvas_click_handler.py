from typing import TYPE_CHECKING, cast
import customtkinter as ctk

if TYPE_CHECKING:
    from .map_canvas import MapCanvas


class CanvasClickHandler:
    """Handles click events on the map canvas to apply terraforming tools."""

    def __init__(self, canvas: "MapCanvas"):
        self.canvas = canvas
        self.canvas.bind("<Button-1>", self._on_canvas_click)

    def _on_canvas_click(self, event):
        """
        Callback for the left-click event on the canvas.

        Applies the currently selected tool to the map, provided the player
        has charges left and interaction is allowed.
        """
        from game import game_manager
        from state_managers import game_state_manager

        # Check if interaction is currently disabled (e.g., during path calculation)
        player_can_interact_var = cast(
            ctk.BooleanVar, game_state_manager.vars["player_can_interact"]
        )
        if not player_can_interact_var.get():
            print("Interaction temporarily disabled (calculating path).")
            return

        # Check if the player has any tool charges left
        tool_charges_var = cast(
            ctk.IntVar, game_state_manager.vars["tool_charges_remaining"]
        )
        if tool_charges_var.get() <= 0:
            print("No tool charges remaining. Reset the map to play again.")
            return

        # 1. Get the currently selected tool from the game state manager
        selected_tool_var = cast(
            ctk.StringVar, game_state_manager.vars["selected_tool"]
        )
        tool_type = selected_tool_var.get()

        # 2. Convert screen coordinates (event.x, event.y) to map grid coordinates
        map_x, map_y = self.canvas.canvas_to_map_coords(event.x, event.y)

        # 3. Apply the tool via the GameManager
        game_manager.use_tool_at(tool_type, map_x, map_y)
