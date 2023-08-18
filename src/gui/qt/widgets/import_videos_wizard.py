import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from typing import Union
import threading
import os

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QListWidget,
    QLabel,
    QFormLayout,
    QLineEdit,
    QTreeView,
    QPushButton,
    QDialog,
    QCheckBox,
    QHBoxLayout
)

from src.gui.qt.workers.match_framerate_thread_worker import MatchFramerateThreadWorker
from src.gui.qt.workers.synchronize_videos_thread_worker import SynchronizeVideosThreadWorker

from src.system.paths_and_filenames.folder_and_filenames import SYNCHRONIZED_VIDEOS_FOLDER_NAME
from src.system.paths_and_filenames.path_getters import get_sessions_folder_path, create_new_session_folder
from src.utilities.video import get_video_paths

NO_FILES_FOUND_STRING = "No '.mp4' video files found"

class ImportVideosWizard(QDialog):
    video_import_finished = pyqtSignal(list, Path)

    def __init__(self, import_path: Union[str, Path], kill_thread_event: threading.Event, parent=None):
        super().__init__(parent=parent)
        self._kill_thread_event = kill_thread_event
        self._import_path = import_path

        # list of videos for this session
        self._video_file_paths = [str(path) for path in get_video_paths(video_folder=import_path)]

        # root folder for this session, setup and create folder and sub folders
        self._folder_name = create_new_session_folder()
        self._folder_name.mkdir(exist_ok=True, parents=True)
        (self._folder_name / SYNCHRONIZED_VIDEOS_FOLDER_NAME).mkdir(exist_ok=True, parents=True)
        

        self.setWindowTitle("Import Videos")

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        
        # Tree View
        self._import_directory_view = self._create_import_directory_view(import_path)
        self._layout.addWidget(self._import_directory_view)
        
        # List of video paths
        self._video_file_list_widget = self._create_video_file_list_widget()
        self._layout.addWidget(self._video_file_list_widget)


        self._form_layout = QFormLayout()
        self._layout.addLayout(self._form_layout)
        
        # Action button
        self._continue_button = QPushButton("Continue")
        self._continue_button.isDefault()
        self._continue_button.clicked.connect(self._handle_continue_button_clicked)
        self._layout.addWidget(self._continue_button)


    def _create_import_directory_view(self, import_path: Path) -> QTreeView:
        self._file_system_model = QFileSystemModel()
        self._file_system_model.setRootPath(str(import_path))

        self._tree_view_widget = QTreeView()
        # self._layout.addWidget(self._tree_view_widget)
        self._tree_view_widget.setModel(self._file_system_model)
        self._tree_view_widget.setRootIndex(self._file_system_model.index(str(import_path)))
        self._tree_view_widget.setColumnWidth(0, 250)
        self._tree_view_widget.setHeaderHidden(False)
        self._tree_view_widget.setAlternatingRowColors(True)
        self._tree_view_widget.setWindowTitle(str(import_path))
        self._tree_view_widget.doubleClicked.connect(self._open_file)

        return self._tree_view_widget
    
    def _create_video_file_list_widget(self) -> QListWidget:
        list_widget = QListWidget()
        list_widget.setWordWrap(True)
        if len(self._video_file_paths) == 0:
            list_widget.addItem(NO_FILES_FOUND_STRING)
        else:
            list_widget.addItems(self._video_file_paths)
        return list_widget

    def _open_file(self):
        index = self._tree_view_widget.currentIndex()
        file_path = self._file_system_model.filePath(index)
        logger.info(f"Opening file from file_system_view_widget: {file_path}")
        os.startfile(file_path)

    def _get_save_folder(self):
        return str(Path(get_sessions_folder_path()) / self._folder_name)

    def _handle_continue_button_clicked(self, event):
        # Start match framerate thread worker
        self.match_framerate_thread_worker = MatchFramerateThreadWorker(input_folder_path=self._import_path, output_folder_path=Path(self._get_save_folder()), kill_thread_event=self._kill_thread_event)
        self.match_framerate_thread_worker.start()
        self.match_framerate_thread_worker.finished.connect(self._handle_framerate_work_completed)
        


    def _handle_framerate_work_completed(self):
        self.video_import_finished.emit(self._video_file_paths, Path(self._get_save_folder()))
        self.accept()