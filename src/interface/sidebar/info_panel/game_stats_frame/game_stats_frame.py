import customtkinter as ctk
from typing import Any

class GameStatsFrame(ctk.CTkFrame):
    LABEL_INIT_PARAMS: dict[str, Any] = {"font": ("", 16)}
    LABEL_PACK_PARAMS: dict[str, Any] = {"padx": (0, 4), "anchor": "w"}

    def __init__(self, parent):
        from state_managers import game_state_manager, canvas_state_manager

        super().__init__(parent, fg_color="transparent", width=300)
        self.pack_propagate(False)

        attempts_display_label = ctk.CTkLabel(
            self, text="Attempts: ", **self.LABEL_INIT_PARAMS
        )
        attempts_display_label.pack(**self.LABEL_PACK_PARAMS)

        def _update_attempts_display(value: float):
            attempts_display_label.configure(text=f"Attempts: {int(value)}")

        won_display_label = ctk.CTkLabel(
            self, text="Map won: ", **self.LABEL_INIT_PARAMS
        )
        won_display_label.pack(**self.LABEL_PACK_PARAMS)

        def _update_won_display(value: bool):
            won_display_label.configure(text=f"Map won: {'Yes' if value else 'No'}")

        first_victory_display_label = ctk.CTkLabel(
            self, text="", **self.LABEL_INIT_PARAMS
        )
        first_victory_display_label.pack(**self.LABEL_PACK_PARAMS)

        def _update_first_victory_display(value: int):
            if value == -1:
                first_victory_display_label.pack_forget()
            else:
                first_victory_display_label.pack(**self.LABEL_PACK_PARAMS)
                first_victory_display_label.configure(
                    text=f"Attempts for 1st win: {int(value)}"
                )

        hovered_gradient_display_label = ctk.CTkLabel(
            self, text="", **self.LABEL_INIT_PARAMS
        )
        hovered_gradient_display_label.pack(**self.LABEL_PACK_PARAMS)

        def _update_hovered_gradient_display(value: str):
            if value == "":
                hovered_gradient_display_label.pack_forget()
            else:
                hovered_gradient_display_label.pack(**self.LABEL_PACK_PARAMS)
                hovered_gradient_display_label.configure(
                    text=f"Path gradient at cursor: {value}"
                )

        game_state_manager.add_callback("attempts", _update_attempts_display)
        game_state_manager.add_callback("won", _update_won_display)
        game_state_manager.add_callback(
            "attempts_before_first_victory", _update_first_victory_display
        )

        canvas_state_manager.add_callback(
            "hovered_gradient", _update_hovered_gradient_display
        )
