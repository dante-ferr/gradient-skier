import customtkinter as ctk
from config import config
from typing import cast


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent):

        super().__init__(parent, fg_color="transparent")

        self.after(300, self._pack_zoom_slider)

    def _pack_zoom_slider(self):
        from state_managers import canvas_state_manager

        zoom_container = ctk.CTkFrame(self, fg_color="transparent", width=64)
        zoom_container.pack(anchor="w")

        zoom_label = ctk.CTkLabel(zoom_container, text="Zoom", font=("", 16))
        zoom_label.pack(padx=(0, 4))

        number_of_steps = (
            config.canvas.ZOOM_RIGHT_OFFSET + config.canvas.ZOOM_LEFT_OFFSET
        ) // config.canvas.STEPS_PER_SCROLL
        zoom_slider = ctk.CTkSlider(
            zoom_container,
            from_=0,
            to=config.canvas.ZOOM_LEFT_OFFSET + config.canvas.ZOOM_RIGHT_OFFSET,
            number_of_steps=int(number_of_steps),
            width=128,
            command=self._handle_zoom,
        )
        zoom_slider.pack(fill="x")

        def _callback(value):
            zoom_slider.set(self._actual_zoom_to_slider_zoom(value))

        canvas_state_manager.add_callback("zoom", _callback)

    def _handle_zoom(self, value: float):
        from state_managers import canvas_state_manager

        zoom_var = cast(ctk.DoubleVar, canvas_state_manager.vars["zoom"])
        zoom_var.set(self._slider_zoom_to_actual_zoom(value))

    def _actual_zoom_to_slider_zoom(self, zoom: float):
        from state_managers import canvas_state_manager

        initial_zoom_var = cast(
            ctk.DoubleVar, canvas_state_manager.vars["initial_zoom"]
        )
        min_zoom = initial_zoom_var.get() - config.canvas.ZOOM_LEFT_OFFSET

        return zoom - min_zoom

    def _slider_zoom_to_actual_zoom(self, zoom: float):
        from state_managers import canvas_state_manager

        initial_zoom_var = cast(
            ctk.DoubleVar, canvas_state_manager.vars["initial_zoom"]
        )
        min_zoom = initial_zoom_var.get() - config.canvas.ZOOM_LEFT_OFFSET

        return zoom + min_zoom
