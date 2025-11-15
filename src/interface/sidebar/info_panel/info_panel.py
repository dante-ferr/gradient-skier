import customtkinter as ctk
from .settings_frame import SettingsFrame
from .game_stats_frame import GameStatsFrame
from .tools_frame import ToolsFrame

class InfoPanel(ctk.CTkFrame):
    FRAME_GRID_PARAMS = {"padx": 32, "pady": 32}

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        game_stats_frame = GameStatsFrame(self)
        game_stats_frame.grid(row=0, column=0, sticky="nsw", **self.FRAME_GRID_PARAMS)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=0, column=1, sticky="ne", **self.FRAME_GRID_PARAMS)

        restart_button = ctk.CTkButton(
            button_frame,
            text="Start New Game",
            font=("", 16),
            command=self._start_new_game,
        )
        restart_button.pack(expand=True)

        self.tools_frame = ToolsFrame(self)
        self.tools_frame.grid(row=1, column=0, sticky="ew", **self.FRAME_GRID_PARAMS)

        self.settings_frame = SettingsFrame(self)
        self.settings_frame.grid(row=1, column=1, sticky="ew", **self.FRAME_GRID_PARAMS)

    def _start_new_game(self):
        from game import game_manager

        game_manager.start_new_game()
