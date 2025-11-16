import customtkinter as ctk


class RestartFrame(ctk.CTkFrame):
    def __init__(self, parent):
        from state_managers import game_state_manager

        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)

        self.restart_button = ctk.CTkButton(
            self,
            text="Start New Game",
            font=("", 16),
            command=self._start_new_game,
            width=192,
        )
        self.restart_button.grid(row=0, column=0, sticky="ne", pady=(4, 0))

        seed_frame = ctk.CTkFrame(self, fg_color="transparent")
        seed_frame.grid(row=1, column=0, sticky="ne", pady=(8, 0))

        self.seed_label = ctk.CTkLabel(
            seed_frame,
            text="Next map seed (optional)",
            font=("", 12),
        )
        self.seed_label.grid(row=0, column=0, sticky="w", padx=(0, 4))

        validate_cmd = self.register(self._validate_seed_input)
        self.seed_input = ctk.CTkEntry(
            seed_frame,
            font=("", 16),
            width=192,
            validate="key",
            validatecommand=(validate_cmd, "%P"),
        )
        self.seed_input.grid(row=1, column=0, sticky="ne")

        game_state_manager.add_callback(
            "player_can_interact", self._update_button_state
        )

    def _update_button_state(self, can_interact: bool):
        """Enables or disables the restart button based on player interaction state."""
        state = "normal" if can_interact else "disabled"
        self.restart_button.configure(state=state)

    def _validate_seed_input(self, new_value: str) -> bool:
        """Ensures that the entry only contains digits or is empty."""
        return new_value.isdigit() or new_value == ""

    def _start_new_game(self):
        from game import game_manager

        seed_str = self.seed_input.get()
        seed = None
        if seed_str.isdigit():
            seed = int(seed_str)

        game_manager.start_new_game(seed=seed)
