import customtkinter as ctk
from .bottom_frame import BottomFrame
from .game_stats_frame import GameStatsFrame


class InfoPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        game_stats_frame = GameStatsFrame(self)
        game_stats_frame.pack(fill="x", padx=32, pady=32)

        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.pack(fill="x", padx=32, pady=32, side="right")

        restart_button = ctk.CTkButton(
            right_frame, text="Restart", font=("", 16), command=self._restart
        )
        restart_button.pack(fill="x", pady=4)

        self.bottom_frame = BottomFrame(self)
        self.bottom_frame.pack(side="bottom", fill="x", padx=32, pady=32)

    def _restart(self):
        from state_managers import game_state_manager

        # game_state_manager.restart()

        pass
