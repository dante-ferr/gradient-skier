import sys
import os
import logging
import ctypes
import multiprocessing

if getattr(sys, "frozen", False):
    bundle_dir = sys._MEIPASS
    os.environ["PATH"] = bundle_dir + os.pathsep + os.environ["PATH"]

    if hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(bundle_dir)
        except Exception:
            pass

    try:
        libcairo = os.path.join(bundle_dir, "libcairo-2.dll")
        if os.path.exists(libcairo):
            ctypes.CDLL(libcairo)
    except Exception:
        pass

else:
    try:
        import bootstrap
    except ImportError:
        print("Bootstrap module not found. Ensure you are in the correct directory.")

from core import app_manager
from interface.app import App

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def main():
    app_manager.app = App()
    app_manager.app.mainloop()

if __name__ == "__main__":
    multiprocessing.freeze_support()

    main()
