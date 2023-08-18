import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from typing import Union

from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSlot, QFileSystemWatcher
from PyQt6.QtWidgets import QWidget

def apply_css_stylesheet(widget: QWidget, path_to_css: Union[str, Path]):
    with open(path_to_css, "r") as file:
        logger.info(f"Reading CSS file from: {path_to_css}")
        css = file.read()
        logger.info(f"Setting stylesheet property for {widget}")
        widget.setStyleSheet(css)

class CSSFileWatcher(QFileSystemWatcher):
    def __init__(self, path_to_css: Union[str, Path], parent=None):
        super().__init__(parent)
        self.addPath(str(path_to_css))
        self.parent = parent
        self.fileChanged.connect(self._file_changed)

    @pyqtSlot(str)
    def _file_changed(self, path: Path):
        logger.info(f"CSS file changed: {path} - applying to {self.parent}")
        try:
            apply_css_stylesheet(self.parent, path)
        except Exception as e:
            logger.error(f"Error setting stylesheet: {e}")