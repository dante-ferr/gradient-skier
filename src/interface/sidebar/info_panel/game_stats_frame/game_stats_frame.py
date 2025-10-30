import customtkinter as ctk


class GameStatsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        from state_managers import game_state_manager

        super().__init__(parent, fg_color="transparent")

        # --- Attempts ---
        attempts_display_label = ctk.CTkLabel(self, text="Attempts: ", font=("", 16))
        attempts_display_label.pack(padx=(0, 4), anchor="w")

        def _update_attempts_display(value: float):
            attempts_display_label.configure(text=f"Attempts: {int(value)}")

        # --- Game Won ---
        won_display_label = ctk.CTkLabel(self, text="Map Won: ", font=("", 16))
        won_display_label.pack(padx=(0, 4), anchor="w")

        def _update_won_display(value: bool):
            won_display_label.configure(text=f"Map Won: {'Yes' if value else 'No'}")

        # --- Attempts Before First Victory ---
        first_victory_display_label = ctk.CTkLabel(self, text="", font=("", 16))
        first_victory_display_label.pack(padx=(0, 4), anchor="w")

        def _update_first_victory_display(value: int):
            if value == -1:
                first_victory_display_label.configure(text="")
            else:
                first_victory_display_label.configure(
                    text=f"Attempts for 1st Win: {int(value)}"
                )

        game_state_manager.add_callback(
            "attempts",
            _update_attempts_display,
        )
        game_state_manager.add_callback(
            "won",
            _update_won_display,
        )
        game_state_manager.add_callback(
            "attempts_before_first_victory",
            _update_first_victory_display,
        )
