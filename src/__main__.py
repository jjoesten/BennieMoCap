import sys
from multiprocessing import freeze_support
from pathlib import Path

try:
    from src.gui.qt.main import qt_gui_main
except:
    base_package_path = Path(__file__).parent.parent
    print(f"adding base_package_path: {base_package_path} : to sys.path")
    sys.path.insert(0, str(base_package_path))
    from src.gui.qt.main import qt_gui_main

def main():
    import ctypes
    import src

    if sys.platform == "win32":
        appId = f"{src.__package_name__}_{src.__version__}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appId)

    qt_gui_main()

if __name__ == "__main__":
    freeze_support()
    print(f"Running `benniemocap.src.__main__ ` from - {__file__}")

    main()