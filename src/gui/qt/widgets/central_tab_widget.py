import logging
logger = logging.getLogger(__name__)

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QTabWidget
)

from src.gui.qt.widgets.home_widget import HomeWidget

class CentralTabWidget(QTabWidget):
    def __init__(
        self,
        # TODO: widgets to be included in this tab widget
        home_widget: HomeWidget,
        parent=None
    ):
        super().__init__(parent=parent)

        # Widgets
        self._home_widget = home_widget
        
        # Create Tabs
        self._create_home_tab(self)



    def _create_home_tab(self, tab_widget: QTabWidget):
        logger.info("Creating Home Tab")
        tab_widget.addTab(self._home_widget, "Home")

        