from pathlib import Path
from typing import Union


from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout
)

from src.gui.qt.widgets.data_visualization.multi_video_display import MultiVideoDisplay
from src.gui.qt.widgets.data_visualization.slider_widget import VideoSlider

class DataVisualizationWidget(QWidget):
    def __init__(self, mediapipe_skeleton_npy_path: Union[str, Path] = None, video_folder_path: Union[str, Path] = None):
        super().__init__()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

        # TODO: Skeleton Viewer Widget
        
        # Multi Video Display
        self._video_display = MultiVideoDisplay()
        layout.addWidget(self._video_display)

        self._frame_count_slider = VideoSlider()
        # TODO: handle this when the skeleton data loads?
        self._frame_count_slider.setEnabled(True)
        layout.addWidget(self._frame_count_slider)

        self._connect_signals_to_slots()

        self._is_video_display_enabled = True

        if mediapipe_skeleton_npy_path is not None:
            self.load_skeleton_data(mediapipe_skeleton_npy_path)
        
        if video_folder_path is not None:
            self.generate_video_display(video_folder_path)

    def load_skeleton_data(self, mediapipe_skeleton_npy_path: Union[str, Path]):
        # TODO: implement load_skeleton_data
        pass

    def generate_video_display(self, videos_folder_path: Union[str, Path]):
        self._video_display.generate_video_display(videos_folder_path)
        self._video_display.update_display(self._frame_count_slider.slider.value())

    def _connect_signals_to_slots(self):
        # TODO: skeleton viewer signals
        self._video_display.videos_loaded_signal.connect(self._handle_data_loaded_signal)
        self._frame_count_slider.slider.valueChanged.connect(self._handle_slider_value_changed)
    
    def _handle_slider_value_changed(self):
        # skeleton viewer
        if self._is_video_display_enabled:
            self._video_display.update_display(self._frame_count_slider.slider.value())

    def _handle_data_loaded_signal(self):
        self._frame_count_slider.set_slider_range(self._video_display.frame_count)
        self._frame_count_slider.setEnabled(True)

    
