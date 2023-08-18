import logging
logger = logging.getLogger(__name__)

import os
from copy import copy

from PyQt6 import QtCore

from pathlib import Path
from typing import Union, Callable

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import (
    QLabel,
    QMenu,
    QTreeView,
    QVBoxLayout,
    QWidget,
    QPushButton
)
from qtpy import QtGui

from src.system.paths_and_filenames.path_getters import get_sessions_folder_path

class DirectoryViewWidget(QWidget):
    new_active_session_selected_signal = pyqtSignal(str)

    def __init__(self, top_level_folder: Union[str, Path], get_active_session_info_callable: Callable):
        super().__init__()
        logger.info("Creating DirectoryViewWidget")
        self._root_folder: Path = None

        self._file_system_model = QFileSystemModel()
        self._top_level_folder = Path(top_level_folder)

        self._get_active_session_info_callable = get_active_session_info_callable

        self._minimum_width = 300
        self.setMinimumWidth(self._minimum_width)
        
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._tree_view_widget = QTreeView()
        self._tree_view_widget.setHeaderHidden(False)
        self._tree_view_widget.setModel(self._file_system_model)
        self._tree_view_widget.setAlternatingRowColors(True)
        self._tree_view_widget.setColumnWidth(0, 250)
        self._tree_view_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree_view_widget.customContextMenuRequested.connect(self._context_menu)
        self._tree_view_widget.doubleClicked.connect(self._open_file)        
        self._layout.addWidget(self._tree_view_widget)

        if self._top_level_folder is not None:
            self.set_folder_as_root(self._top_level_folder)

        self._show_data_folder_button = QPushButton("Show Root Data Folder")
        self._show_data_folder_button.clicked.connect(lambda: self.set_folder_as_root(self._top_level_folder))
        self._layout.addWidget(self._show_data_folder_button)

        self._path_label = QLabel(str(self._top_level_folder))
        self._layout.addWidget(self._path_label)


    def _context_menu(self):
        menu = QMenu()
        open = menu.addAction("Open File")
        open.triggered.connect(self._open_file)

        go_to_parent_directory = menu.addAction("Go to parent directory")
        go_to_parent_directory.triggered.connect(self._go_to_parent_directory)

        cursor = QtGui.QCursor()
        menu.exec(cursor.pos())

    def _open_file(self):
        index = self._tree_view_widget.currentIndex()
        file = self._file_system_model.filePath(index)
        logger.info(f"Opening file from DirectoryViewWidget: {file}")
        os.startfile(file)

    def _go_to_parent_directory(self):
        logger.debug(f"Setting parent directory as root: {self._root_folder.parent}")
        self.set_folder_as_root(self._root_folder.parent)
        self.expand_directory_to_path(self._root_folder, collapse_other_directories=False)





    def expand_directory_to_path(self, path: Union[str, Path], collapse_other_directories: bool = True):
        if collapse_other_directories:
            logger.debug("Collapsing other directories")
            self._tree_view_widget.collapseAll()
        logger.debug(f"Expanding directory at path: {str(path)}")
        orig_index = self._file_system_model.index(str(path))
        self._tree_view_widget.expand(orig_index)

        parent_path = copy(path)
        while Path(self._file_system_model.rootPath()) in Path(parent_path).parents:
            parent_path = Path(parent_path).parent
            index = self._file_system_model.index(str(parent_path))
            logger.debug(f"Expanding parent directory at path: {str(parent_path)}")
            self._tree_view_widget.expand(index)

        self._tree_view_widget.scrollTo(orig_index)

    def set_folder_as_root(self, folder: Union[str, Path]):
        logger.info(f"Setting root folder to {str(folder)}")
        self._root_folder = folder
        self._tree_view_widget.setWindowTitle(str(folder))
        self._file_system_model.setRootPath(str(folder))
        self._tree_view_widget.setRootIndex(self._file_system_model.index(str(folder)))
        self._tree_view_widget.setColumnWidth(0, int(self._minimum_width * 0.9))

    def handle_new_active_session_selected(self) -> None:
        current_session_info = self._get_active_session_info_callable()
        if current_session_info is None:
            self._show_data_folder_button.hide()
            self.expand_directory_to_path(get_sessions_folder_path())
            return
        
        self._tree_view_widget.setCurrentIndex(self._file_system_model.index(str(current_session_info.path)))

        if current_session_info.annotated_videos_folder_path is not None:
            self.expand_directory_to_path(current_session_info.annotated_videos_folder_path)
        elif current_session_info.synchronized_videos_folder_path is not None:
            self.expand_directory_to_path(current_session_info.synchronized_videos_folder_path)
        else:
            self.expand_directory_to_path(current_session_info.path)
            


    