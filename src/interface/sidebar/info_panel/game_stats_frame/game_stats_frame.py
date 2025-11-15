import customtkinter as ctk
from typing import Any, Callable
from config import config
from interface.components.svg_image import SvgImage
from interface.theme import theme

class GameStatsFrame(ctk.CTkFrame):
    LABEL_INIT_PARAMS: dict[str, Any] = {"font": ("", 16)}
    LABEL_PACK_PARAMS: dict[str, Any] = {"padx": (0, 4), "anchor": "w"}

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent", width=300)
        self.pack_propagate(False)

        self.stat_widgets: list[ctk.CTkFrame | ctk.CTkLabel] = []

        self._setup_stat_displays()
        self._setup_hovered_gradient_display()
        self._setup_visibility_control()

    def _create_stat_display(
        self, manager, state_var: str, formatter: Callable, initial_pack: bool = True
    ) -> ctk.CTkLabel:
        label = ctk.CTkLabel(self, text="", **self.LABEL_INIT_PARAMS)
        if initial_pack:
            label.pack(**self.LABEL_PACK_PARAMS)
        self.stat_widgets.append(label)

        def _update_label(value: Any):
            label.configure(text=formatter(value))

        manager.add_callback(state_var, _update_label)
        return label

    def _setup_stat_displays(self):
        """Creates and configures the primary game statistic labels."""
        from state_managers import game_state_manager

        self._create_stat_display(
            manager=game_state_manager,
            state_var="tool_charges_remaining",
            formatter=lambda v: f"Charges Left: {int(v)} / {config.tool.MAX_TOOL_CHARGES}",
        )
        self._create_stat_display(
            manager=game_state_manager,
            state_var="initial_path_cost",
            formatter=lambda v: f"Initial Cost: {v:.2f}",
        )
        self._create_stat_display(
            manager=game_state_manager,
            state_var="current_path_cost",
            formatter=lambda v: f"Current Cost: {v:.2f}",
        )
        self._create_stat_display(
            manager=game_state_manager,
            state_var="won",
            formatter=lambda v: f"Solved: {'Yes (WIN!)' if v else 'No'}",
        )
        self._setup_seed_display(game_state_manager)

    def _setup_seed_display(self, manager):
        """Creates the map seed display with a copy button."""
        seed_frame = ctk.CTkFrame(self, fg_color="transparent")
        seed_frame.pack(**self.LABEL_PACK_PARAMS)

        seed_label = ctk.CTkLabel(seed_frame, text="", **self.LABEL_INIT_PARAMS)
        seed_label.pack(side="left")
        self.stat_widgets.append(seed_frame)

        def _update_label(value: Any):
            seed_label.configure(text=f"Map Seed: {value}")

        manager.add_callback("current_seed", _update_label)

        copy_svg = SvgImage(
            svg_path=str(config.ASSETS_PATH / "svg" / "copy.svg"),
            fill=theme.icon_color,
            stroke=theme.icon_color,
            size=(16, 16),
        )
        copy_button = ctk.CTkButton(
            seed_frame,
            image=copy_svg.get_ctk_image(),
            text="",
            width=20,
            height=20,
            fg_color="transparent",
            command=self._copy_seed_to_clipboard,
        )
        copy_button.pack(side="right", padx=(5, 0))

    def _setup_hovered_gradient_display(self):
        """Creates and configures the label for the hovered map gradient."""
        from state_managers import canvas_state_manager

        hover_label = self._create_stat_display(
            manager=canvas_state_manager,
            state_var="hovered_gradient",
            formatter=lambda v: f"Map Gradient: {v}",
            initial_pack=False,
        )

        def _update_hovered_gradient_display(value: str):
            if value:
                hover_label.pack(**self.LABEL_PACK_PARAMS)
            else:
                hover_label.pack_forget()

        canvas_state_manager.add_callback(
            "hovered_gradient", _update_hovered_gradient_display
        )

    def _update_visibility(self, loading: bool):
        # This method will be called with the new value, but we need to check both states.
        from state_managers import canvas_state_manager

        is_loading = (
            canvas_state_manager.vars["map_loading"].get()
            or canvas_state_manager.vars["path_loading"].get()
        )

        for widget in self.stat_widgets:
            if not is_loading:
                # Re-pack if not already visible, except for the hover label which manages itself.
                if not widget.winfo_ismapped() and widget != self.stat_widgets[-1]:
                    widget.pack(**self.LABEL_PACK_PARAMS)
            else:
                widget.pack_forget()

    def _setup_visibility_control(self):
        """Binds the visibility of the stat labels to the map/path loading state."""
        from state_managers import canvas_state_manager

        canvas_state_manager.add_callback("map_loading", self._update_visibility)
        canvas_state_manager.add_callback("path_loading", self._update_visibility)

    def _copy_seed_to_clipboard(self):
        from state_managers import game_state_manager

        seed = str(game_state_manager.vars["current_seed"].get())
        self.clipboard_clear()
        self.clipboard_append(seed)
