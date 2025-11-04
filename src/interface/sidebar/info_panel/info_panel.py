import customtkinter as ctk
from .bottom_frame import BottomFrame
from .game_stats_frame import GameStatsFrame


class InfoPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)  # Let the bottom frame take its own height

        game_stats_frame = GameStatsFrame(self)
        game_stats_frame.grid(row=0, column=0, padx=32, pady=32, sticky="nsw")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=0, column=1, padx=32, pady=32, sticky="ne")

        restart_button = ctk.CTkButton(
            button_frame,
            text="Start New Game",
            font=("", 16),
            command=self._start_new_game,
        )
        restart_button.pack(expand=True)

        self.bottom_frame = BottomFrame(self)
        self.bottom_frame.grid(
            row=1, column=0, columnspan=2, padx=32, pady=32, sticky="ew"
        )

    def _start_new_game(self):
        from game import game_manager

        game_manager.start_new_game()
