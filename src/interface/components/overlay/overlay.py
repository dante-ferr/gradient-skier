import customtkinter as ctk


class Overlay(ctk.CTkToplevel):
    def __init__(self, title: str):
        from app_manager import app_manager

        super().__init__(app_manager.app)

        self.attributes("-topmost", True)

        self.title(title)

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_reqwidth() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_reqheight() // 2)
        self.geometry(f"+{x}+{y}")

        self.after(10, self.grab_set)
        self._post_init_config()

    def _close(self):
        self.grab_release()
        self.destroy()

    def _post_init_config(self):
        self.minsize(width=320, height=160)
        self.maxsize(width=320, height=480)
        self.resizable(False, False)
