import logging
logger = logging.getLogger(__name__)

import os
import threading
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QLayout,
)

from src.data_layer.session_models.session_info_model import SessionInfoModel

from src.gui.qt.workers.anipose_calibration_thread_worker import AniposeCalibrationThreadWorker

from src.system.paths_and_filenames.path_getters import get_last_successful_calibration_toml_path

from src.gui.qt.utilities.gui_state import GuiState, save_gui_state

class CalibrationControlPanel(QWidget):
    def __init__(self, get_active_session_info: Callable, kill_thread_event: threading.Event, gui_state: GuiState, parent=None):
        super().__init__(parent=parent)
        self._gui_state = gui_state
        self._has_toml_path = False
        self._calibration_toml_path = None
        self._user_selected_toml_path = None
        self._get_active_session_info = get_active_session_info
        self._kill_thread_event = kill_thread_event
        self._anipose_calibration_thread_worker = None

        self.parent = parent

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        
        self._selected_calibration_toml_label = QLabel("")
        self._selected_calibration_toml_label.setWordWrap(True)
        self._layout.addWidget(self._selected_calibration_toml_label)

        self._radio_button_layout = self._create_radio_button_layout()
        self._radio_button_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._layout.addLayout(self._radio_button_layout)
        self._layout.addStretch()

    @property
    def calibration_toml_path(self) -> str:
        return self._calibration_toml_path

    @property
    def radio_button_layout(self) -> QLayout:
        return self._radio_button_layout

        

    def _create_radio_button_layout(self) -> QFormLayout:
        radio_button_layout = QFormLayout()
        radio_button_layout.addRow(self._create_use_most_recent_calibration_radio_button())
        radio_button_layout.addRow(self._create_load_calibration_from_file_radio_button())
        radio_button_layout.addRow(self._create_calibrate_from_active_session_radio_button())

        self.update_calibration_toml_path()
        return radio_button_layout

    def _create_use_most_recent_calibration_radio_button(self) -> QRadioButton:
        self._use_most_recent_calibration_radio_button = QRadioButton("Use most recent calibration")
        self._use_most_recent_calibration_radio_button.toggled.connect(self._handle_use_most_recent_calibration_toggled)
        self._use_most_recent_calibration_radio_button.setToolTip(str(get_last_successful_calibration_toml_path()))
        return self._use_most_recent_calibration_radio_button

    def _create_load_calibration_from_file_radio_button(self) -> QVBoxLayout:
        vbox =QVBoxLayout()
        radio_button_push_button_layout = QHBoxLayout()
        vbox.addLayout(radio_button_push_button_layout)

        self._load_calibration_from_file_radio_button = QRadioButton("Load calibration from file")
        radio_button_push_button_layout.addWidget(self._load_calibration_from_file_radio_button)
        self._load_calibration_from_file_radio_button.toggled.connect(self._handle_load_calibration_from_file_toggled)

        self._load_calibration_toml_dialog_button = QPushButton("Load TOML")
        radio_button_push_button_layout.addWidget(self._load_calibration_toml_dialog_button)
        self._load_calibration_toml_dialog_button.clicked.connect(self.open_calibration_toml_dialog)
        self._load_calibration_toml_dialog_button.setEnabled(False)

        return vbox

    def _create_calibrate_from_active_session_radio_button(self) -> QVBoxLayout:
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        vbox.addLayout(hbox)

        self._calibrate_from_active_session_radio_button = QRadioButton("Calibrate from Active Session")
        hbox.addWidget(self._calibrate_from_active_session_radio_button)
        self._calibrate_from_active_session_radio_button.toggled.connect(self._handle_calibrate_from_active_session_toggled)

        self._calibrate_from_active_session_button = QPushButton("Run calibration...")
        hbox.addWidget(self._calibrate_from_active_session_button)
        self._calibrate_from_active_session_button.setEnabled(False)
        self._calibrate_from_active_session_button.clicked.connect(self.calibrate_from_active_session)

        self._charuco_layout = self._create_charuco_layout()
        hbox2 = QHBoxLayout()
        hbox2.addStretch()
        hbox2.addLayout(self._charuco_layout)
        vbox.addLayout(hbox2)
        self._set_charuco_form_visibility(False)

        return vbox
    
    def _create_charuco_layout(self) -> QFormLayout:
        form_layout = QFormLayout()

        self._charuco_square_size_line_edit = QLineEdit()
        self._charuco_square_size_line_edit.setValidator(QDoubleValidator())
        self._charuco_square_size_line_edit.setFixedWidth(100)
        self._charuco_square_size_line_edit.setText(str(self._gui_state.charuco_square_size))
        self._charuco_square_size_line_edit.setToolTip("The length of one of the edges of the black squares on the calibration board in mm")
        self._charuco_square_size_line_edit.textChanged.connect(self._on_charuco_square_size_line_edit_changed)

        self._charuco_square_size_label = QLabel("Charuco square size (mm)")
        self._charuco_square_size_label.setStyleSheet("QLable { font-size: 12px; }")

        form_layout.addRow(self._charuco_square_size_label, self._charuco_square_size_line_edit)
        form_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        return form_layout

    def _on_charuco_square_size_line_edit_changed(self):
        self._gui_state.charuco_square_size = float(self._charuco_square_size_line_edit.text())
        save_gui_state(gui_state=self._gui_state)

    def _set_charuco_form_visibility(self, visible: bool):
        label_index = self._charuco_layout.indexOf(self._charuco_square_size_label)
        line_edit_index = self._charuco_layout.indexOf(self._charuco_square_size_line_edit)
        self._charuco_layout.itemAt(label_index).widget().setEnabled(visible)
        self._charuco_layout.itemAt(line_edit_index).widget().setEnabled(visible)


    def _handle_use_most_recent_calibration_toggled(self, checked):
        self.update_calibration_toml_path()

    def _handle_load_calibration_from_file_toggled(self, checked):
        if checked:
            self._load_calibration_toml_dialog_button.setEnabled(True)
        else:
            self._load_calibration_toml_dialog_button.setEnabled(False)
        self.update_calibration_toml_path()

    def _handle_calibrate_from_active_session_toggled(self, checked):
        active_session_info: SessionInfoModel = self._get_active_session_info()
        self._update_calibrate_from_active_recording_button_text()
        self.update_calibration_toml_path()

        if checked and active_session_info is not None and active_session_info.videos_synchronized_status_check:
            self._calibrate_from_active_session_button.setEnabled(True)
            self._set_charuco_form_visibility(True)
        else:
            self._calibrate_from_active_session_button.setEnabled(False)
            self._set_charuco_form_visibility(False)

    def _show_calibration_toml_path(self, calibration_toml_pathstring: str):
        self._calibration_toml_path = calibration_toml_pathstring
        path = str(calibration_toml_pathstring).replace(os.sep, "/ ")
        self._selected_calibration_toml_label.setText(path)
        self._selected_calibration_toml_label.show()

    def _check_active_session_for_calibration_toml(self):
        active_session: SessionInfoModel = self._get_active_session_info()
        if active_session is not None:
            if active_session.calibration_toml_check:
                active_session.calibration_toml_path


    def _update_calibrate_from_active_recording_button_text(self):
        active_session_info: SessionInfoModel = self._get_active_session_info()
        if active_session_info is None:
            active_path_str = "- No Active Session Selected -"
        else:
            if not active_session_info.videos_synchronized_status_check:
                active_path_str = f"Session {active_session_info.name} has no synchronized videos"
            else:
                active_path_str = f"Calibrate from session: {active_session_info.name}"
        self._calibrate_from_active_session_button.setToolTip(active_path_str)
        self.update_calibration_toml_path()

    def update_calibration_toml_path(self, toml_path: str = None):
        if toml_path is None:
            if self._load_calibration_from_file_radio_button.isChecked():
                if self._user_selected_toml_path is not None:
                    toml_path = self._user_selected_toml_path
                else:
                    toml_path = self._check_active_session_for_calibration_toml()
            elif self._use_most_recent_calibration_radio_button.isChecked():
                toml_path = get_last_successful_calibration_toml_path()
            elif self._calibrate_from_active_session_radio_button.isChecked():
                toml_path = self._check_active_session_for_calibration_toml()
            else: # no radio button selected, initialize
                toml_path = self._check_active_session_for_calibration_toml()
                if toml_path is not None:
                    self._load_calibration_from_file_radio_button.setChecked(True)
                else:
                    toml_path = get_last_successful_calibration_toml_path()
                    self._use_most_recent_calibration_radio_button.setChecked(True)
        
        self._calibration_toml_path = toml_path

        if self._calibration_toml_path is not None:
            logger.info(f"Setting calibration TOML path: {self._calibration_toml_path}")
            self._show_calibration_toml_path(self._calibration_toml_path)
        else:
            self._show_calibration_toml_path("- Calibration File Not Found -")

    def open_calibration_toml_dialog(self) -> str:
        dialog = QFileDialog
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

        calibration_toml_path = dialog.getOpenFileName(
            self,
            "Select 'toml' containing camera calibration info",
            str(self._get_active_session_info().path),
            "Camera Calibration TOML (*.toml)"
        )
        if len(calibration_toml_path) > 0:
            self._user_selected_toml_path = calibration_toml_path[0]
            logger.info(f"User selected camera calibration toml path: {self._user_selected_toml_path}")
            self._show_calibration_toml_path(self._user_selected_toml_path)
            self.update_calibration_toml_path(toml_path=self._user_selected_toml_path)
            return self._user_selected_toml_path

    def calibrate_from_active_session(self, charuco_square_size_mm: float = None):
        if not charuco_square_size_mm:
            charuco_square_size_mm = float(self._charuco_square_size_line_edit.text())

        active_session_info: SessionInfoModel = self._get_active_session_info()
        if active_session_info is None:
            logger.error("Cannot calibrate from active session - no active session selected")
            return       

        if not active_session_info.videos_synchronized_status_check:
            logger.error(f"Cannot calibrate from {active_session_info.name} - synchronized videos status check is {active_session_info.check_videos_synchronized_status}")
            return
        
        logger.info(f"Calibrating from active session: {active_session_info.name}")

        self._anipose_calibration_thread_worker = AniposeCalibrationThreadWorker(
            calibration_videos_folder_path=active_session_info.synchronized_videos_folder_path,
            charuco_square_size=float(charuco_square_size_mm),
            kill_thread_event=self._kill_thread_event,
        )
        self._anipose_calibration_thread_worker.start()
        self._anipose_calibration_thread_worker.finished.connect(self.update_calibration_toml_path)

        
