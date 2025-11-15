import customtkinter as ctk
from interface.components.svg_image import SvgImage
from interface.theme import theme
from src.config import config
from typing import cast


class ToolBox(ctk.CTkFrame):
    def __init__(
        self, tools_frame: "ToolsFrame", tool_name: str, icon_image: ctk.CTkImage
    ):
        from state_managers import game_state_manager

        super().__init__(tools_frame, fg_color="transparent")
        self.tools_frame = tools_frame
        self.tool_name = tool_name

        label = ctk.CTkLabel(self, image=icon_image, text="")
        label.pack(padx=4.8, pady=4.8)

        label.bind("<Button-1>", self._on_click)
        label.bind("<Enter>", lambda event: self.activate())
        label.bind("<Leave>", lambda event: self.deactivate())

    def _on_click(self, event):
        from state_managers import game_state_manager

        selected_tool_var = cast(
            ctk.StringVar, game_state_manager.vars["selected_tool"]
        )
        selected_tool_var.set(self.tool_name)

    def activate(self):
        self.configure(fg_color=("gray75", "gray25"))

    def deactivate(self):
        from state_managers import game_state_manager

        selected_tool_var = cast(
            ctk.StringVar, game_state_manager.vars["selected_tool"]
        )
        if selected_tool_var.get() == self.tool_name:
            return

        self.configure(fg_color="transparent")


class ToolsFrame(ctk.CTkFrame):
    TOOL_SIZE = 32

    def __init__(self, parent):
        from state_managers import game_state_manager

        super().__init__(parent, fg_color="transparent")

        self.tool_boxes = self._create_tool_boxes()
        selected_tool_var = cast(
            ctk.StringVar, game_state_manager.vars["selected_tool"]
        )
        self.selected_tool = self.tool_boxes[selected_tool_var.get()]

        game_state_manager.add_callback("selected_tool", self._handle_tool_selected)

        self._grid_tool_boxes()

    def _handle_tool_selected(self, tool_name: str):
        self.selected_tool.deactivate()
        self.selected_tool = self.tool_boxes[tool_name]
        self.selected_tool.activate()

    def _grid_tool_boxes(self):
        for i, (tool_name, tool_box) in enumerate(self.tool_boxes.items()):
            tool_box.grid(row=0, column=i, padx=1)

    def _create_tool_boxes(self):
        dumper_truck_icon = SvgImage(
            svg_path=str(config.ASSETS_PATH / "svg" / "dumper_truck.svg"),
            fill=theme.icon_color,
            stroke=theme.icon_color,
            size=(self.TOOL_SIZE, self.TOOL_SIZE),
        )
        filler_box = ToolBox(self, "filler", dumper_truck_icon.get_ctk_image())

        dynamite_icon = SvgImage(
            svg_path=str(config.ASSETS_PATH / "svg" / "dynamite.svg"),
            fill=theme.icon_color,
            stroke=theme.icon_color,
            size=(self.TOOL_SIZE, self.TOOL_SIZE),
        )
        excavator_box = ToolBox(self, "excavator", dynamite_icon.get_ctk_image())

        bulldozer_icon = SvgImage(
            svg_path=str(config.ASSETS_PATH / "svg" / "bulldozer.svg"),
            fill=theme.icon_color,
            stroke=theme.icon_color,
            size=(self.TOOL_SIZE, self.TOOL_SIZE),
        )
        grader_box = ToolBox(self, "grader", bulldozer_icon.get_ctk_image())

        return {box.tool_name: box for box in [filler_box, excavator_box, grader_box]}
