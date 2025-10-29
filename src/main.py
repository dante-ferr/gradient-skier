from bootstrap import *
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def main():
    from interface.app import App

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
