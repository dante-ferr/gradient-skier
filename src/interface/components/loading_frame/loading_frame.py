import customtkinter as ctk


class LoadingFrame(ctk.CTkFrame):
    def __init__(self, parent, text: str):
        super().__init__(parent, fg_color="transparent")

        self.loading_label = ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(size=20),
        )
        self.loading_label.pack(pady=10)
        self.loading_progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.loading_progress.pack(pady=10, padx=20, fill="x")

        self.loading_progress.start()
