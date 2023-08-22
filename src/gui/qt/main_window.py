import logging
logger = logging.getLogger(__name__)

import multiprocessing
from pathlib import Path
from typing import Union, Callable, List

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QDockWidget,
    QFileDialog
)

from src.data_layer.session_models.session_info_model import SessionInfoModel
from src.data_layer.session_models.post_processing_parameter_models import PostProcessingParameterModel

from src.gui.qt.actions_and_menus.actions import Actions
from src.gui.qt.actions_and_menus.menu_bar import MenuBar

from src.gui.qt.stylesheets.css_file_watcher import CSSFileWatcher, apply_css_stylesheet
from src.gui.qt.stylesheets.scss_file_watcher import SCSSFileWatcher

from src.gui.qt.utilities.get_qt_app import get_qt_app
from src.gui.qt.utilities.update_most_recent_session_toml import update_most_recent_session_toml

from src.gui.qt.widgets.active_session_info_widget import ActiveSessionInfoWidget
from src.gui.qt.widgets.central_tab_widget import CentralTabWidget
from src.gui.qt.widgets.control_panel_widget import ControlPanelWidget
from src.gui.qt.widgets.directory_view_widget import DirectoryViewWidget
from src.gui.qt.widgets.home_widget import HomeWidget
from src.gui.qt.widgets.import_videos_wizard import ImportVideosWizard
from src.gui.qt.widgets.log_view_widget import LogViewWidget
from src.gui.qt.widgets.control_panel.process_mocap_data_panel import ProcessMotionCaptureDataPanel

from src.system.paths_and_filenames.folder_and_filenames import (
    PATH_TO_LOGO_SVG
)
from src.system.paths_and_filenames.path_getters import (
    get_sessions_folder_path,
    get_scss_stylesheet_path,
    get_css_stylesheet_path,
    create_new_session_folder,
)

from src.utilities.remove_empty_directories import remove_empty_directories



REBOOT_EXIT_CODE = 123456789

class MainWindow(QMainWindow):
    def __init__(
        self,
        data_folder_path: Union[str, Path],
        parent=None
    ):
        super().__init__(parent=parent)
        # self.setObjectName("MainWindow")

        self._log_view_widget = LogViewWidget()
        logger.info("Initializing MainWindow")

        # Initialize variables
        self._data_folder_path = data_folder_path
        self._kill_thread_event = multiprocessing.Event()
        self._actions = Actions(main_window=self)

        # Setup Window
        self._size_main_window(.9, .9)
        self.setWindowIcon(QIcon(str(PATH_TO_LOGO_SVG)))
        self.setWindowTitle("Bennie MoCap")

        # TODO: Do we need this, what does it accomplish
        # Build UI Widgets
        # dummy_widget = QWidget()
        # dummy_widget.setStyleSheet("background-color:red;")
        # self._layout = QHBoxLayout()
        # dummy_widget.setLayout(self._layout)
        # self.setCentralWidget(dummy_widget)

        # CSS Styling
        self._css_file_watcher = self._setup_stylesheet()

        # Menu Bar
        self._menu_bar = MenuBar(actions=self._actions, parent=self)
        self.setMenuBar(self._menu_bar)

        # Active Session Info Widget
        self._active_session_info_widget = ActiveSessionInfoWidget(parent=self)
        self._active_session_info_widget.new_active_session_selected_signal.connect(self._handle_new_active_session_selected)
        
        # Directory View Widget
        self._directory_view_widget = DirectoryViewWidget(
                                                top_level_folder=self._data_folder_path, 
                                                get_active_session_info_callable=self._active_session_info_widget.get_active_session_info
                                                )
        self._directory_view_widget.expand_directory_to_path(get_sessions_folder_path())
        self._directory_view_widget.new_active_session_selected_signal.connect(self._active_session_info_widget.set_active_session)

        # Central Tab Widget
        self._central_tab_widget = self._create_central_tab_widget()
        self.setCentralWidget(self._central_tab_widget)

        # Tools Dock Widget
        self._tools_dock_widget = self._create_tools_dock_widget()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._tools_dock_widget)

        # Control Panel Widget
        self._control_panel_widget = self._create_control_panel_widget(log_update=self._log_view_widget.add_log)
        self._tools_dock_widget.setWidget(self._control_panel_widget)

        # Log View Widget
        log_view_dock_widget = QDockWidget("Log View", self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, log_view_dock_widget)
        log_view_dock_widget.setWidget(self._log_view_widget)
        log_view_dock_widget.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)

        logger.info("Finished initializing MainWindow")


    #----------------
    # PRIVATE METHODS
    # ---------------

    def _size_main_window(self, width_fraction: float = 0.8, height_fraction: float = 0.8):
        screen = QApplication.primaryScreen().availableGeometry()
        width = screen.width() * width_fraction
        height = screen.height() * height_fraction
        # center screen
        left = (screen.width() - width) / 2
        top = (screen.height() - height) / 2
        # apply
        self.setGeometry(int(left), int(top), int(width), int(height))

    def _setup_stylesheet(self) -> CSSFileWatcher:
        apply_css_stylesheet(self, get_css_stylesheet_path())
        SCSSFileWatcher(path_to_scss=get_scss_stylesheet_path(), path_to_css=get_css_stylesheet_path(), parent=self)
        return CSSFileWatcher(path_to_css=get_css_stylesheet_path(), parent=self)

    def _create_central_tab_widget(self) -> CentralTabWidget:
        self._home_widget = HomeWidget(self)
        central_tab_widget = CentralTabWidget(
            parent=self,
            home_widget=self._home_widget,
            directory_view_widget=self._directory_view_widget,
            active_session_info_widget = self._active_session_info_widget
        )
        return central_tab_widget
    
    def _create_tools_dock_widget(self) -> QDockWidget:
        widget = QDockWidget("Control Panel", self)
        widget.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        widget.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        return widget
    
    def _create_control_panel_widget(self, log_update: Callable) -> ControlPanelWidget:

        # TODO: add controls to control panel widget
        self._process_motion_capture_data_panel = ProcessMotionCaptureDataPanel(
            session_processing_parameters=PostProcessingParameterModel(),
            get_active_session_info=self._active_session_info_widget.get_active_session_info,
            kill_thread_event=self._kill_thread_event,
            log_update=log_update
        )
        self._process_motion_capture_data_panel.processing_finished.connect(self._handle_processing_finished_signal)

        return ControlPanelWidget(
            process_motion_capture_data_panel=self._process_motion_capture_data_panel,
            parent=self
        )
    
    def _handle_processing_finished_signal(self):
        # TODO: Implement _handle_processing_finished_signal
        pass
    
    def _handle_import_videos(self, video_paths: List[str], save_folder: Path):
        # save_folder.mkdir(parents=True, exist_ok=True)

        if len(video_paths) == 0:
            logger.error("No videos to import")
            return
        
        self._active_session_info_widget.set_active_session(session_folder_path=save_folder)

        # TODO: at this point the videos have been framerate matched and saved to the synchronized videos folder
        # Next step is to synchronized based on audio

    def _handle_new_active_session_selected(self, session_info_model: SessionInfoModel):
        logger.info(f"New active session selected: {session_info_model.path}")

        path =  Path(session_info_model.path)
        path.mkdir(parents=True, exist_ok=True)

        if str(path.parent) != get_sessions_folder_path():
            self._directory_view_widget.set_folder_as_root(path.parent)
        else:
            self._directory_view_widget.set_folder_as_root(path)

        self._active_session_info_widget.update_parameter_tree()
        self._directory_view_widget.handle_new_active_session_selected()

        # TODO: Update control panel?
        # TODO: update most recent session toml?
        



    # --------------
    # PUBLIC METHODS
    # --------------

    def update(self):
        super().update()

    def handle_start_new_session_action(self):
        logger.info("Starting new session by importing videos")

        # create new session folder
        session_path = create_new_session_folder()
        # create session info model
        session_info_model = SessionInfoModel(session_path)
        update_most_recent_session_toml(session_info_model=session_info_model)



        import_videos_wizard = ImportVideosWizard(parent=self)
        import_videos_wizard.exec()

        # import_videos_path = QFileDialog.getExistingDirectory(
        #     self,
        #     "Select a folder containing motion capture session videos. One video file per camera in the capture area.",
        #     str(Path.home())
        # )
        # if len(import_videos_path) == 0:
        #     logger.info("User cancelled importing videos")
        #     return
        
        # import_video_window = ImportVideosWizard(
        #     parent=self,
        #     import_path=import_videos_path,
        #     kill_thread_event=self._kill_thread_event
        # )
        # import_video_window.video_import_finished.connect(self._handle_import_videos)
        # import_video_window.exec()
        # TODO: Implement handle_start_new_session_action


    def handle_load_existing_session_action(self):
        logger.info("Opening 'Load Existing Session' dialog")
        path = QFileDialog.getExistingDirectory(self, "Select a session folder", str(get_sessions_folder_path()))
        if len(path) == 0:
            logger.info("User cancelled 'Load Exisiting Session' dialog")
            return
        logger.info(f"User selected session path: {path}")
        self._active_session_info_widget.set_active_session(session_folder_path=path)
        self._central_tab_widget.setCurrentIndex(2)

    def kill_threads_and_processes(self):
        logger.info("Killing running threads and processes")
        self._kill_thread_event.set()

    def reboot_gui(self):
        logger.info("Rebooting GUI")
        get_qt_app().exit(REBOOT_EXIT_CODE)

    def closeEvent(self, a0) -> None:
        logger.info("MainWindow 'closeEvent'")

        try:
            remove_empty_directories(get_sessions_folder_path())
        except Exception as e:
            logger.error(f"Error removing empty directories: {e}") 

        super().closeEvent(a0)
        