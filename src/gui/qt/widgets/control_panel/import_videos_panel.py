import logging
logger = logging.getLogger(__name__)

import threading
from typing import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QWidget,
    QStackedLayout,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QTreeView,
    QLabel, 
    QAbstractItemView
)

from src.data_layer.session_models.video_model import VideoModel
from src.data_layer.session_models.session_info_model import SessionInfoModel

from src.gui.qt.widgets.spinner_widget import QtWaitSpinner

from src.gui.qt.workers.match_framerate_thread_worker import MatchFramerateThreadWorker

class ImportVideosPanel(QWidget):
    video_import_finished = pyqtSignal(list, str)

    def __init__(self, get_active_session_info: Callable, kill_thread_event: threading.Event, log_update: Callable, parent=None):
        super().__init__(parent)
        self._kill_thread_event = kill_thread_event
        self._log_update = log_update
        self._active_session_info: SessionInfoModel = get_active_session_info()

        self._video_model_list: list[VideoModel] = []

        self._layout = QStackedLayout()
        self.setLayout(self._layout)

        # FIRST PAGE
        first_page_widget = QWidget()
        first_page_layout = QVBoxLayout()
        first_page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        first_page_widget.setLayout(first_page_layout)

        self._select_videos_button = QPushButton("Select Videos")
        self._select_videos_button.clicked.connect(self._select_videos_for_import)
        first_page_layout.addWidget(self._select_videos_button)

        self._import_videos_tree_view = QTreeView()
        self._import_videos_tree_view.setMaximumHeight(300)
        self._import_videos_tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._standard_model = QStandardItemModel()
        self._standard_model.setHorizontalHeaderLabels(["","FPS","Sample Rate","Duration","Resolution","Size"])
        self._import_videos_tree_view.setModel(self._standard_model)
        first_page_layout.addWidget(self._import_videos_tree_view)

        self._import_videos_button = QPushButton("Import Videos")
        self._import_videos_button.setEnabled(False)
        self._import_videos_button.clicked.connect(self._import_videos)
        first_page_layout.addWidget(self._import_videos_button)
        
        # SECOND PAGE
        second_page_widget = QWidget()
        second_page_layout = QVBoxLayout()
        second_page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        second_page_widget.setLayout(second_page_layout)

        self._second_page_status_label = QLabel("Importing Videos...")
        second_page_layout.addWidget(self._second_page_status_label)

        self._wait_spinner = QtWaitSpinner(self, center_on_parent=False)
        second_page_layout.addWidget(self._wait_spinner)

        
        self._layout.addWidget(first_page_widget)
        self._layout.addWidget(second_page_widget)





    def _select_videos_for_import(self):
        import_file_paths = QFileDialog.getOpenFileNames()[0]
        self._video_model_list = [VideoModel(path) for path in import_file_paths]

        item = self._standard_model.invisibleRootItem()
        for video_model in self._video_model_list:
            item.appendRow(self._prepare_row(video_model))
        self._import_videos_tree_view.resizeColumnToContents(0)

        if len(self._video_model_list) > 0:
            self._import_videos_button.setEnabled(True)

            
        
        

    def _import_videos(self):
        self._layout.setCurrentIndex(1)
        self._wait_spinner.start()
        self._wait_spinner.show()

        import_video_paths = [str(video_model.path) for video_model in self._video_model_list]
        self._match_framerate_thread_worker = MatchFramerateThreadWorker(
            input_file_list=import_video_paths, 
            output_folder_path=self._active_session_info.framerate_matched_videos_folder_path,
            kill_thread_event=self._kill_thread_event)
        self._match_framerate_thread_worker.start()
        self._match_framerate_thread_worker.finished.connect(self._framerate_matching_finished)


    def _framerate_matching_finished(self):
        self._wait_spinner.stop()
        self._wait_spinner.hide()
        self._second_page_status_label.setText("Finished importing videos")
        self.video_import_finished.emit(
            [str(video_model.path) for video_model in self._video_model_list],
            self._active_session_info.framerate_matched_videos_folder_path 
        )


    def _prepare_row(self, video_model: VideoModel):
        return [QStandardItem(str(video_model.path)), 
                QStandardItem(str(video_model.fps)), 
                QStandardItem(str(video_model.audio_sample_rate)), 
                QStandardItem(str(video_model.duration)), 
                QStandardItem(video_model.resolution), 
                QStandardItem(f"{video_model.size} MB")]
        

        