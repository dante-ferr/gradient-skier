import customtkinter as ctk
from .settings_frame import SettingsFrame
from .game_stats_frame import GameStatsFrame
from .tools_frame import ToolsFrame
from .restart_frame import RestartFrame

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

        restart_frame = RestartFrame(self)
        restart_frame.grid(row=0, column=1, sticky="ne", **self.FRAME_GRID_PARAMS)

        self.tools_frame = ToolsFrame(self)
        self.tools_frame.grid(row=1, column=0, sticky="ew", **self.FRAME_GRID_PARAMS)

        self.settings_frame = SettingsFrame(self)
        self.settings_frame.grid(row=1, column=1, sticky="es", **self.FRAME_GRID_PARAMS)
