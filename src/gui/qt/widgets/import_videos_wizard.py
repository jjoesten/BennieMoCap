import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from typing import Union
import threading
import os
from enum import IntEnum
from shutil import copyfile

from pyqtgraph.parametertree import Parameter, ParameterTree

from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSignal, QAbstractTableModel, pyqtProperty, QTimer
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
    QHBoxLayout,
)

from src.gui.qt.workers.match_framerate_thread_worker import MatchFramerateThreadWorker
from src.gui.qt.workers.synchronize_videos_thread_worker import SynchronizeVideosThreadWorker

from src.system.paths_and_filenames.folder_and_filenames import SYNCHRONIZED_VIDEOS_FOLDER_NAME, PATH_TO_LOGO_PNG, FRAMERATE_MATCHED_VIDEOS_FOLDER_NAME
from src.system.paths_and_filenames.path_getters import (
    get_sessions_folder_path, 
    create_new_session_folder, 
    home_dir, 
    get_most_recent_session_path, 
    get_synchronzied_videos_folder_path,
    get_framerate_matched_videos_folder_path
)

from src.gui.qt.widgets.spinner_widget import QtWaitSpinner

from src.data_layer.session_models.video_model import VideoModel

from src.utilities.video import change_framerate_ffmpeg, convert_video_to_mp4
from src.utilities.video_sync.audio_sync import synchronize_videos_from_audio

# from skelly_synchronize.skelly_synchronize import synchronize_videos_from_audio

NO_FILES_FOUND_STRING = "No '.mp4' video files found"

class Pages(IntEnum):
    Page_Intro = 0
    Page_Import = 1
    Page_Framerate = 2
    Page_Synchronize = 3
    Page_Conclusion = 4
class ImportVideosWizard(QWizard):



    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWizardStyle(QWizard.WizardStyle.ClassicStyle)

        self._import_video_paths: list[str] = []

        self._pages = [
            IntroPage(),
            SelectVideosPage(),
            FramerateMatchPage(),
            SynchronizationPage(),
            ConclusionPage()
        ]
        for page in self._pages:
            self.addPage(page)
        self.setStartId(Pages.Page_Intro)

        # Add pages
        # self.addPage(IntroPage())
        # self.addPage(SelectVideosPage())
        # self.addPage(SynchronizationPage())
        # self.addPage(ConclusionPage())

        self.setWindowTitle("Import Videos")

    @property
    def import_video_paths(self) -> list[str]:
        return self._import_video_paths

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

    def nextId(self) -> int:
        return Pages.Page_Import

class SelectVideosPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setTitle("Select Videos")

        self._import_video_paths = []
        self._video_model_list: list[VideoModel] = []
        self._session_folder = create_new_session_folder()        

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._import_videos_button = QPushButton("Import Videos")
        self._import_videos_button.clicked.connect(self._open_file_dialog)
        
        self._import_videos_tree_view = QTreeView(self)
        self._standard_model = QStandardItemModel(self)
        self._standard_model.setHorizontalHeaderLabels(["","FPS","Sample Rate","Duration","Resolution","Size(MB)"])
        self._import_videos_tree_view.setModel(self._standard_model)
        # self._import_videos_table_view.expandAll()

        layout.addWidget(self._import_videos_tree_view)
        layout.addWidget(self._import_videos_button)
        

    def _prepare_row(self, filename, fps, sampling_rate, duration, resolution, size):
        return [QStandardItem(filename), QStandardItem(str(fps)), QStandardItem(str(sampling_rate)), QStandardItem(str(duration)), QStandardItem(resolution), QStandardItem(f"{size} MB")]

    def _open_file_dialog(self):
        import_file_paths = QFileDialog.getOpenFileNames(directory=str(home_dir()))
        self._video_file_paths = [str(path) for path in import_file_paths[0]]
        
        # create model, get details about the videos to be imported
        for video_path in self._video_file_paths:
            self._video_model_list.append(VideoModel(video_path=video_path))
        # add video_model_list as wizard property
        self.registerField("import_video_model_list", self, "video_model_list")

        # add to tree view
        item = self._standard_model.invisibleRootItem()
        for video_model in self._video_model_list:
            item.appendRow(self._prepare_row(video_model.filename, video_model.fps, video_model.audio_sample_rate, video_model.duration, video_model.resolution, video_model.size))
        

    def nextId(self) -> int:
        # all videos have same framerate
        # i = self._video_model_list[0].fps
        # if all(video.fps == i for video in self._video_model_list):
        #     return Pages.Page_Synchronize
        # else:
        return Pages.Page_Framerate

    @pyqtProperty(list)
    def video_model_list(self):
        return self._video_model_list
    @video_model_list.setter
    def video_model_list(self, video_model_list):
        self._video_model_list = video_model_list

class FramerateMatchPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setTitle("Match Framerates")

        self._framerate_matched_video_model_list: list[VideoModel] = []

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        # setup ui
        # self._spinner = QtWaitSpinner(self, roundness=100.0, fade=70.0, radius=12, lines=20, line_length=16, line_width=3, speed=1.0, color=(213, 189, 136))
        self._spinner = QtWaitSpinner(self, center_on_parent=False)
        self._layout.addWidget(self._spinner)

        self._import_videos_tree_view = QTreeView(self)
        self._standard_model = QStandardItemModel(self)
        self._standard_model.setHorizontalHeaderLabels(["","FPS","Sample Rate","Duration","Resolution","Size(MB)"])
        self._import_videos_tree_view.setModel(self._standard_model)
        self._layout.addWidget(self._import_videos_tree_view)



        # match framerate and import videos
        # self.match_framerate_thread_worker = MatchFramerateThreadWorker(input_file_list=self)

    def initializePage(self) -> None:       

        self._spinner.start()
        self._spinner.show()

        QTimer.singleShot(10, self._start_page_work)

    def _start_page_work(self):
        self._import_video_model_list = self.field("import_video_model_list")
        self._match_framerates()

    def _match_framerates(self) -> None:
        new_video_paths = []
        min_fps = min([video_model.fps for video_model in self._import_video_model_list])
        for video_model in self._import_video_model_list:
            output_filename = f"{video_model.filename}"
            output_path = get_framerate_matched_videos_folder_path(get_most_recent_session_path()) / output_filename
            if video_model.fps > min_fps:
                change_framerate_ffmpeg(str(video_model.path), str(output_path), min_fps)
            else:
                copyfile(str(video_model.path), str(output_path))
            # convert to mp4
            if Path(output_filename).suffix.lower() != ".mp4":
                convert_video_to_mp4(str(output_path))
            
            new_video_paths.append(output_path)

        # add new files to treeview
        for video_path in new_video_paths:
            self._framerate_matched_video_model_list.append(VideoModel(video_path=video_path))
        item = self._standard_model.invisibleRootItem()
        for video_model in self._framerate_matched_video_model_list:
            item.appendRow(self._prepare_row(video_model.filename, video_model.fps, video_model.audio_sample_rate, video_model.duration, video_model.resolution, video_model.size))
    
    def _prepare_row(self, filename, fps, sampling_rate, duration, resolution, size):
        return [QStandardItem(filename), QStandardItem(str(fps)), QStandardItem(str(sampling_rate)), QStandardItem(str(duration)), QStandardItem(resolution), QStandardItem(f"{size} MB")] 
                




class SynchronizationPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setTitle("Synchronization")

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._spinner = QtWaitSpinner(self, center_on_parent=False)
        self._layout.addWidget(self._spinner)

    def initializePage(self) -> None:
        self._spinner.start()
        self._spinner.show()
        QTimer.singleShot(10, self._start_page_work)

    def _start_page_work(self) -> None:
        logger.debug("Starting video synchronization")
        
        fr_video_folder_path = get_framerate_matched_videos_folder_path(get_most_recent_session_path())
        sync_video_folder_path = get_synchronzied_videos_folder_path(get_most_recent_session_path())


        try:
            output_folder_path = synchronize_videos_from_audio(raw_video_folder_path=fr_video_folder_path, synchronized_video_folder_path=sync_video_folder_path, create_debug_plots_bool=True)
        except Exception as e:
            logger.exception("Something when wrong while synchronizing videos")
            logger.exception(e)

        # delete fr_videos

        
    


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