import customtkinter as ctk
from .sidebar import Sidebar
from .theme import theme
from .map_canvas import MapCanvas
from ._loading_manager import LoadingManager
import sys

ctk.deactivate_automatic_dpi_awareness()

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme(str(theme.path))

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        from game import game_manager
        from core import map_manager

        self.title("Gradient Engineer")

        if sys.platform.startswith("win"):
            self.state("zoomed")
        else:
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

        sidebar = Sidebar(self)
        sidebar.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        self.canvas: MapCanvas | None = None

        self.loading_manager = LoadingManager(
            self.left_frame, on_load_finish_callback=self._on_all_loading_finished
        )

        from state_managers import canvas_state_manager

        canvas_state_manager.add_callback(
            "map_loading",
            lambda loading: self.loading_manager.on_loading_change(
                "map", "Creating Map...", loading
            ),
        )
        canvas_state_manager.add_callback(
            "path_loading",
            lambda loading: self.loading_manager.on_loading_change(
                "path", "Calculating Path...", loading
            ),
        )

    def _on_all_loading_finished(self):
        """Callback for when the LoadingManager reports no more active loaders."""
        self._on_game_start()

    def _on_game_start(self):
        """Initializes and displays the main map canvas."""
        self.canvas = MapCanvas(self.left_frame)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.loading_manager.set_canvas(self.canvas)
        # Ensure loading container is on top if a new loading task started
        # while the canvas was being created.
        self.loading_manager.loading_container.lift()
