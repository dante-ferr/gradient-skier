import customtkinter as ctk
from .bottom_frame import BottomFrame

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        bottom_frame = BottomFrame(self)
        bottom_frame.pack(side="bottom", fill="x")

        self.pack_propagate(False)
