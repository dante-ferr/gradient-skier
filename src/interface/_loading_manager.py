import customtkinter as ctk
from typing import Dict, Callable, Optional
from interface.components.loading_frame import LoadingFrame


class LoadingManager:
    """Manages the display of one or more loading indicators."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        on_load_finish_callback: Callable[[], None],
    ):
        self.parent = parent
        self.on_load_finish_callback = on_load_finish_callback
        self.canvas_to_manage: Optional[ctk.CTkCanvas] = None

        self.loading_frames: Dict[str, LoadingFrame] = {}
        self.loading_container = ctk.CTkFrame(self.parent, fg_color="transparent")

    def set_canvas(self, canvas: ctk.CTkCanvas):
        """Sets the canvas widget that the loading manager will hide/show."""
        self.canvas_to_manage = canvas

    def on_loading_change(self, key: str, text: str, loading: bool):
        """Adds or removes a loading frame."""
        if loading:
            if key not in self.loading_frames:
                frame = LoadingFrame(self.loading_container, text)
                frame.pack(pady=5)
                self.loading_frames[key] = frame
        else:
            if key in self.loading_frames:
                self.loading_frames[key].destroy()
                del self.loading_frames[key]

        self._update_loading_state()

    def _update_loading_state(self):
        """Shows or hides the loading container based on the loading state."""
        is_loading = len(self.loading_frames) > 0

        if is_loading:
            self.loading_container.place(relx=0.5, rely=0.5, anchor="center")
            self.loading_container.lift()
            if self.canvas_to_manage:
                self.canvas_to_manage.grid_forget()
        else:
            self.loading_container.place_forget()
            self.on_load_finish_callback()
