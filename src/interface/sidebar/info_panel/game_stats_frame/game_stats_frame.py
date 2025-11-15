import customtkinter as ctk
from typing import Any
from config import config

class GameStatsFrame(ctk.CTkFrame):
    LABEL_INIT_PARAMS: dict[str, Any] = {"font": ("", 16)}
    LABEL_PACK_PARAMS: dict[str, Any] = {"padx": (0, 4), "anchor": "w"}

    def __init__(self, parent):
        from state_managers import game_state_manager, canvas_state_manager

        super().__init__(parent, fg_color="transparent", width=300)
        self.pack_propagate(False)

        # --- 1. Tool Charges Display ---
        charges_display_label = ctk.CTkLabel(
            self, text="Charges Left: ", **self.LABEL_INIT_PARAMS
        )
        charges_display_label.pack(**self.LABEL_PACK_PARAMS)

        def _update_charges_display(value: float):
            charges_display_label.configure(
                text=f"Charges Left: {int(value)} / {config.tool.MAX_TOOL_CHARGES}"
            )

        # --- 2. Initial Path Cost Display (The Goal) ---
        initial_cost_display_label = ctk.CTkLabel(
            self, text="Initial Cost: ", **self.LABEL_INIT_PARAMS
        )
        initial_cost_display_label.pack(**self.LABEL_PACK_PARAMS)

        def _update_initial_cost_display(value: float):
            initial_cost_display_label.configure(text=f"Initial Cost: {value:.2f}")

        # --- 3. Current Path Cost Display ---
        current_cost_display_label = ctk.CTkLabel(
            self, text="Current Cost: ", **self.LABEL_INIT_PARAMS
        )
        current_cost_display_label.pack(**self.LABEL_PACK_PARAMS)

        def _update_current_cost_display(value: float):
            current_cost_display_label.configure(text=f"Current Cost: {value:.2f}")

        # --- 4. Win Status Display ---
        won_display_label = ctk.CTkLabel(
            self, text="Solved: No", **self.LABEL_INIT_PARAMS
        )
        won_display_label.pack(**self.LABEL_PACK_PARAMS)

        def _update_won_display(value: bool):
            status = "Yes (WIN!)" if value else "No"
            won_display_label.configure(text=f"Solved: {status}")

        # --- 5. Hovered Gradient/Map Info Display (from canvas) ---
        hovered_gradient_display_label = ctk.CTkLabel(
            self, text="", **self.LABEL_INIT_PARAMS
        )
        hovered_gradient_display_label.pack(**self.LABEL_PACK_PARAMS)

        def _update_hovered_gradient_display(value: str):
            if value == "":
                hovered_gradient_display_label.pack_forget()
            else:
                hovered_gradient_display_label.pack(**self.LABEL_PACK_PARAMS)
                hovered_gradient_display_label.configure(text=f"Map Gradient: {value}")

        # --- Register New Callbacks ---
        game_state_manager.add_callback(
            "tool_charges_remaining", _update_charges_display
        )
        game_state_manager.add_callback(
            "initial_path_cost", _update_initial_cost_display
        )
        game_state_manager.add_callback(
            "current_path_cost", _update_current_cost_display
        )
        game_state_manager.add_callback("won", _update_won_display)

        # --- Keep Existing Canvas Callback ---
        canvas_state_manager.add_callback(
            "hovered_gradient", _update_hovered_gradient_display
        )
