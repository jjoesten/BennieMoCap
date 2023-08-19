import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from typing import Union
import threading
import os

from pyqtgraph.parametertree import Parameter, ParameterTree

from PyQt6.QtCore import pyqtSignal, QAbstractTableModel
from PyQt6.QtGui import QFileSystemModel, QPixmap, QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QFileDialog,
    QListWidget,
    QLabel,
    QTableWidget,
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

from src.system.paths_and_filenames.folder_and_filenames import SYNCHRONIZED_VIDEOS_FOLDER_NAME, PATH_TO_LOGO_PNG
from src.system.paths_and_filenames.path_getters import get_sessions_folder_path, create_new_session_folder, home_dir
from src.utilities.video import get_video_paths

from src.data_layer.session_models.video_model import VideoModel

NO_FILES_FOUND_STRING = "No '.mp4' video files found"

class ImportVideosWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # style = self.wizardStyle()
        # self.setWizardStyle(QWizard.WizardStyle.AeroStyle)
        # style = self.wizardStyle()

        self.setWizardStyle(QWizard.WizardStyle.ClassicStyle)

        # Add pages
        self.addPage(IntroPage())
        self.addPage(SelectVideosPage())
        self.addPage(SynchronizationPage())
        self.addPage(ConclusionPage())

        self.setWindowTitle("Import Videos")

    # def accept(self):

    #     super(ImportVideosWizard, self).accept()


class IntroPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setTitle("Introduction")
        label = QLabel("This wizard will import the selected videos into this new session by first ensuring that all videos \
                       have the same framerate. If the framerates between videos do not match the videos will be modified so \
                       they all match the lowest framerate of the group. You will then be presented with options for synchronizing \
                       the videos. Synchronized videos will be save to the synchronized_videos folder and you will be returned \
                       to the application to continue 2d and 3d data processing.")
        label.setWordWrap(True)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(label)

class SelectVideosPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setTitle("Select Videos")

        self._import_video_path = []
        self._session_folder = create_new_session_folder()
        

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._import_videos_button = QPushButton("Import Videos")
        self._import_videos_button.clicked.connect(self._open_file_dialog)
        
        self._import_videos_table_view = QTreeView(self)
        self._standard_model = QStandardItemModel(self)
        self._standard_model.setHorizontalHeaderLabels(["","FPS","Sample Rate","Duration","Resolution","Size(MB)"])

        self._import_videos_table_view.setModel(self._standard_model)
        # self._import_videos_table_view.expandAll()


        layout.addWidget(self._import_videos_table_view)
        layout.addWidget(self._import_videos_button)
        

    def _prepare_row(self, filename, fps, sampling_rate, duration, resolution, size):
        return [QStandardItem(filename), QStandardItem(str(fps)), QStandardItem(str(sampling_rate)), QStandardItem(str(duration)), QStandardItem(resolution), QStandardItem(f"{size} MB")]

    def _open_file_dialog(self):
        import_file_paths = QFileDialog.getOpenFileNames(directory=str(home_dir()))
        self._video_file_paths = [str(path) for path in import_file_paths[0]]
        
        # create model, get details about the videos to be imported
        self._video_model_list: list[VideoModel] = []
        for video_path in self._video_file_paths:
            self._video_model_list.append(VideoModel(video_path=video_path))

        
        item = self._standard_model.invisibleRootItem()
        for video_model in self._video_model_list:
            item.appendRow(self._prepare_row(video_model.filename, video_model.fps, video_model.audio_sample_rate, video_model.duration, video_model.resolution, video_model.size))
        self._standard_model.dataChanged.emit()



        

class SynchronizationPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setTitle("Synchronization")

class ConclusionPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setTitle("Conclusion")
        self._label = QLabel("Conclusion")
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)

    def initializePage(self) -> None:
        finish_text = "Finish" #self.wizard().buttonText(QWizard.FinishButton)
        finish_text = finish_text.replace('&', '')
        self._label.setText(f"Click {finish_text} to return to application")


    # video_import_finished = pyqtSignal(list, Path)

    # def __init__(self, import_path: Union[str, Path], kill_thread_event: threading.Event, parent=None):
    #     super().__init__(parent=parent)
    #     self._kill_thread_event = kill_thread_event
    #     self._import_path = import_path

    #     # list of videos for this session
    #     self._video_file_paths = [str(path) for path in get_video_paths(video_folder=import_path)]

    #     # root folder for this session, setup and create folder and sub folders
    #     self._folder_name = create_new_session_folder()
    #     (self._folder_name / SYNCHRONIZED_VIDEOS_FOLDER_NAME).mkdir(exist_ok=True, parents=True)
        

    #     self.setWindowTitle("Import Videos")

    #     self._layout = QVBoxLayout()
    #     self.setLayout(self._layout)
        
    #     # Tree View
    #     self._import_directory_view = self._create_import_directory_view(import_path)
    #     self._layout.addWidget(self._import_directory_view)
        
    #     # List of video paths
    #     self._video_file_list_widget = self._create_video_file_list_widget()
    #     self._layout.addWidget(self._video_file_list_widget)


    #     self._form_layout = QFormLayout()
    #     self._layout.addLayout(self._form_layout)
        
    #     # Action button
    #     self._continue_button = QPushButton("Continue")
    #     self._continue_button.isDefault()
    #     self._continue_button.clicked.connect(self._handle_continue_button_clicked)
    #     self._layout.addWidget(self._continue_button)


    # def _create_import_directory_view(self, import_path: Path) -> QTreeView:
    #     self._file_system_model = QFileSystemModel()
    #     self._file_system_model.setRootPath(str(import_path))

    #     self._tree_view_widget = QTreeView()
    #     # self._layout.addWidget(self._tree_view_widget)
    #     self._tree_view_widget.setModel(self._file_system_model)
    #     self._tree_view_widget.setRootIndex(self._file_system_model.index(str(import_path)))
    #     self._tree_view_widget.setColumnWidth(0, 250)
    #     self._tree_view_widget.setHeaderHidden(False)
    #     self._tree_view_widget.setAlternatingRowColors(True)
    #     self._tree_view_widget.setWindowTitle(str(import_path))
    #     self._tree_view_widget.doubleClicked.connect(self._open_file)

    #     return self._tree_view_widget
    
    # def _create_video_file_list_widget(self) -> QListWidget:
    #     list_widget = QListWidget()
    #     list_widget.setWordWrap(True)
    #     if len(self._video_file_paths) == 0:
    #         list_widget.addItem(NO_FILES_FOUND_STRING)
    #     else:
    #         list_widget.addItems(self._video_file_paths)
    #     return list_widget

    # def _open_file(self):
    #     index = self._tree_view_widget.currentIndex()
    #     file_path = self._file_system_model.filePath(index)
    #     logger.info(f"Opening file from file_system_view_widget: {file_path}")
    #     os.startfile(file_path)

    # def _get_save_folder(self):
    #     return str(Path(get_sessions_folder_path()) / self._folder_name)

    # def _handle_continue_button_clicked(self, event):
    #     # Start match framerate thread worker
    #     self.match_framerate_thread_worker = MatchFramerateThreadWorker(input_folder_path=self._import_path, output_folder_path=Path(self._get_save_folder()), kill_thread_event=self._kill_thread_event)
    #     self.match_framerate_thread_worker.start()
    #     self.match_framerate_thread_worker.finished.connect(self._handle_framerate_work_completed)
        


    # def _handle_framerate_work_completed(self):
    #     self.video_import_finished.emit(self._video_file_paths, Path(self._get_save_folder()))
    #     self.accept()


class VideoFileTreeView(ParameterTree):
    def __init__(self, parent=None):
        super().__init__(parent=parent, showHeader=False)

    def setup_parameter_tree(self, video_model: VideoModel):
        if video_model is None:
            logger.debug("No video model provided - clearing tree")
            self.clear()
            return
        
        logger.debug(f"Setting up 'VideoInfoTreeView' for video {video_model.path}")
        self.clear()
        self.setParameters(self._create_parameter_tree(video_model=video_model))

    def _create_parameter_tree(self, video_model: VideoModel) -> Parameter:
        parameter_group = Parameter.create(
            name=f"Video: {video_model.filename}",
            type="str",
            value=video_model.filename,
        )