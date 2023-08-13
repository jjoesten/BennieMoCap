import logging
logger = logging.getLogger(__name__)

import multiprocessing
from pathlib import Path
from typing import Union

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout
)

from src.gui.qt.widgets.central_tab_widget import CentralTabWidget
from src.gui.qt.widgets.home_widget import HomeWidget

REBOOT_EXIT_CODE = 123456789

class MainWindow(QMainWindow):
    def __init__(
        self,
        data_folder_path: Union[str, Path],
        parent=None
    ):
        super().__init__(parent=parent)

        # Initialize variables
        self._data_folder_path = data_folder_path
        self._kill_thread_event = multiprocessing.Event()

        # TODO: Log View
        logger.info("Initializing MainWindow")

        # Setup Window
        self._size_main_window(.9, .9)
        self.setWindowTitle("Bennie MoCap")

        # Build UI Widgets
        # dummy_widget = QWidget()
        # dummy_widget.setStyleSheet("background-color:red;")
        # self._layout = QHBoxLayout()
        # dummy_widget.setLayout(self._layout)
        # self.setCentralWidget(dummy_widget)



        # Central Tab Widget
        self._central_tab_widget = self._create_central_tab_widget()
        self.setCentralWidget(self._central_tab_widget)


        logger.info("Finished initializing MainWindow")


    #----------------
    # PRIVATE METHODS
    # ---------------

    def _size_main_window(self, width_fraction: float = 0.8, height_fraction: float = 0.8):
        screen = QApplication.primaryScreen().availableGeometry()
        width = screen.width() * width_fraction
        height = screen.height() * height_fraction
        # center screen
        left = (screen.width() - width) / 2
        top = (screen.height() - height) / 2
        # apply
        self.setGeometry(int(left), int(top), int(width), int(height))

    def _create_central_tab_widget(self) -> CentralTabWidget:
        self._home_widget = HomeWidget(self)
        central_tab_widget = CentralTabWidget(home_widget=self._home_widget)

        return central_tab_widget

    # --------------
    # PUBLIC METHODS
    # --------------

    def update(self):
        super().update()
        