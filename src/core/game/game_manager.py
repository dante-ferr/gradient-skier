from ._match import Match
from config import config
import customtkinter as ctk
from typing import Callable, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from ._match import Match


class GameManager:
    def __init__(self):
        self.match: "Match | None" = None
        self.root: ctk.CTk | None = None
        self.match_start_callback: Callable | None = None
        self.on_step_callbacks: list[Callable[["Match"], None]] = []

    def set_root(self, root: ctk.CTk):
        self.root = root

    def _start_match(self, player_starting_position: tuple[int, int]):
        from core import map_manager

        if not map_manager.map:
            raise Exception("No map loaded")

        if map_manager.map.is_valid_start_point(*player_starting_position):
            self.match = Match(player_starting_position, map_manager.map)
            if self.match_start_callback:
                self.match_start_callback()

    def add_on_step_callback(self, callback: Callable[["Match"], None]):
        self.on_step_callbacks.append(callback)

    def _step_match(self):
        from state_managers import game_state_manager

        if not self.match:
            print("Match ended or not started.")
            return

        match_finished = self.match.step()

        for callback in self.on_step_callbacks:
            callback(self.match)

        if match_finished:
            print("Match finished! Match status:", self.match.status)

            attempts_var = cast(ctk.IntVar, game_state_manager.vars["attempts"])
            attempts_var.set(attempts_var.get() + 1)

            if self.match.status == "won":
                won_var = cast(ctk.BooleanVar, game_state_manager.vars["won"])

                if not won_var.get():
                    attempts_before_first_victory_var = cast(
                        ctk.IntVar,
                        game_state_manager.vars["attempts_before_first_victory"],
                    )
                    attempts_before_first_victory_var.set(attempts_var.get())

                    won_var.set(True)

            elif self.match.status == "lost":
                pass

            self.match = None
        else:
            # Schedule the next step
            if self.root:
                self.root.after(config.game.STEP_INTERVAL, self._step_match)

    def run_match_simulation(self, start_position: tuple[int, int]):
        if self.root is None:
            raise RuntimeError(
                "GameManager's root has not been set. Call set_root() from the main App."
            )

        self._start_match(start_position)
        if self.match:
            self._step_match()


game_manager = GameManager()
