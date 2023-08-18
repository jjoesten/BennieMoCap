import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from typing import Union

from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSlot, QFileSystemWatcher

from src.gui.qt.stylesheets.compile_scss import compile_scss

class SCSSFileWatcher(QFileSystemWatcher):
    def __init__(self, path_to_scss: Union[str, Path], path_to_css: Union[str, Path], parent=None):
        super().__init__(parent)
        self.addPath(str(path_to_scss))
        self.parent = parent
        self.path_to_scss = path_to_scss
        self.path_to_css = path_to_css
        self.fileChanged.connect(self._file_changed)

    @pyqtSlot(str)
    def _file_changed(self, path: Path):
        logger.info(f"SCSS file changed: {path} - compiling")
        try:
            compile_scss(self.path_to_scss, self.path_to_css)
            logger.info("SCSS compiled")
        except Exception as e:
            logger.error(f"Error in SCSS compilation: {e}")