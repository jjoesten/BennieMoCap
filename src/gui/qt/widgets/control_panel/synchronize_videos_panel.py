import logging
logger = logging.getLogger(__name__)

import threading
from typing import Callable

from PyQt6.QtWidgets import (
    QWidget,
    QStackedLayout,
    QStackedWidget,
    QRadioButton,
    QButtonGroup,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton
)

from src.gui.qt.widgets.spinner_widget import QtWaitSpinner
from src.data_layer.session_models.session_info_model import SessionInfoModel
from src.utilities.video_sync.manual_sync import synchronize_videos_manually
from src.gui.qt.widgets.synchronization_widget import SynchronizationWidget
# from src.gui.qt.widgets.data_visualization.single_video_display import SingleVideoDisplay

class SynchronizeVideosPanel(QWidget):

    def __init__(self, kill_thread_event: threading.Event, log_update: Callable, synchronization_widget: SynchronizationWidget, session_info_model: SessionInfoModel, parent=None):
        super().__init__(parent)
        self._kill_thread_event = kill_thread_event
        self._log_update = log_update
        self._synchronization_widget = synchronization_widget
        self._session_info_model = session_info_model

        layout = QVBoxLayout()
        self.setLayout(layout)

        self._wait_spinner = QtWaitSpinner(self, center_on_parent=False)
        layout.addWidget(self._wait_spinner)

        # MAIN LAYOUT
        self._stacked_widget = QStackedWidget()

        # RADIO BUTTON GROUP        
        group_box = QGroupBox("Synchronization Type")
        radio_button_layout = QHBoxLayout()
        group_box.setLayout(radio_button_layout)


        audio_radio_button = QRadioButton("Audio")
        video_radio_button = QRadioButton("Video")
        manual_radio_button = QRadioButton("Manual")

        radio_button_layout.addWidget(audio_radio_button)
        radio_button_layout.addWidget(video_radio_button)
        radio_button_layout.addWidget(manual_radio_button)
        
        self._sync_button_group = QButtonGroup(group_box)
        self._sync_button_group.addButton(audio_radio_button, 0)
        self._sync_button_group.addButton(video_radio_button, 1)
        self._sync_button_group.addButton(manual_radio_button, 2)
        
        self._sync_button_group.buttonToggled.connect(self._sync_button_changed)
        

        # PAGES
        audio_page_widget = QWidget()
        audio_page_widget.setStyleSheet("background-color: red;")

        video_page_widget = QWidget()
        video_page_widget.setStyleSheet("background-color: green;")

        # Manual Page
        manual_page_widget = QWidget()
        manual_page_layout = QVBoxLayout()
        manual_page_widget.setLayout(manual_page_layout)
        self._manual_synch_button = QPushButton("Synchronize")
        self._manual_synch_button.clicked.connect(self._manual_synchronization)
        manual_page_layout.addWidget(self._manual_synch_button)


        self._stacked_widget.addWidget(audio_page_widget)
        self._stacked_widget.addWidget(video_page_widget)
        self._stacked_widget.addWidget(manual_page_widget)


        layout.addWidget(group_box)
        layout.addWidget(self._stacked_widget)

        manual_radio_button.setChecked(True)
        self._stacked_widget.setCurrentIndex(2)


    def _sync_button_changed(self):
        selected_button = self._sync_button_group.checkedId()
        self._stacked_widget.setCurrentIndex(selected_button)

    def _manual_synchronization(self):
        self._wait_spinner.start()
        self._wait_spinner.show()
        # self._manual_synch_button.setEnabled(False)

        logger.debug("Starting video synchronization")

        keypoint_dict = {}
        for video_player in self._synchronization_widget.video_players:
            keypoint_dict[video_player.video_name] = video_player.current_frame

        try:
            output_folder_path = synchronize_videos_manually(
                raw_video_folder_path=self._session_info_model.framerate_matched_videos_folder_path,
                synchronized_video_folder_path=self._session_info_model.synchronized_videos_folder_path,
                keypoint_dict=keypoint_dict
            )
        except Exception as e:
            logger.exception("Something went wrong while manually synchronizing videos")
            logger.exception(e)

        
        


        

        
        
        



        

        