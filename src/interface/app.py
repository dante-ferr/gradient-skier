import customtkinter as ctk
from .sidebar import Sidebar
from .theme import theme
from .map_canvas import MapCanvas

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme(str(theme.path))


class App(ctk.CTk):

    def __init__(self):
        from game import game_manager

        super().__init__()

        self.title("Gradient Skier")
        self.attributes("-zoomed", True)
        self.minsize(width=800, height=600)

        game_manager.set_root(self)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=256)

        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="nsew")
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(0, weight=0)
        left_frame.grid_rowconfigure(1, weight=1)

        canvas = MapCanvas(left_frame)
        canvas.grid(row=1, column=0, sticky="nsew")

        sidebar = Sidebar(self)
        sidebar.grid(row=0, column=1, sticky="ns", padx=16, pady=32)
