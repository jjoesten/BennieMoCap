import logging
logger = logging.getLogger(__name__)

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QTabWidget,
    QWidget
)

from src.gui.qt.widgets.home_widget import HomeWidget

class CentralTabWidget(QTabWidget):
    def __init__(
        self,
        directory_view_widget: QWidget,
        active_session_info_widget: QWidget,
        synchronization_widget: QWidget,
        data_visualization_widget: QWidget,
        # TODO: widgets to be included in this tab widget
        home_widget: HomeWidget,
        parent=None
    ):
        super().__init__(parent=parent)
        self.parent = parent

        # Widgets
        self._home_widget = home_widget
        self._directory_view_widget = directory_view_widget
        self._active_session_info_widget = active_session_info_widget
        self._data_visualization_widget = data_visualization_widget
        self._synchronization_widget = synchronization_widget
        
        # Create Tabs
        self.addTab(self._home_widget, "Home")
        self.addTab(self._synchronization_widget, "Video Synch")
        self.addTab(self._data_visualization_widget, "Data Visualization")
        self.addTab(self._directory_view_widget, "Directory View")
        self.addTab(self._active_session_info_widget, "Active Session Info")


        

        