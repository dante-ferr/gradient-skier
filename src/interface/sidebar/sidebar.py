import customtkinter as ctk
from .info_panel import InfoPanel
from .terrain_3d_frame import Terrain3dFrame


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=8)
        self.grid_columnconfigure(0, weight=1)

        info_panel = InfoPanel(self)
        info_panel.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        terrain_3d_frame = Terrain3dFrame(self)
        terrain_3d_frame.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
