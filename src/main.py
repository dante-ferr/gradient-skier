from bootstrap import *
from core import app_manager
import logging
from interface.app import App

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def main():
    app_manager.app = App()
    app_manager.app.mainloop()


if __name__ == "__main__":
    main()
