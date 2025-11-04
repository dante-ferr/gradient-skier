import customtkinter as ctk
from .sidebar import Sidebar
from .theme import theme
from .map_canvas import MapCanvas

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme(str(theme.path))

class App(ctk.CTk):

    def __init__(self):
        from game import game_manager
        from core import map_manager

        super().__init__()

        self.title("Gradient Skier")
        self.attributes("-zoomed", True)
        self.minsize(width=800, height=600)

        map_manager.set_root(self)
        game_manager.set_root(self)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=2)

        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(0, weight=0)
        self.left_frame.grid_rowconfigure(1, weight=1)

        self.loading_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.loading_label = ctk.CTkLabel(
            self.loading_frame, text="Generating new map...", font=ctk.CTkFont(size=20)
        )
        self.loading_label.pack(pady=10)
        self.loading_progress = ctk.CTkProgressBar(
            self.loading_frame, mode="indeterminate"
        )
        self.loading_progress.pack(pady=10, padx=20, fill="x")

        sidebar = Sidebar(self)
        sidebar.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        map_manager.load_map_from_json()

        self.canvas: MapCanvas | None = None

        from state_managers import canvas_state_manager

        canvas_state_manager.add_callback("loading", self._on_map_loading)

    def _on_map_loading(self, loading: bool):
        if loading:
            if self.canvas is not None:
                self.canvas.grid_forget()

            self.loading_frame.place(relx=0.5, rely=0.5, anchor="center")
            self.loading_progress.start()
        else:
            self._on_game_start()
            self.loading_progress.stop()
            self.loading_frame.place_forget()

    def _on_game_start(self):
        self.canvas = MapCanvas(self.left_frame)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        # Ensure canvas is drawn under the loading frame if it's active
        self.loading_frame.lift()
