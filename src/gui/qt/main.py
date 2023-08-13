import logging
import signal
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from src.gui.qt.main_window import MainWindow, REBOOT_EXIT_CODE
from src.gui.qt.utilities.get_qt_app import get_qt_app

from src.system.paths_and_filenames.path_getters import get_data_folder_path

logging.getLogger("matplotlib").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def sigint_handler(*args):
    QApplication.quit()

def qt_gui_main():
    logger.info("Starting main")
    signal.signal(signal.SIGINT, sigint_handler)
    app = get_qt_app()
    timer = QTimer()
    timer.start(500)

    while True:
        main_window = MainWindow(
            data_folder_path=get_data_folder_path()
        )
        logger.info("Showing MainWindow")
        # main_window.show()
        main_window.showMaximized()

        # Update main_window on timer timeout
        timer.timeout.connect(main_window.update)

        # Application Exiting
        error_code = app.exec()
        logger.info(f"Application exited with error code: {error_code}")
        main_window.close()

        if not error_code == REBOOT_EXIT_CODE:
            print("Application Exiting")
            break

        logger.info("'main' exited with reboot code, rebooting")

    sys.exit()