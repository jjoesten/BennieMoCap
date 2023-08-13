import logging
logger = logging.getLogger(__name__)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel
)

class HomeWidget(QWidget):
    def __init__(
        self,

        parent: QWidget = None
    ):
        super().__init__(parent=parent)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self.sizePolicy().setHorizontalStretch(1)
        self.sizePolicy().setVerticalStretch(1)
        self._layout.addStretch(1)

        self._create_new_session_button = QPushButton("CREATE NEW SESSION")
        self._layout.addWidget(self._create_new_session_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self._load_existing_session_button = QPushButton("LOAD EXISTING SESSION")
        self._layout.addWidget(self._load_existing_session_button, alignment=Qt.AlignmentFlag.AlignCenter)