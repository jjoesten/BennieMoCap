import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from typing import Union

from PyQt6.QtCore import pyqtSignal, QFileSystemWatcher
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget
from pyqtgraph.parametertree import Parameter, ParameterTree

from src.data_layer.session_models.session_info_model import SessionInfoModel
from src.system.paths_and_filenames.path_getters import get_most_recent_session_path


class ActiveSessionInfoWidget(QWidget):
    new_active_session_selected_signal = pyqtSignal(SessionInfoModel)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._active_session_info: SessionInfoModel = None
        self._directory_watcher = self._create_directory_watcher()

        self._active_session_view_widget = ActiveSessionTreeView(parent=self)

        self._layout.addWidget(self._active_session_view_widget)

    @property
    def active_session_info(self) -> SessionInfoModel:
        return self._active_session_info
    
    def get_active_session_info(self, return_path: bool = False):
        if self._active_session_info is None:
            most_recent_path = get_most_recent_session_path()
            if most_recent_path is not None:
                self.set_active_session(most_recent_path)
        if return_path:
            return self._active_session_info.path
        
        return self._active_session_info

    def set_active_session(self, session_folder_path: Union[str, Path]):
        logger.info(f"Setting active session to {session_folder_path}")

        self._active_session_info = SessionInfoModel(session_folder_path=session_folder_path)

        logger.debug(f"Emitting 'new_active_session_selected_signal' for session: {self._active_session_info.name}")
        self.new_active_session_selected_signal.emit(self._active_session_info)


    def _create_directory_watcher(self) -> QFileSystemWatcher:
        watcher = QFileSystemWatcher()
        watcher.fileChanged.connect(self._handle_directory_changed)
        watcher.directoryChanged.connect(self._handle_directory_changed)
        return watcher
    
    def _handle_directory_changed(self, path: str):
        logger.info(f"Directory changed: {path} - updating parameter tree")
        self.update_parameter_tree()

    def update_parameter_tree(self):
        logger.info("Updating parameter tree")
        self._active_session_view_widget.setup_parameter_tree(self._active_session_info)


class ActiveSessionTreeView(ParameterTree):
    def __init__(self, parent=None):
        super().__init__(parent=parent, showHeader=False)

    def setup_parameter_tree(self, session_info_model: SessionInfoModel):
        if session_info_model is None:
            logger.debug("No session info model provided - clearing parameter tree")
            self.clear()
            return
        
        logger.debug(f"Setting up 'ActiveSessionTreeView' for session: {session_info_model.name}")
        self.clear()
        self.setParameters(self._create_parameter_tree(session_info_model=session_info_model))

    def _create_parameter_tree(self, session_info_model: SessionInfoModel) -> Parameter:
        parameter_group = Parameter.create(
            name=f"Session Name: {session_info_model.name}",
            type="group",
            readonly=True,
            children=[
                dict(
                    name="Path",
                    type="str",
                    value=session_info_model.path,
                    readonly=True,

                ),
                dict(
                    name="Calibration TOML",
                    type="str",
                    value=session_info_model.calibration_toml_path,
                    readonly=True,
                ),
                dict(
                    name="Status",
                    type="group",
                    readonly=True,
                    children=[
                        dict(
                            name="Videos Framerate Mathces",
                            type="str",
                            value=session_info_model.videos_framerate_status_check,
                            readonly=True,
                        ),
                        dict(
                            name="Videos Synchronized",
                            type="str",
                            value=session_info_model.videos_synchronized_status_check,
                            readonly=True,
                        ),
                        dict(
                            name="2D data exists?",
                            type="str",
                            value=session_info_model.data2d_status_check,
                            readonly=True,
                        ),
                        dict(
                            name="3D data exists?",
                            type="str",
                            value=session_info_model.data3d_status_check,
                        ),
                        dict(
                            name="Center of Mass data exists?",
                            type="str",
                            value=session_info_model.com_status_check,
                            readonly=True,
                        ),
                        # TODO BLENDER
                    ]
                )
            ]
        )
        return parameter_group
