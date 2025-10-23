import customtkinter as ctk


class MapCanvas(ctk.CTkCanvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)

        self.configure(bg="black")
