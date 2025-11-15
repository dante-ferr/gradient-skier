import customtkinter as ctk
from typing import Any, Callable
from config import config


class GameStatsFrame(ctk.CTkFrame):
    LABEL_INIT_PARAMS: dict[str, Any] = {"font": ("", 16)}
    LABEL_PACK_PARAMS: dict[str, Any] = {"padx": (0, 4), "anchor": "w"}

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent", width=300)
        self.pack_propagate(False)

        self.stat_labels: list[ctk.CTkLabel] = []

        self._setup_stat_displays()
        self._setup_hovered_gradient_display()
        self._setup_visibility_control()

    def _create_stat_display(
        self, manager, state_var: str, formatter: Callable, initial_pack: bool = True
    ) -> ctk.CTkLabel:
        label = ctk.CTkLabel(self, text="", **self.LABEL_INIT_PARAMS)
        if initial_pack:
            label.pack(**self.LABEL_PACK_PARAMS)
        self.stat_labels.append(label)

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

        for label in self.stat_labels:
            if not is_loading:
                # Re-pack if not already visible, except for the hover label which manages itself.
                if not label.winfo_ismapped() and label != self.stat_labels[-1]:
                    label.pack(**self.LABEL_PACK_PARAMS)
            else:
                label.pack_forget()

    def _setup_visibility_control(self):
        """Binds the visibility of the stat labels to the map/path loading state."""
        from state_managers import canvas_state_manager

        canvas_state_manager.add_callback("map_loading", self._update_visibility)
        canvas_state_manager.add_callback("path_loading", self._update_visibility)
