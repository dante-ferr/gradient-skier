from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from interface.app import App


class AppManager:
    def __init__(self):

        self.app: "None | App" = None


app_manager = AppManager()
